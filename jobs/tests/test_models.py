from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from jobs.models import Job, Application, SavedJob, JobAlert
from datetime import timedelta

User = get_user_model()


class JobModelTest(TestCase):
    def setUp(self):
        self.employer = User.objects.create_user(
            username="emp", email="emp@test.com", password="pass", role="employer"
        )

    def test_create_job(self):
        job = Job.objects.create(
            employer=self.employer,
            title="Python Dev",
            description="Build APIs",
            requirements="Python",
            location="Remote",
            expires_at=timezone.now() + timedelta(days=30),
        )
        self.assertEqual(job.title, "Python Dev")
        self.assertEqual(job.views_count, 0)

    def test_job_ordering_by_created_desc(self):
        job1 = Job.objects.create(
            employer=self.employer,
            title="First",
            description="D",
            requirements="R",
            location="L",
            expires_at=timezone.now() + timedelta(days=30),
        )
        job2 = Job.objects.create(
            employer=self.employer,
            title="Second",
            description="D",
            requirements="R",
            location="L",
            expires_at=timezone.now() + timedelta(days=30),
        )
        jobs = Job.objects.all()
        self.assertEqual(jobs[0].title, "Second")


class ApplicationModelTest(TestCase):
    def setUp(self):
        self.employer = User.objects.create_user(
            username="emp", email="e@e.com", password="pass", role="employer"
        )
        self.candidate = User.objects.create_user(
            username="can", email="c@c.com", password="pass", role="candidate"
        )
        self.job = Job.objects.create(
            employer=self.employer,
            title="Test Job",
            description="D",
            requirements="R",
            location="L",
            expires_at=timezone.now() + timedelta(days=30),
        )

    def test_create_application(self):
        app = Application.objects.create(
            job=self.job,
            candidate=self.candidate,
            cover_letter="I want this job",
            status="pending",
        )
        self.assertEqual(app.status, "pending")

    def test_unique_job_candidate_constraint(self):
        Application.objects.create(job=self.job, candidate=self.candidate)
        with self.assertRaises(Exception):
            Application.objects.create(job=self.job, candidate=self.candidate)


class SavedJobModelTest(TestCase):
    def setUp(self):
        self.candidate = User.objects.create_user(
            username="can", email="c@c.com", password="pass", role="candidate"
        )
        self.employer = User.objects.create_user(
            username="emp", email="e@e.com", password="pass", role="employer"
        )
        self.job = Job.objects.create(
            employer=self.employer,
            title="Job",
            description="D",
            requirements="R",
            location="L",
            expires_at=timezone.now() + timedelta(days=30),
        )

    def test_save_job(self):
        saved = SavedJob.objects.create(candidate=self.candidate, job=self.job)
        self.assertEqual(saved.candidate.username, "can")
        self.assertEqual(saved.job.title, "Job")
        self.assertIsNotNone(saved.saved_at)

    def test_unique_save_constraint(self):
        SavedJob.objects.create(candidate=self.candidate, job=self.job)
        with self.assertRaises(Exception):
            SavedJob.objects.create(candidate=self.candidate, job=self.job)


class JobAlertModelTest(TestCase):
    def setUp(self):
        self.candidate = User.objects.create_user(
            username="can", email="c@c.com", password="pass", role="candidate"
        )

    def test_create_job_alert(self):
        alert = JobAlert.objects.create(
            candidate=self.candidate,
            search_keyword="Python",
            location="Remote",
            is_remote=True,
            frequency="daily",
        )
        self.assertEqual(alert.search_keyword, "Python")
        self.assertTrue(alert.is_active)
