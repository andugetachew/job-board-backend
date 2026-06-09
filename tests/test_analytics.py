import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from jobs.models import Job, Application, SavedJob, JobAlert

User = get_user_model()


@pytest.mark.django_db
class TestEmployerAnalyticsView:

    def setup_method(self):
        self.client = APIClient()

        self.employer = User.objects.create_user(
            username="employer1",
            password="testpass",
            role="employer",
        )

        self.candidate = User.objects.create_user(
            username="candidate1",
            password="testpass",
            role="candidate",
        )

        self.candidate2 = User.objects.create_user(
            username="candidate2",
            password="testpass",
            role="candidate",
        )

        self.job1 = Job.objects.create(
            title="Backend Dev",
            employer=self.employer,
            is_active=True,
            views_count=100,
            expires_at=timezone.now() + timedelta(days=30),
        )

        self.job2 = Job.objects.create(
            title="Frontend Dev",
            employer=self.employer,
            is_active=False,
            views_count=50,
            expires_at=timezone.now() + timedelta(days=30),
        )

        Application.objects.create(
            job=self.job1,
            candidate=self.candidate,
            status="pending",
            resume="resumes/dummy.pdf",
        )
        Application.objects.create(
            job=self.job1,
            candidate=self.candidate2,
            status="accepted",
            resume="resumes/dummy.pdf",
        )

    def test_only_employer_can_access(self):
        self.client.force_authenticate(user=self.candidate)
        response = self.client.get("/api/analytics/employer/")
        assert response.status_code == 403
        assert "Only employers" in response.data["error"]

    def test_employer_analytics_summary(self):
        self.client.force_authenticate(user=self.employer)
        response = self.client.get("/api/analytics/employer/")
        assert response.status_code == 200
        data = response.data["summary"]
        assert data["total_jobs"] == 2
        assert data["active_jobs"] == 1
        assert data["total_applications"] == 2
        assert data["total_views"] == 150
        assert data["application_rate"] == round((2 / 150 * 100), 1)

    def test_top_jobs_returned(self):
        self.client.force_authenticate(user=self.employer)
        response = self.client.get("/api/analytics/employer/")
        assert response.status_code == 200
        top_jobs = response.data["top_jobs"]
        assert len(top_jobs) <= 5
        assert top_jobs[0]["id"] == self.job1.id

    def test_recent_applications_structure(self):
        self.client.force_authenticate(user=self.employer)
        response = self.client.get("/api/analytics/employer/")
        recent = response.data["recent_applications"]
        assert len(recent) == 2
        assert "candidate__username" in recent[0]
        assert "job__title" in recent[0]
        assert "status" in recent[0]


@pytest.mark.django_db
class TestCandidateAnalyticsView:

    def setup_method(self):
        self.client = APIClient()

        self.candidate = User.objects.create_user(
            username="candidate1",
            password="testpass",
            role="candidate",
        )

        self.employer = User.objects.create_user(
            username="employer1",
            password="testpass",
            role="employer",
        )

        self.job = Job.objects.create(
            title="Backend Dev",
            employer=self.employer,
            views_count=10,
            expires_at=timezone.now() + timedelta(days=30),
        )

        Application.objects.create(
            job=self.job,
            candidate=self.candidate,
            status="pending",
            resume="resumes/dummy.pdf",
        )

        SavedJob.objects.create(candidate=self.candidate, job=self.job)

        JobAlert.objects.create(
            candidate=self.candidate,
            search_keyword="python",
            is_active=True,
        )

    def test_only_candidate_can_access(self):
        self.client.force_authenticate(user=self.employer)
        response = self.client.get("/api/analytics/candidate/")
        assert response.status_code == 403
        assert "Only candidates" in response.data["error"]

    def test_candidate_summary(self):
        self.client.force_authenticate(user=self.candidate)
        response = self.client.get("/api/analytics/candidate/")
        assert response.status_code == 200
        assert response.data["total_applications"] == 1
        assert response.data["saved_jobs"] == 1
        assert response.data["active_alerts"] == 1

    def test_recent_applications(self):
        self.client.force_authenticate(user=self.candidate)
        response = self.client.get("/api/analytics/candidate/")
        recent = response.data["recent_applications"]
        assert len(recent) == 1
        assert recent[0]["job__title"] == "Backend Dev"