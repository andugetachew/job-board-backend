from django.urls import path
from .analytics import EmployerAnalyticsView, CandidateAnalyticsView
from .views import (
    JobListCreateView,
    JobDetailView,
    ApplyToJobView,
    MyApplicationsView,
    EmployerApplicationsView,
    UpdateApplicationStatusView,
    SavedJobView,
    UnsaveJobView,
    JobAlertListCreateView,
    JobAlertDeleteView,
    AdminFlagJobView,
    WithdrawApplicationView,
    UpdateResumeView,
    EmailPreferencesView,
    CompanyJobsView,
    ApplicantProfileView,
    JobShareView,
    RestoreJobView,
    ApplicationAuditLogView,
    EmployerJobStatsView,
)

urlpatterns = [
    # Job URLs
    path("", JobListCreateView.as_view(), name="job-list"),
    path("<int:pk>/", JobDetailView.as_view(), name="job-detail"),
    path("<int:job_id>/apply/", ApplyToJobView.as_view(), name="apply"),
    # Application URLs
    path("applications/my/", MyApplicationsView.as_view(), name="my-applications"),
    path(
        "applications/employer/",
        EmployerApplicationsView.as_view(),
        name="employer-applications",
    ),
    path(
        "applications/<int:pk>/status/",
        UpdateApplicationStatusView.as_view(),
        name="update-status",
    ),
    # Withdraw: single canonical URL (removed duplicate at bottom)
    path(
        "applications/<int:application_id>/withdraw/",
        WithdrawApplicationView.as_view(),
        name="withdraw",
    ),
    # Saved Jobs URLs
    path("saved/", SavedJobView.as_view(), name="saved-jobs"),
    path("saved/<int:pk>/", UnsaveJobView.as_view(), name="unsave-job"),
    # Job Alert URLs
    path("alerts/", JobAlertListCreateView.as_view(), name="job-alerts"),
    path("alerts/<int:pk>/", JobAlertDeleteView.as_view(), name="job-alert-delete"),
    # Resume / preferences
    path("update-resume/", UpdateResumeView.as_view(), name="update-resume"),
    path(
        "email-preferences/", EmailPreferencesView.as_view(), name="email-preferences"
    ),
    # Company URLs
    path(
        "company/<int:employer_id>/jobs/",
        CompanyJobsView.as_view(),
        name="company-jobs",
    ),
    path(
        "applicant/<int:user_id>/",
        ApplicantProfileView.as_view(),
        name="applicant-profile",
    ),
    # Share URL
    path("<int:job_id>/share/", JobShareView.as_view(), name="job-share"),
    # Admin URLs
    path(
        "admin/jobs/<int:job_id>/restore/",
        RestoreJobView.as_view(),
        name="restore-job",
    ),
    path(
        "applications/<int:application_id>/audit/",
        ApplicationAuditLogView.as_view(),
        name="audit-log",
    ),
    path(
        "admin/jobs/<int:job_id>/flag/",
        AdminFlagJobView.as_view(),
        name="admin-flag-job",
    ),
    path("analytics/employer/", EmployerAnalyticsView.as_view(), name="employer-analytics"),
    path("analytics/candidate/", CandidateAnalyticsView.as_view(), name="candidate-analytics"),
    path("employer/stats/", EmployerJobStatsView.as_view(), name="employer-stats"),
]
