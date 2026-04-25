from django.test import TestCase
from django.contrib.auth import get_user_model
from jobs.models import Job, Application, SavedJob
from datetime import datetime, timedelta

User = get_user_model()


class JobModelTest(TestCase):

    def setUp(self):
        self.employer = User.objects.create_user(
            username="emp", email="e@e.com", password="pass", role="employer"
        )

    def test_create_job(self):
        job = Job.objects.create(
            employer=self.employer,
            title="Python Dev",
            description="Build APIs",
            requirements="Python",
            location="Remote",
            expires_at=datetime.now() + timedelta(days=30),
        )
        self.assertEqual(job.title, "Python Dev")
        self.assertEqual(job.views_count, 0)


class ApplicationModelTest(TestCase):

    def setUp(self):
        self.employer = User.objects.create_user(
            username="emp", password="pass", role="employer"
        )
        self.candidate = User.objects.create_user(
            username="can", password="pass", role="candidate"
        )
        self.job = Job.objects.create(
            employer=self.employer,
            title="Job",
            description="D",
            requirements="R",
            location="L",
            expires_at=datetime.now() + timedelta(days=30),
        )

    def test_candidate_can_apply(self):
        app = Application.objects.create(job=self.job, candidate=self.candidate)
        self.assertEqual(app.status, "pending")

    def test_cannot_apply_twice(self):
        Application.objects.create(job=self.job, candidate=self.candidate)
        with self.assertRaises(Exception):
            Application.objects.create(job=self.job, candidate=self.candidate)
