from django.test import TestCase
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status
from datetime import timedelta
import uuid


class JobAPITest(TestCase):
    """
    Enterprise-level API tests for Job system
    Clean structure, reusable helpers, minimal repetition
    """

    def setUp(self):
        self.client = APIClient()

        # Pre-create users (faster + cleaner tests)
        self.employer_token = self._register_and_login("employer")
        self.candidate_token = self._register_and_login("candidate")

    def _register_and_login(self, role="candidate", company="Test Co"):
        unique = uuid.uuid4().hex[:8]
        username = f"{role}_{unique}"
        email = f"{username}@test.com"

        data = {
            "username": username,
            "email": email,
            "password": "testpass123",
            "role": role,
        }

        if role == "employer":
            data["company"] = company

        reg = self.client.post("/api/auth/register/", data)
        self.assertEqual(reg.status_code, 201)

        login = self.client.post(
            "/api/auth/login/",
            {"username": username, "password": "testpass123"},
        )
        self.assertEqual(login.status_code, 200)

        return login.data["access"]

    def _auth(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def _create_job(self, token, title="Test Job"):
        self._auth(token)
        resp = self.client.post(
            "/api/jobs/",
            {
                "title": title,
                "description": "Desc",
                "requirements": "Req",
                "location": "Remote",
                "employment_type": "full",
                "expires_at": (timezone.now() + timedelta(days=30)).isoformat(),
            },
        )
        print(f"Job creation response: {resp.status_code} {resp.data}")  # <-- ADD THIS
        return resp

    def _apply_to_job(self, token, job_id):
        self._auth(token)

        resume = SimpleUploadedFile(
            "resume.txt",
            b"John Doe Email: john@test.com Skills: Python",
        )

        return self.client.post(
            f"/api/jobs/{job_id}/apply/",
            {
                "cover_letter": "I want this job",
                "resume": resume,
            },
            format="multipart",
        )

    def test_employer_can_create_job(self):
        resp = self._create_job(self.employer_token, "New Job")

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", resp.data)

    def test_candidate_cannot_create_job(self):
        self._auth(self.candidate_token)

        resp = self.client.post("/api/jobs/", {"title": "Hack Job"})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_anyone_can_view_jobs(self):
        resp = self.client.get("/api/jobs/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_candidate_can_apply_to_job(self):
        job_resp = self._create_job(self.employer_token, "Apply Job")
        job_id = job_resp.data["id"]

        apply_resp = self._apply_to_job(self.candidate_token, job_id)

        self.assertEqual(apply_resp.status_code, status.HTTP_201_CREATED)
        self.assertIn("application_id", apply_resp.data)

    def test_employer_can_update_application_status(self):
        job_resp = self._create_job(self.employer_token, "Status Job")
        job_id = job_resp.data["id"]

        apply_resp = self._apply_to_job(self.candidate_token, job_id)
        app_id = apply_resp.data.get("application_id") or apply_resp.data.get("id")

        self._auth(self.employer_token)

        update_resp = self.client.patch(
            f"/api/jobs/applications/{app_id}/status/",
            {"status": "reviewed"},
            format="json",
        )

        self.assertEqual(update_resp.status_code, 200)
        self.assertEqual(update_resp.data["status"], "reviewed")

    def test_candidate_can_save_job(self):
        job_resp = self._create_job(self.employer_token, "Save Job")
        job_id = job_resp.data["id"]

        self._auth(self.candidate_token)

        resp = self.client.post("/api/jobs/saved/", {"job_id": job_id})

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
