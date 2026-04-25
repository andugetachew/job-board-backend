from django.test import TestCase
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from datetime import datetime, timedelta


class IntegrationTest(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_full_workflow_employer_candidate(self):
        """Complete flow: Register → Post Job → Apply → Update Status → Email"""

        # 1. Register employer
        self.client.post(
            "/api/auth/register/",
            {
                "username": "emp",
                "email": "emp@test.com",
                "password": "pass",
                "role": "employer",
                "company": "Test Co",
            },
        )
        emp_login = self.client.post(
            "/api/auth/login/", {"username": "emp", "password": "pass"}
        )
        emp_token = emp_login.data["access"]

        # 2. Post job
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {emp_token}")
        job = self.client.post(
            "/api/jobs/",
            {
                "title": "Integration Job",
                "description": "Desc",
                "requirements": "Req",
                "location": "Remote",
                "employment_type": "full",
                "expires_at": (datetime.now() + timedelta(days=30)).isoformat(),
            },
        )
        job_id = job.data["id"]

        # 3. Register candidate
        self.client.post(
            "/api/auth/register/",
            {
                "username": "can",
                "email": "can@test.com",
                "password": "pass",
                "role": "candidate",
            },
        )
        can_login = self.client.post(
            "/api/auth/login/", {"username": "can", "password": "pass"}
        )
        can_token = can_login.data["access"]

        # 4. Apply to job
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {can_token}")
        resume = SimpleUploadedFile(
            "resume.txt", b"Email: john@test.com, Skills: Python"
        )
        apply = self.client.post(
            f"/api/jobs/{job_id}/apply/",
            {"cover_letter": "I want this job", "resume": resume},
            format="multipart",
        )
        app_id = apply.data["id"]

        # 5. Employer updates status
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {emp_token}")
        status_update = self.client.patch(
            f"/api/jobs/applications/{app_id}/status/", {"status": "interview"}
        )

        # 6. Assertions
        self.assertEqual(status_update.status_code, 200)
        self.assertEqual(status_update.data["status"], "interview")

        # 7. Verify email was sent
        self.assertGreaterEqual(
            len(mail.outbox), 2
        )  # Application confirmation + status update

    def test_candidate_cannot_apply_twice(self):
        """Duplicate application prevention"""

        # Setup employer and job
        self.client.post(
            "/api/auth/register/",
            {
                "username": "emp2",
                "email": "emp2@test.com",
                "password": "pass",
                "role": "employer",
            },
        )
        emp_login = self.client.post(
            "/api/auth/login/", {"username": "emp2", "password": "pass"}
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {emp_login.data["access"]}')
        job = self.client.post(
            "/api/jobs/",
            {
                "title": "Test Job",
                "description": "D",
                "requirements": "R",
                "location": "L",
                "employment_type": "full",
                "expires_at": (datetime.now() + timedelta(days=30)).isoformat(),
            },
        )
        job_id = job.data["id"]

        # Setup candidate
        self.client.post(
            "/api/auth/register/",
            {
                "username": "can2",
                "email": "can2@test.com",
                "password": "pass",
                "role": "candidate",
            },
        )
        can_login = self.client.post(
            "/api/auth/login/", {"username": "can2", "password": "pass"}
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {can_login.data["access"]}')
        resume = SimpleUploadedFile("resume.txt", b"Test")

        # First application - should succeed
        first = self.client.post(
            f"/api/jobs/{job_id}/apply/",
            {"cover_letter": "First", "resume": resume},
            format="multipart",
        )
        self.assertEqual(first.status_code, 201)

        # Second application - should fail
        second = self.client.post(
            f"/api/jobs/{job_id}/apply/",
            {"cover_letter": "Second", "resume": resume},
            format="multipart",
        )
        self.assertEqual(second.status_code, 400)
