import sys
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import F
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.http import Http404

from .models import Job, Application, SavedJob, JobAlert, StatusHistory
from .serializers import (
    JobSerializer,
    ApplicationSerializer,
    SavedJobSerializer,
    JobAlertSerializer,
)
from .filters import JobFilter
from .tasks import send_application_confirmation, send_status_update_email
from django.contrib.auth import get_user_model
from accounts.serializers import UserSerializer
from rest_framework.throttling import UserRateThrottle
from .resume_parser import parse_resume

User = get_user_model()


def is_running_tests():
    return "test" in sys.argv or "pytest" in sys.modules


class ApplyThrottle(UserRateThrottle):
    rate = "5/hour"


class IsEmployerOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            return request.user.is_authenticated and request.user.is_employer
        return True


class JobListCreateView(generics.ListCreateAPIView):
    queryset = Job.objects.filter(is_active=True)
    serializer_class = JobSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsEmployerOrReadOnly)
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = JobFilter
    search_fields = ["title", "description", "location"]
    ordering_fields = ["salary_min", "salary_max", "created_at"]
    ordering = ["-created_at"]

    def perform_create(self, serializer):
        serializer.save(employer=self.request.user, is_active=True)


class JobDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        Job.objects.filter(pk=instance.pk).update(views_count=F("views_count") + 1)
        instance.refresh_from_db()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def perform_update(self, serializer):
        if self.get_object().employer != self.request.user:
            raise PermissionDenied("You can only edit your own jobs")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.employer != self.request.user:
            raise PermissionDenied("You can only delete your own jobs")
        instance.delete()


