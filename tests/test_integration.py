from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from django.utils import timezone
from datetime import timedelta
import time


class IntegrationTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.timestamp = str(int(time.time()))

    def test_full_workflow_employer_candidate(self):
        """Complete flow: Register → Login → Post Job → Apply → Update Status"""

        emp_username = f"emp_{self.timestamp}"
        emp_email = f"{emp_username}@test.com"

        res = self.client.post(
            "/api/auth/register/",
            {
                "username": emp_username,
                "email": emp_email,
                "password": "pass123",
                "role": "employer",
                "company": "Flow Corp",
            },
            format="json",
        )
        self.assertEqual(res.status_code, 201, res.data)

        res = self.client.post(
            "/api/auth/login/",
            {"username": emp_username, "password": "pass123"},
            format="json",
        )
        self.assertEqual(res.status_code, 200, res.data)

        emp_token = res.data.get("access")
        self.assertIsNotNone(emp_token, "No access token returned")

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {emp_token}")

        job_data = {
            "title": "Integration Test Job",
            "description": "Test Description",
            "requirements": "Python, Django",
            "location": "Remote",
            "is_remote": True,
            "employment_type": "full",
            "expires_at": (timezone.now() + timedelta(days=30)).isoformat(),
        }

        res = self.client.post("/api/jobs/", job_data, format="json")
        self.assertEqual(res.status_code, 201, res.data)

        job_id = res.data.get("id")
        self.assertIsNotNone(job_id, "Job ID missing")

        can_username = f"can_{self.timestamp}"
        can_email = f"{can_username}@test.com"

        res = self.client.post(
            "/api/auth/register/",
            {
                "username": can_username,
                "email": can_email,
                "password": "pass123",
                "role": "candidate",
            },
            format="json",
        )
        self.assertEqual(res.status_code, 201, res.data)

        res = self.client.post(
            "/api/auth/login/",
            {"username": can_username, "password": "pass123"},
            format="json",
        )
        self.assertEqual(res.status_code, 200, res.data)

        can_token = res.data.get("access")
        self.assertIsNotNone(can_token, "No candidate token")

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {can_token}")

        resume = SimpleUploadedFile(
            "resume.txt",
            b"Sample resume content",
            content_type="text/plain",
        )

        res = self.client.post(
            f"/api/jobs/{job_id}/apply/",
            {
                "cover_letter": "I want this job",
                "resume": resume,
            },
            format="multipart",
        )

        if res.status_code != 201:
            print("\n--- APPLY DEBUG ---")
            print("Status:", res.status_code)
            print("Response:", res.data)

        self.assertEqual(res.status_code, 201, res.data)

        app_id = res.data.get("application_id") or res.data.get("id")
        self.assertIsNotNone(app_id, "Application ID missing")

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {emp_token}")

        res = self.client.patch(
            f"/api/jobs/applications/{app_id}/status/",
            {"status": "interview"},
            format="json",
        )

        if res.status_code != 200:
            print("\n--- STATUS UPDATE DEBUG ---")
            print("Status:", res.status_code)
            print("Response:", res.data)

        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(res.data.get("status"), "interview")
