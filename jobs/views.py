from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db import models
from django.contrib.auth import get_user_model

from .models import Job, Application, SavedJob, JobAlert, StatusHistory
from .serializers import (
    JobSerializer,
    ApplicationSerializer,
    SavedJobSerializer,
    JobAlertSerializer,
    StatusHistorySerializer,
)
from .filters import JobFilter
from .tasks import send_application_confirmation, send_status_update_email
from .resume_parser import parse_resume
from config.cache import cache_response, invalidate_job_cache
from config.permissions import IsEmployerOrReadOnly, IsEmployer, IsCandidate, IsAdmin
from config.pagination import StandardPagination
from config.throttling import ApplyThrottle

from accounts.serializers import UserSerializer
from config.websocket import send_status_update_notification

User = get_user_model()


class JobListCreateView(generics.ListCreateAPIView):
    """List all active jobs or create a new job (employer only)"""

    queryset = Job.objects.filter(is_active=True, is_deleted=False)
    serializer_class = JobSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsEmployerOrReadOnly)
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = JobFilter
    search_fields = ["title", "description", "location", "skills_required"]
    ordering_fields = ["salary_min", "salary_max", "created_at", "views_count"]
    ordering = ["-created_at"]

    @cache_response("job_list", ttl=900)
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(employer=self.request.user)
        invalidate_job_cache()


class JobDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete a specific job"""

    queryset = Job.objects.filter(is_active=True, is_deleted=False)
    serializer_class = JobSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsEmployerOrReadOnly)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.views_count += 1
        instance.save(update_fields=["views_count"])

        from django.core.cache import cache

        cache_key = f"job_detail_{instance.id}"
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data)

        serializer_data = self.get_serializer(instance).data
        cache.set(cache_key, serializer_data, timeout=300)
        return Response(serializer_data)

    def perform_update(self, serializer):
        if self.get_object().employer != self.request.user:
            raise PermissionDenied("You can only edit your own jobs")
        serializer.save()
        invalidate_job_cache()

    def perform_destroy(self, instance):
        # Allow admin/staff to delete any job; owners can delete their own
        user = self.request.user
        is_admin = (
            user.is_superuser or user.is_staff or getattr(user, "role", "") == "admin"
        )
        if not is_admin and instance.employer != user:
            raise PermissionDenied("You can only delete your own jobs")
        instance.soft_delete()
        invalidate_job_cache()


class ApplyToJobView(APIView):
    """Apply to a job with resume upload (candidate only)"""

    permission_classes = [permissions.IsAuthenticated, IsCandidate]
    parser_classes = [MultiPartParser, FormParser]
    throttle_classes = [ApplyThrottle]

    def post(self, request, job_id):
        job = get_object_or_404(Job, id=job_id, is_active=True)

        if Application.objects.filter(job=job, candidate=request.user).exists():
            return Response(
                {"error": "You have already applied to this job"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ApplicationSerializer(data=request.data)
        if serializer.is_valid():
            application = serializer.save(job=job, candidate=request.user)

            if application.resume:
                try:
                    application.resume.open()
                    resume_data = parse_resume(application.resume)
                    application.resume.close()

                    application.parsed_email = resume_data.get("email")
                    application.parsed_phone = resume_data.get("phone")
                    application.extracted_skills = resume_data.get("skills", [])
                    application.save()
                except Exception as e:
                    print(f"Resume parsing error: {e}")

            # Call the task (already patched in tests via conftest autouse fixture)
            send_application_confirmation(application.id)

            invalidate_job_cache()

            return Response(
                {
                    "success": True,
                    "application_id": application.id,
                    "id": application.id,
                    "job_title": job.title,
                    "parsed_email": application.parsed_email,
                    "parsed_skills": application.extracted_skills,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MyApplicationsView(generics.ListAPIView):
    """Get all applications for the logged-in candidate"""

    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated, IsCandidate]
    pagination_class = StandardPagination

    def get_queryset(self):
        return Application.objects.filter(candidate=self.request.user)


class EmployerApplicationsView(generics.ListAPIView):
    """Get all applications for jobs posted by the employer"""

    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated, IsEmployer]
    pagination_class = StandardPagination

    def get_queryset(self):
        return Application.objects.filter(job__employer=self.request.user)


class UpdateApplicationStatusView(generics.UpdateAPIView):
    """Update application status (employer only)"""

    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated, IsEmployer]
    lookup_field = "id"
    lookup_url_kwarg = "pk"

    def perform_update(self, serializer):
        application = self.get_object()
        old_status = application.status

        if application.job.employer != self.request.user:
            raise PermissionDenied("You can only update applications for your jobs")

        updated_application = serializer.save()

        if old_status != updated_application.status:
            StatusHistory.objects.create(
                application=application,
                status=updated_application.status,
                changed_by=self.request.user,
                notes=self.request.data.get("notes", ""),
            )

            # Call the task (patched in tests via conftest autouse fixture)
            send_status_update_email(
                application.id, old_status, updated_application.status
            )

            send_status_update_notification(
                user_id=application.candidate.id,
                application_id=application.id,
                job_title=application.job.title,
                old_status=old_status,
                new_status=updated_application.status,
            )


class SavedJobView(generics.ListCreateAPIView):
    """Save a job or list saved jobs"""

    serializer_class = SavedJobSerializer
    permission_classes = [permissions.IsAuthenticated, IsCandidate]
    pagination_class = StandardPagination

    def get_queryset(self):
        return SavedJob.objects.filter(candidate=self.request.user)

    def perform_create(self, serializer):
        job_id = self.request.data.get("job_id")
        job = get_object_or_404(Job, id=job_id)
        serializer.save(candidate=self.request.user, job=job)


class UnsaveJobView(generics.DestroyAPIView):
    """Remove a saved job"""

    permission_classes = [permissions.IsAuthenticated, IsCandidate]

    def get_queryset(self):
        return SavedJob.objects.filter(candidate=self.request.user)


class JobAlertListCreateView(generics.ListCreateAPIView):
    """Create or list job alerts"""

    serializer_class = JobAlertSerializer
    permission_classes = [permissions.IsAuthenticated, IsCandidate]
    pagination_class = StandardPagination

    def get_queryset(self):
        return JobAlert.objects.filter(candidate=self.request.user)

    def perform_create(self, serializer):
        serializer.save(candidate=self.request.user)


class JobAlertDeleteView(generics.DestroyAPIView):
    """Delete a job alert"""

    permission_classes = [permissions.IsAuthenticated, IsCandidate]

    def get_queryset(self):
        return JobAlert.objects.filter(candidate=self.request.user)


class CompanyJobsView(generics.ListAPIView):
    """List all jobs for a specific company"""

    serializer_class = JobSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = StandardPagination

    def get_queryset(self):
        employer_id = self.kwargs["employer_id"]
        return Job.objects.filter(employer_id=employer_id, is_active=True)


class ApplicantProfileView(generics.RetrieveAPIView):
    """View applicant profile (employer only, only if they applied to your job)"""

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsEmployer]

    def get_queryset(self):
        return User.objects.all()

    def get_object(self):
        applicant_id = self.kwargs["user_id"]

        if Application.objects.filter(
            candidate_id=applicant_id, job__employer=self.request.user
        ).exists():
            return User.objects.get(id=applicant_id)

        raise PermissionDenied("Not authorized to view this profile")


class JobShareView(APIView):
    """Get social media share links for a job"""

    permission_classes = [permissions.AllowAny]

    def get(self, request, job_id):
        job = get_object_or_404(Job, id=job_id)

        frontend_url = request.GET.get("frontend_url", "http://localhost:5173")
        job_url = f"{frontend_url}/jobs/{job_id}"

        share_data = {
            "title": job.title,
            "company": job.employer.company or job.employer.username,
            "url": job_url,
            "twitter_url": f"https://twitter.com/intent/tweet?text={job.title} at {job.employer.company}&url={job_url}",
            "linkedin_url": f"https://www.linkedin.com/sharing/share-offsite/?url={job_url}",
            "facebook_url": f"https://www.facebook.com/sharer/sharer.php?u={job_url}",
            "email_subject": f"Job Opportunity: {job.title} at {job.employer.company}",
            "email_body": f"I found this great job opportunity:\n\n{job.title} at {job.employer.company}\n\n{job_url}",
        }

        return Response(share_data, status=200)


class UpdateResumeView(APIView):
    """Update resume for latest application"""

    permission_classes = [permissions.IsAuthenticated, IsCandidate]
    parser_classes = [MultiPartParser, FormParser]

    def put(self, request):
        try:
            application = Application.objects.filter(candidate=request.user).last()
            if application and "resume" in request.FILES:
                application.resume = request.FILES["resume"]
                application.save()
                return Response({"message": "Resume updated successfully"}, status=200)
            return Response({"error": "No application found"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=400)


class EmailPreferencesView(APIView):
    """Get or update email notification preferences"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response(
            {
                "receive_email_notifications": getattr(
                    user, "receive_email_notifications", True
                ),
                "receive_marketing_emails": getattr(
                    user, "receive_marketing_emails", False
                ),
                "receive_alert_emails": getattr(user, "receive_alert_emails", True),
            }
        )

    def post(self, request):
        user = request.user
        user.receive_email_notifications = request.data.get(
            "receive_email_notifications", True
        )
        user.receive_marketing_emails = request.data.get(
            "receive_marketing_emails", False
        )
        user.receive_alert_emails = request.data.get("receive_alert_emails", True)
        user.save()
        return Response({"message": "Preferences updated successfully"}, status=200)


class AdminStatsView(APIView):
    """Get dashboard statistics (admin only)"""

    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        stats = {
            "total_users": User.objects.count(),
            "total_employers": User.objects.filter(role="employer").count(),
            "total_candidates": User.objects.filter(role="candidate").count(),
            "total_jobs": Job.objects.count(),
            "active_jobs": Job.objects.filter(is_active=True).count(),
            "total_applications": Application.objects.count(),
            "pending_applications": Application.objects.filter(
                status="pending"
            ).count(),
            "total_views": Job.objects.aggregate(total=models.Sum("views_count"))[
                "total"
            ]
            or 0,
        }
        return Response(stats, status=200)


