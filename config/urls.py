from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView
from jobs.views import (
    AdminStatsView,
    AdminRecentJobsView,
    AdminRecentUsersView,
    AdminDeleteJobView,
    MyApplicationsView,
)
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
from backup.views import BackupDatabaseView, BackupMediaView
from jobs.analytics import EmployerAnalyticsView, CandidateAnalyticsView
from django.http import JsonResponse
from django.views.generic import RedirectView

def health_check(request):
    return JsonResponse({"status": "ok"})
urlpatterns = [

    path("", RedirectView.as_view(url="/api/docs/"), name="root"), 
    path("health/", health_check, name="health"), 
    
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/jobs/", include("jobs.urls")),
    path("api/my-apps/", MyApplicationsView.as_view(), name="direct-apps"),
    path("api/admin/stats/", AdminStatsView.as_view(), name="admin-stats"),
    path(
        "api/admin/recent-jobs/",
        AdminRecentJobsView.as_view(),
        name="admin-recent-jobs",
    ),
    path(
        "api/admin/recent-users/",
        AdminRecentUsersView.as_view(),
        name="admin-recent-users",
    ),
    path(
        "api/admin/jobs/<int:job_id>/",
        AdminDeleteJobView.as_view(),
        name="admin-delete-job",
    ),
    path("auth/", include("social_django.urls", namespace="social")),
    path("", include("reviews.urls")),
    path(
        "api/admin/backup/database/",
        BackupDatabaseView.as_view(),
        name="backup-database",
    ),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("api/admin/backup/media/", BackupMediaView.as_view(), name="backup-media"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("api/analytics/employer/", EmployerAnalyticsView.as_view(), name="employer-analytics"),
    path("api/analytics/candidate/", CandidateAnalyticsView.as_view(), name="candidate-analytics"),
]

handler404 = "config.views.handler404"
handler500 = "config.views.handler500"
handler403 = "config.views.handler403"
handler400 = "config.views.handler400"

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
