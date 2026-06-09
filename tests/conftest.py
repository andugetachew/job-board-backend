import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch
from jobs.models import Job, Application, SavedJob, JobAlert
from reviews.models import CompanyReview

User = get_user_model()

from django.core.cache import cache

# ─────────────────────────────────────────────
# API Clients
# ─────────────────────────────────────────────


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(api_client, test_candidate):
    api_client.force_authenticate(user=test_candidate)
    return api_client


@pytest.fixture
def employer_auth_client(api_client, test_employer):
    api_client.force_authenticate(user=test_employer)
    return api_client


@pytest.fixture
def admin_auth_client(api_client, test_admin):
    api_client.force_authenticate(user=test_admin)
    return api_client


# ─────────────────────────────────────────────
# Users
# ─────────────────────────────────────────────


@pytest.fixture
def test_candidate():
    return User.objects.create_user(
        username="testcandidate",
        email="candidate@test.com",
        password="candidate123",
        role="candidate",
        is_email_verified=True,  # ← add this
    )


@pytest.fixture
def test_employer():
    return User.objects.create_user(
        username="testemployer",
        email="employer@test.com",
        password="employer123",
        role="employer",
        company="Test Corp",
        is_email_verified=True,  # ← add this
    )


@pytest.fixture
def test_employer_2():
    return User.objects.create_user(
        username="testemployer2",
        email="employer2@test.com",
        password="employer123",
        role="employer",
        company="Other Corp",
        is_email_verified=True,  # ← add this
    )


@pytest.fixture
def test_admin():
    user = User.objects.create_superuser(
        username="testadmin",
        email="admin@test.com",
        password="admin123",
    )
    user.is_staff = True
    user.is_email_verified = True  # ← add this
    user.save()
    return user


@pytest.fixture
def test_job(test_employer):
    return Job.objects.create(
        employer=test_employer,
        title="Python Developer",
        description="Build scalable APIs",
        requirements="3+ years Python",
        location="Remote",
        is_remote=True,
        is_active=True,  # add this
        employment_type="full",
        salary_min=80000,
        salary_max=120000,
        expires_at=timezone.now() + timedelta(days=30),
    )


@pytest.fixture
def test_job_2(test_employer):
    return Job.objects.create(
        employer=test_employer,
        title="React Developer",
        description="Build frontend components",
        requirements="2+ years React",
        location="New York",
        is_remote=False,
        employment_type="part",
        salary_min=60000,
        salary_max=90000,
        expires_at=timezone.now() + timedelta(days=30),
    )


@pytest.fixture
def expired_job(test_employer):
    return Job.objects.create(
        employer=test_employer,
        title="Expired Job",
        description="This job is expired",
        requirements="N/A",
        location="Remote",
        employment_type="full",
        expires_at=timezone.now() - timedelta(days=1),
    )


@pytest.fixture
def resume_file():
    return SimpleUploadedFile(
        "resume.pdf",
        b"John Doe\nEmail: john@test.com\nPhone: 555-123-4567\nSkills: Python, Django",
        content_type="application/pdf",
    )


@pytest.fixture
def test_application(test_candidate, test_job):
    return Application.objects.create(
        job=test_job,
        candidate=test_candidate,
        cover_letter="I am very interested in this position.",
        status="pending",
    )


@pytest.fixture
def test_saved_job(test_candidate, test_job):
    return SavedJob.objects.create(
        user=test_candidate,
        job=test_job,
    )


@pytest.fixture
def test_job_alert(test_candidate):
    return JobAlert.objects.create(
        user=test_candidate,
        search_keyword="Python",
        location="Remote",
        frequency="daily",
    )


@pytest.fixture
def test_review(test_candidate, test_employer):
    return CompanyReview.objects.create(
        reviewer=test_candidate,
        company=test_employer,
        rating=4,
        comment="Great company to work with!",
    )


@pytest.fixture(autouse=True)
def mock_celery_tasks():
    with patch("accounts.views.send_verification_email.delay") as mock_verify, patch(
        "accounts.views.send_password_reset_email.delay"
    ) as mock_reset, patch(
        "accounts.views.send_welcome_email.delay"
    ) as mock_welcome, patch(
        "jobs.tasks.send_application_confirmation.delay"
    ) as mock_confirm, patch(
        "jobs.tasks.send_status_update_email.delay"
    ) as mock_status, patch(
        "jobs.tasks.send_daily_job_alerts.delay"
    ) as mock_alerts:
        yield {
            "verify": mock_verify,
            "reset": mock_reset,
            "welcome": mock_welcome,
            "confirm": mock_confirm,
            "status": mock_status,
            "alerts": mock_alerts,
        }


@pytest.fixture(autouse=True)
def disable_throttling(settings):
    settings.REST_FRAMEWORK = {
        **getattr(settings, "REST_FRAMEWORK", {}),
        "DEFAULT_THROTTLE_CLASSES": [],
        "DEFAULT_THROTTLE_RATES": {},
    }
    cache.clear()
    with patch("jobs.views.ApplyThrottle.allow_request", return_value=True):
        yield
    cache.clear()
