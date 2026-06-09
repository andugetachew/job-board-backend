from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.db.models import Count, Sum, Avg
from django.utils import timezone
from datetime import timedelta
from .models import Job, Application, SavedJob, JobAlert


class EmployerAnalyticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        if not user.is_employer:
            return Response(
                {"error": "Only employers can access analytics"}, status=403
            )

        jobs = Job.objects.filter(employer=user)
        applications = Application.objects.filter(job__employer=user)

        # Basic stats
        total_jobs = jobs.count()
        active_jobs = jobs.filter(is_active=True).count()
        total_applications = applications.count()
        total_views = jobs.aggregate(total=Sum("views_count"))["total"] or 0

        # Application rate
        application_rate = (
            round((total_applications / total_views * 100), 1) if total_views > 0 else 0
        )

        # Applications by status
        applications_by_status = applications.values("status").annotate(
            count=Count("id")
        )

        # Monthly trends (last 6 months)
        monthly_data = []
        for i in range(6):
            month_start = timezone.now() - timedelta(days=30 * (5 - i))
            month_end = month_start + timedelta(days=30)

            month_jobs = jobs.filter(
                created_at__gte=month_start, created_at__lt=month_end
            ).count()
            month_apps = applications.filter(
                applied_at__gte=month_start, applied_at__lt=month_end
            ).count()

            monthly_data.append(
                {
                    "month": month_start.strftime("%B %Y"),
                    "jobs": month_jobs,
                    "applications": month_apps,
                }
            )

        # Top performing jobs
        top_jobs = jobs.order_by("-applications_count")[:5].values(
            "id", "title", "applications_count", "views_count"
        )

        # Response data
        data = {
            "summary": {
                "total_jobs": total_jobs,
                "active_jobs": active_jobs,
                "total_applications": total_applications,
                "total_views": total_views,
                "application_rate": application_rate,
            },
            "applications_by_status": applications_by_status,
            "monthly_trends": monthly_data,
            "top_jobs": top_jobs,
            "recent_applications": applications.select_related("candidate", "job")
            .order_by("-applied_at")[:10]
            .values("id", "candidate__username", "job__title", "status", "applied_at"),
        }

        return Response(data)


class CandidateAnalyticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        if not user.is_candidate:
            return Response(
                {"error": "Only candidates can access analytics"}, status=403
            )

        applications = Application.objects.filter(candidate=user)

        data = {
            "total_applications": applications.count(),
            "applications_by_status": applications.values("status").annotate(
                count=Count("id")
            ),
            "saved_jobs": SavedJob.objects.filter(candidate=user).count(),
            "active_alerts": JobAlert.objects.filter(
                candidate=user, is_active=True
            ).count(),
            "recent_applications": applications.select_related("job")
            .order_by("-applied_at")[:10]
            .values("id", "job__title", "status", "applied_at"),
        }

        return Response(data)
