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
    AdminToggleUserView,
    MyApplicationsView,
)

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    # API Routes
    path("api/auth/", include("accounts.urls")),
    path("api/jobs/", include("jobs.urls")),
    # Direct test endpoint
    path("api/my-apps/", MyApplicationsView.as_view(), name="direct-apps"),
    # Admin API endpoints (keep consistent with /api/ prefix)
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
    path(
        "api/admin/users/<int:user_id>/",
        AdminToggleUserView.as_view(),
        name="admin-toggle-user",
    ),
    path("auth/", include("social_django.urls", namespace="social")),
    path("api/", include("reviews.urls")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