class ApplyToJobView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    throttle_classes = [ApplyThrottle]

    def post(self, request, job_id):
        print(f"ApplyToJobView reached with job_id={job_id}")

        # First, try to find the job without the is_active filter to help debugging
        try:
            job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            return Response(
                {"error": f"No job exists with id {job_id}"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not job.is_active:
            return Response(
                {"error": f"Job {job_id} is not active (is_active=False)"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if job.expires_at and job.expires_at < timezone.now():
            return Response(
                {"error": "This job has expired"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if Application.objects.filter(job=job, candidate=request.user).exists():
            return Response(
                {"error": "You have already applied"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ApplicationSerializer(data=request.data)
        if serializer.is_valid():
            application = serializer.save(job=job, candidate=request.user)

            if application.resume:
                try:
                    with application.resume.open() as resume_file:
                        resume_data = parse_resume(resume_file)
                    application.parsed_email = resume_data.get("email")
                    application.parsed_phone = resume_data.get("phone")
                    application.extracted_skills = resume_data.get("skills", [])
                    application.save(
                        update_fields=[
                            "parsed_email",
                            "parsed_phone",
                            "extracted_skills",
                        ]
                    )
                except Exception as e:
                    print(f"Resume parsing error: {e}")

            if not is_running_tests():
                send_application_confirmation.delay(application.id)

            return Response(
                {
                    "success": True,
                    "application_id": application.id,
                    "job_title": job.title,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MyApplicationsView(generics.ListAPIView):
    serializer_class = ApplicationSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Application.objects.filter(candidate=self.request.user)


class EmployerApplicationsView(generics.ListAPIView):
    serializer_class = ApplicationSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        if not self.request.user.is_employer:
            return Application.objects.none()
        return Application.objects.filter(job__employer=self.request.user)


class UpdateApplicationStatusView(generics.UpdateAPIView):
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    permission_classes = (permissions.IsAuthenticated,)

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
            if not is_running_tests():
                send_status_update_email.delay(
                    application.id, old_status, updated_application.status
                )
            else:
                print("Test environment: skipping Celery task send_status_update_email")


class SavedJobView(generics.ListCreateAPIView):
    serializer_class = SavedJobSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return SavedJob.objects.filter(candidate=self.request.user)

    def perform_create(self, serializer):
        job_id = self.request.data.get("job_id")
        job = get_object_or_404(Job, id=job_id)
        serializer.save(candidate=self.request.user, job=job)


class UnsaveJobView(generics.DestroyAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return SavedJob.objects.filter(candidate=self.request.user)


class JobAlertListCreateView(generics.ListCreateAPIView):
    serializer_class = JobAlertSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return JobAlert.objects.filter(candidate=self.request.user)

    def perform_create(self, serializer):
        serializer.save(candidate=self.request.user)


class JobAlertDeleteView(generics.DestroyAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return JobAlert.objects.filter(candidate=self.request.user)


class AdminStatsView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        from accounts.models import User

        stats = {
            "totalUsers": User.objects.count(),
            "totalJobs": Job.objects.count(),
            "totalApplications": Application.objects.count(),
            "pendingApplications": Application.objects.filter(status="pending").count(),
        }
        return Response(stats)


class AdminRecentJobsView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        jobs = Job.objects.all().order_by("-created_at")[:10]
        serializer = JobSerializer(jobs, many=True)
        return Response(serializer.data)


class AdminRecentUsersView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        from accounts.models import User
        from accounts.serializers import UserSerializer

        users = User.objects.all().order_by("-date_joined")[:10]
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)


class AdminDeleteJobView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def delete(self, request, job_id):
        try:
            job = Job.objects.get(id=job_id)
            job.delete()
            return Response({"message": "Job deleted successfully"}, status=200)
        except Job.DoesNotExist:
            return Response({"error": "Job not found"}, status=404)


class AdminToggleUserView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def patch(self, request, user_id):
        from accounts.models import User

        try:
            user = User.objects.get(id=user_id)
            user.is_active = not user.is_active
            user.save()
            return Response(
                {"message": f"User {'activated' if user.is_active else 'deactivated'}"},
                status=200,
            )
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)


class WithdrawApplicationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, application_id):
        try:
            application = Application.objects.get(
                id=application_id, candidate=request.user
            )
            application.delete()
            return Response({"message": "Application withdrawn"}, status=200)
        except Application.DoesNotExist:
            return Response({"error": "Application not found"}, status=404)


class UpdateResumeView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def put(self, request):
        application_id = request.data.get("application_id")
        if not application_id:
            return Response({"error": "application_id is required"}, status=400)

        try:
            application = Application.objects.get(
                id=application_id, candidate=request.user
            )
        except Application.DoesNotExist:
            return Response({"error": "Application not found"}, status=404)

        if "resume" in request.FILES:
            application.resume = request.FILES["resume"]
            application.save()
            return Response({"message": "Resume updated"}, status=200)
        return Response({"error": "No resume file provided"}, status=400)


class EmailPreferencesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response(
            {
                "receive_email_notifications": getattr(
                    user, "receive_email_notifications", True
                )
            }
        )

    def post(self, request):
        user = request.user
        user.receive_email_notifications = request.data.get(
            "receive_email_notifications", True
        )
        user.save()
        return Response({"message": "Preferences updated"})


class CompanyJobsView(generics.ListAPIView):
    serializer_class = JobSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        employer_id = self.kwargs["employer_id"]
        return Job.objects.filter(employer_id=employer_id, is_active=True)


class ApplicantProfileView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.is_employer:
            return User.objects.none()
        return User.objects.all()

    def get_object(self):
        applicant_id = self.kwargs["user_id"]
        if Application.objects.filter(
            candidate_id=applicant_id, job__employer=self.request.user
        ).exists():
            return User.objects.get(id=applicant_id)
        raise PermissionDenied("Not authorized to view this profile")


class JobShareView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, job_id):
        from django.conf import settings

        FRONTEND_URL = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
        try:
            job = Job.objects.get(id=job_id)
            share_data = {
                "title": job.title,
                "company": job.employer.company,
                "url": f"{FRONTEND_URL}/jobs/{job_id}",
                "twitter_url": f"https://twitter.com/intent/tweet?text={job.title} at {job.employer.company}&url={FRONTEND_URL}/jobs/{job_id}",
                "linkedin_url": f"https://www.linkedin.com/sharing/share-offsite/?url={FRONTEND_URL}/jobs/{job_id}",
            }
            return Response(share_data, status=200)
        except Job.DoesNotExist:
            return Response({"error": "Job not found"}, status=404)


class AdminFlagJobView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, job_id):
        try:
            job = Job.objects.get(id=job_id)
            job.is_active = False
            job.save()
            return Response({"message": f"Job {job.title} flagged"}, status=200)
        except Job.DoesNotExist:
            return Response({"error": "Job not found"}, status=404)