class AdminRecentJobsView(APIView):
    """Get recent jobs (admin only)"""

    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        jobs = Job.objects.all().order_by("-created_at")[:10]
        serializer = JobSerializer(jobs, many=True)
        return Response(serializer.data, status=200)


class AdminRecentUsersView(APIView):
    """Get recent users (admin only)"""

    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        users = User.objects.all().order_by("-date_joined")[:10]
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=200)


class AdminFlagJobView(APIView):
    """Flag a job as inappropriate (admin only)"""

    permission_classes = [permissions.IsAdminUser]

    def post(self, request, job_id):
        job = get_object_or_404(Job, id=job_id)
        job.is_active = False
        job.save()
        invalidate_job_cache()
        return Response(
            {"message": f"Job '{job.title}' has been flagged and hidden"}, status=200
        )


class AdminDeleteJobView(APIView):
    """Delete any job (admin only)"""

    permission_classes = [permissions.IsAdminUser]

    def delete(self, request, job_id):
        job = get_object_or_404(Job, id=job_id)
        job.delete()
        invalidate_job_cache()
        return Response({"message": f"Job '{job.title}' has been deleted"}, status=200)


class WithdrawApplicationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, application_id):
        try:
            application = Application.objects.get(
                id=application_id, candidate=request.user
            )

            if application.status not in ["pending", "reviewed"]:
                return Response(
                    {
                        "error": "Cannot withdraw application after it's been interviewed or hired"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            application.delete()
            return Response(
                {"message": "Application withdrawn successfully"},
                status=status.HTTP_204_NO_CONTENT,
            )
        except Application.DoesNotExist:
            return Response({"error": "Application not found"}, status=404)


class EmployerAnalyticsView(APIView):
    """Get analytics for employer dashboard"""

    permission_classes = [permissions.IsAuthenticated, IsEmployer]

    def get(self, request):
        jobs = Job.objects.filter(employer=request.user)
        applications = Application.objects.filter(job__employer=request.user)

        total_jobs = jobs.count()
        active_jobs = jobs.filter(is_active=True).count()
        total_applications = applications.count()
        total_views = jobs.aggregate(total=models.Sum("views_count"))["total"] or 0

        application_rate = (
            round((total_applications / total_views * 100), 1) if total_views > 0 else 0
        )

        applications_by_status = applications.values("status").annotate(
            count=models.Count("id")
        )

        top_jobs = jobs.order_by("-applications_count")[:5].values(
            "id", "title", "applications_count", "views_count"
        )

        return Response(
            {
                "summary": {
                    "total_jobs": total_jobs,
                    "active_jobs": active_jobs,
                    "total_applications": total_applications,
                    "total_views": total_views,
                    "application_rate": application_rate,
                },
                "applications_by_status": applications_by_status,
                "top_jobs": top_jobs,
            },
            status=200,
        )


class CandidateAnalyticsView(APIView):
    """Get analytics for candidate dashboard"""

    permission_classes = [permissions.IsAuthenticated, IsCandidate]

    def get(self, request):
        applications = Application.objects.filter(candidate=request.user)

        data = {
            "total_applications": applications.count(),
            "applications_by_status": applications.values("status").annotate(
                count=models.Count("id")
            ),
            "saved_jobs": SavedJob.objects.filter(candidate=request.user).count(),
            "active_alerts": JobAlert.objects.filter(
                candidate=request.user, is_active=True
            ).count(),
        }

        return Response(data, status=200)


class RestoreJobView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, job_id):
        try:
            job = Job.objects.get(id=job_id, is_deleted=True)
            job.restore()
            return Response({"message": f"Job {job.title} restored"}, status=200)
        except Job.DoesNotExist:
            return Response({"error": "Job not found"}, status=404)


class ApplicationAuditLogView(generics.ListAPIView):
    serializer_class = StatusHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        application_id = self.kwargs["application_id"]
        try:
            application = Application.objects.get(id=application_id)
            if application.job.employer != self.request.user:
                return StatusHistory.objects.none()
            return StatusHistory.objects.filter(application=application).order_by(
                "-changed_at"
            )
        except Application.DoesNotExist:
            return StatusHistory.objects.none()


class EmployerJobStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not request.user.is_employer:
            return Response({"error": "Only employers can access this"}, status=403)

        jobs = Job.objects.filter(employer=request.user, is_deleted=False)
        applications = Application.objects.filter(job__employer=request.user)

        stats = {
            "total_jobs": jobs.count(),
            "active_jobs": jobs.filter(is_active=True).count(),
            "total_applications": applications.count(),
            "applications_by_status": {
                "pending": applications.filter(status="pending").count(),
                "reviewed": applications.filter(status="reviewed").count(),
                "interview": applications.filter(status="interview").count(),
                "rejected": applications.filter(status="rejected").count(),
                "hired": applications.filter(status="hired").count(),
            },
            "jobs": JobSerializer(jobs, many=True).data,
        }
        return Response(stats)