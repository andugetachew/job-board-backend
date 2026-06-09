import pytest
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from datetime import timedelta


class TestSecurity:
    """Security, file validation, and injection prevention tests"""

    # ─────────────────────────────────────────
    # Token Security
    # ─────────────────────────────────────────

    @pytest.mark.django_db
    def test_invalid_token_rejected(self, api_client):
        api_client.credentials(HTTP_AUTHORIZATION="Bearer faketoken.fake.fake")
        response = api_client.get("/api/auth/profile/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_malformed_auth_header_rejected(self, api_client):
        api_client.credentials(HTTP_AUTHORIZATION="NotBearer sometoken")
        response = api_client.get("/api/auth/profile/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_valid_token_allows_access(self, api_client, test_candidate):
        # Use real login to get a real token
        login = api_client.post(
            "/api/auth/login/",
            {
                "username": "testcandidate",
                "password": "candidate123",
            },
        )
        assert login.status_code == status.HTTP_200_OK
        token = login.data["access"]
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = api_client.get("/api/auth/profile/")
        assert response.status_code == status.HTTP_200_OK

    # ─────────────────────────────────────────
    # File Upload Security
    # ─────────────────────────────────────────

    @pytest.mark.django_db
    def test_invalid_file_type_exe_fails(self, auth_client, test_job):
        invalid_file = SimpleUploadedFile(
            "resume.exe",
            b"fake executable",
            content_type="application/x-msdownload",
        )
        response = auth_client.post(
            f"/api/jobs/{test_job.id}/apply/",
            {"cover_letter": "Test", "resume": invalid_file},
            format="multipart",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_valid_pdf_accepted(self, auth_client, test_job, resume_file):
        response = auth_client.post(
            f"/api/jobs/{test_job.id}/apply/",
            {"cover_letter": "Test cover letter", "resume": resume_file},
            format="multipart",
        )
        assert response.status_code == status.HTTP_201_CREATED

    # ─────────────────────────────────────────
    # Injection Prevention
    # ─────────────────────────────────────────

    @pytest.mark.django_db
    def test_sql_injection_does_not_crash(self, api_client):
        response = api_client.get("/api/jobs/?search=1' OR '1'='1")
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.django_db
    def test_sql_injection_union_does_not_crash(self, api_client):
        response = api_client.get(
            "/api/jobs/?search=1 UNION SELECT username FROM auth_user"
        )
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.django_db
    def test_xss_in_search_does_not_crash(self, api_client):
        response = api_client.get("/api/jobs/?search=<script>alert('xss')</script>")
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.django_db
    def test_xss_job_title_stored_as_raw_text(self, employer_auth_client):
        """
        APIs store raw input — sanitization is the frontend's responsibility.
        This test verifies the API doesn't CRASH on XSS input.
        """
        response = employer_auth_client.post(
            "/api/jobs/",
            {
                "title": "<script>alert('xss')</script>",
                "description": "Test",
                "requirements": "Test",
                "location": "Remote",
                "employment_type": "full",
                "expires_at": (timezone.now() + timedelta(days=30)).isoformat(),
            },
        )
        # API should accept or reject — but NOT crash
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST,
        ]

    # ─────────────────────────────────────────
    # IDOR Prevention
    # ─────────────────────────────────────────

    @pytest.mark.django_db
    def test_user_cannot_access_other_user_application(
        self, api_client, test_employer_2, test_application
    ):
        api_client.force_authenticate(user=test_employer_2)
        response = api_client.patch(
            f"/api/jobs/applications/{test_application.id}/status/",
            {"status": "hired"},
        )
        assert response.status_code in [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        ]
