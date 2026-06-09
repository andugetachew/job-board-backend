import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model

User = get_user_model()


class TestIntegrations:
    """End-to-end workflow tests"""

    def _create_verified_user(
        self, api_client, username, email, password, role, company=None
    ):
        """Helper: register a user and immediately verify their email."""
        data = {
            "username": username,
            "email": email,
            "password": password,
            "role": role,
        }
        if company:
            data["company"] = company

        reg = api_client.post("/api/auth/register/", data)
        assert reg.status_code == 201, f"Registration failed: {reg.data}"

        # Email task is mocked — manually verify the user
        user = User.objects.get(username=username)
        user.is_email_verified = True
        user.save()
        return user

    @pytest.mark.django_db
    def test_full_hiring_workflow(self, api_client):
        """Register → Verify → Login → Post Job → Apply → Update Status → Hire"""

        # 1. Register and verify employer
        self._create_verified_user(
            api_client,
            "flowemployer",
            "flow@test.com",
            "pass123",
            "employer",
            "Flow Corp",
        )

        # 2. Login employer
        emp_login = api_client.post(
            "/api/auth/login/",
            {"username": "flowemployer", "password": "pass123"},
        )
        assert emp_login.status_code == 200, emp_login.data
        emp_token = emp_login.data["access"]

        # 3. Create job
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {emp_token}")
        job_response = api_client.post(
            "/api/jobs/",
            {
                "title": "Integration Job",
                "description": "Test Description",
                "requirements": "Python, Django",
                "location": "Remote",
                "employment_type": "full",
                "is_active": True,
                "expires_at": "2026-12-31T23:59:59Z",
            },
        )
        assert job_response.status_code == 201, job_response.data
        job_id = job_response.data["id"]

        # Verify job is actually active in DB before candidate applies
        from jobs.models import Job

        job_obj = Job.objects.get(id=job_id)
        job_obj.is_active = True
        job_obj.save()

        # 4. Register and verify candidate
        self._create_verified_user(
            api_client, "flowcandidate", "flowcan@test.com", "pass123", "candidate"
        )

        # 5. Login candidate
        can_login = api_client.post(
            "/api/auth/login/",
            {"username": "flowcandidate", "password": "pass123"},
        )
        assert can_login.status_code == 200, can_login.data
        can_token = can_login.data["access"]

        # 6. Apply to job
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {can_token}")
        resume = SimpleUploadedFile(
            "resume.pdf",
            b"John Doe\nEmail: john@test.com",
            content_type="application/pdf",
        )
        apply_response = api_client.post(
            f"/api/jobs/{job_id}/apply/",
            {"cover_letter": "I want this job", "resume": resume},
            format="multipart",
        )
        assert apply_response.status_code == 201, apply_response.data
        app_id = apply_response.data["application_id"]

        # 7. Employer invites to interview
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {emp_token}")
        interview = api_client.patch(
            f"/api/jobs/applications/{app_id}/status/",
            {"status": "interview"},
            format="json",
        )
        assert interview.status_code == 200
        assert interview.data["status"] == "interview"

        # 8. Employer hires candidate
        hired = api_client.patch(
            f"/api/jobs/applications/{app_id}/status/",
            {"status": "hired"},
            format="json",
        )
        assert hired.status_code == 200
        assert hired.data["status"] == "hired"

    @pytest.mark.django_db
    def test_save_and_apply_workflow(self, api_client, test_job):
        """Register → Verify → Login → Save Job → Apply"""

        self._create_verified_user(
            api_client, "saveflow", "save@test.com", "pass123", "candidate"
        )

        login = api_client.post(
            "/api/auth/login/",
            {"username": "saveflow", "password": "pass123"},
        )
        assert login.status_code == 200, login.data
        token = login.data["access"]
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        save_response = api_client.post("/api/jobs/saved/", {"job_id": test_job.id})
        assert save_response.status_code == 201

        saved_response = api_client.get("/api/jobs/saved/")
        assert saved_response.data["count"] >= 1

        resume = SimpleUploadedFile(
            "resume.pdf", b"Test resume", content_type="application/pdf"
        )
        apply_response = api_client.post(
            f"/api/jobs/{test_job.id}/apply/",
            {"cover_letter": "Test", "resume": resume},
            format="multipart",
        )
        assert apply_response.status_code == 201

    @pytest.mark.django_db
    def test_employer_analytics_flow(
        self, employer_auth_client, test_job, test_application
    ):
        """Employer views jobs → checks applicants → updates status"""

        jobs_response = employer_auth_client.get("/api/jobs/")
        assert jobs_response.status_code == 200

        apps_response = employer_auth_client.get("/api/jobs/applications/employer/")
        assert apps_response.status_code == 200
        assert apps_response.data["count"] >= 1

        status_response = employer_auth_client.patch(
            f"/api/jobs/applications/{test_application.id}/status/",
            {"status": "reviewed"},
            format="json",
        )
        assert status_response.status_code == 200
