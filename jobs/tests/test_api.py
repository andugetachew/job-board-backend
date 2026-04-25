from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status
from datetime import datetime, timedelta


class JobAPITest(TestCase):

    def setUp(self):
        self.client = APIClient()

    def register_and_login(self, role="candidate"):
        self.client.post(
            "/api/auth/register/",
            {
                "username": f"user_{role}",
                "email": f"{role}@test.com",
                "password": "pass123",
                "role": role,
            },
        )
        response = self.client.post(
            "/api/auth/login/", {"username": f"user_{role}", "password": "pass123"}
        )
        return response.data["access"]

    def test_employer_can_create_job(self):
        token = self.register_and_login("employer")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = self.client.post(
            "/api/jobs/",
            {
                "title": "New Job",
                "description": "Desc",
                "requirements": "Req",
                "location": "Remote",
                "employment_type": "full",
                "expires_at": (datetime.now() + timedelta(days=30)).isoformat(),
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_candidate_cannot_create_job(self):
        token = self.register_and_login("candidate")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = self.client.post("/api/jobs/", {"title": "Hacker Job"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anyone_can_view_jobs(self):
        response = self.client.get("/api/jobs/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_candidate_can_apply_to_job(self):
        # Create job as employer
        emp_token = self.register_and_login("employer")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {emp_token}")
        job = self.client.post(
            "/api/jobs/",
            {
                "title": "Apply Job",
                "description": "D",
                "requirements": "R",
                "location": "L",
                "employment_type": "full",
                "expires_at": (datetime.now() + timedelta(days=30)).isoformat(),
            },
        )
        job_id = job.data["id"]

        # Apply as candidate
        can_token = self.register_and_login("candidate")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {can_token}")
        resume = SimpleUploadedFile("resume.txt", b"John Doe, Email: john@test.com")

        response = self.client.post(
            f"/api/jobs/{job_id}/apply/",
            {"cover_letter": "I want this", "resume": resume},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_employer_can_update_application_status(self):
        # Create job and application
        emp_token = self.register_and_login("employer")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {emp_token}")
        job = self.client.post(
            "/api/jobs/",
            {
                "title": "Status Job",
                "description": "D",
                "requirements": "R",
                "location": "L",
                "employment_type": "full",
                "expires_at": (datetime.now() + timedelta(days=30)).isoformat(),
            },
        )
        job_id = job.data["id"]

        can_token = self.register_and_login("candidate")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {can_token}")
        resume = SimpleUploadedFile("resume.txt", b"Resume")
        app = self.client.post(
            f"/api/jobs/{job_id}/apply/",
            {"cover_letter": "Test", "resume": resume},
            format="multipart",
        )
        app_id = app.data["id"]

        # Update status
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {emp_token}")
        response = self.client.patch(
            f"/api/jobs/applications/{app_id}/status/", {"status": "reviewed"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "reviewed")

    def test_candidate_can_save_job(self):
        # Create job
        emp_token = self.register_and_login("employer")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {emp_token}")
        job = self.client.post(
            "/api/jobs/",
            {
                "title": "Save Job",
                "description": "D",
                "requirements": "R",
                "location": "L",
                "employment_type": "full",
                "expires_at": (datetime.now() + timedelta(days=30)).isoformat(),
            },
        )
        job_id = job.data["id"]

        # Save job
        can_token = self.register_and_login("candidate")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {can_token}")
        response = self.client.post("/api/jobs/saved/", {"job_id": job_id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
