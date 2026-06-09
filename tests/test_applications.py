import pytest
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile


class TestApplications:
    """Application submission, status, and management tests"""

    # ─────────────────────────────────────────
    # Apply
    # ─────────────────────────────────────────

    @pytest.mark.django_db
    def test_apply_to_job_success(self, auth_client, test_job, resume_file):
        response = auth_client.post(
            f"/api/jobs/{test_job.id}/apply/",
            {"cover_letter": "I am very interested.", "resume": resume_file},
            format="multipart",
        )
        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.django_db
    def test_apply_without_auth_fails(self, api_client, test_job, resume_file):
        response = api_client.post(
            f"/api/jobs/{test_job.id}/apply/",
            {"cover_letter": "Test", "resume": resume_file},
            format="multipart",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_employer_cannot_apply(self, employer_auth_client, test_job, resume_file):
        response = employer_auth_client.post(
            f"/api/jobs/{test_job.id}/apply/",
            {"cover_letter": "Test", "resume": resume_file},
            format="multipart",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_apply_to_nonexistent_job_fails(self, auth_client, resume_file):
        response = auth_client.post(
            "/api/jobs/99999/apply/",
            {"cover_letter": "Test", "resume": resume_file},
            format="multipart",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.django_db
    def test_duplicate_application_fails(self, auth_client, test_job, resume_file):
        auth_client.post(
            f"/api/jobs/{test_job.id}/apply/",
            {"cover_letter": "First", "resume": resume_file},
            format="multipart",
        )
        resume_file2 = SimpleUploadedFile(
            "resume2.pdf", b"Second resume", content_type="application/pdf"
        )
        response = auth_client.post(
            f"/api/jobs/{test_job.id}/apply/",
            {"cover_letter": "Second", "resume": resume_file2},
            format="multipart",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # ─────────────────────────────────────────
    # Candidate: My Applications
    # ─────────────────────────────────────────

    @pytest.mark.django_db
    def test_candidate_can_view_own_applications(self, auth_client, test_application):
        response = auth_client.get("/api/jobs/applications/my/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] >= 1

    @pytest.mark.django_db
    def test_withdraw_application_success(self, auth_client, test_application):
        # Correct URL: /api/jobs/applications/<id>/withdraw/
        response = auth_client.delete(
            f"/api/jobs/applications/{test_application.id}/withdraw/"
        )
        assert response.status_code in [
            status.HTTP_204_NO_CONTENT,
            status.HTTP_200_OK,
        ]

    @pytest.mark.django_db
    def test_withdraw_other_user_application_fails(
        self, api_client, test_employer_2, test_application
    ):
        api_client.force_authenticate(user=test_employer_2)
        response = api_client.delete(
            f"/api/jobs/applications/{test_application.id}/withdraw/"
        )
        assert response.status_code in [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        ]

    # ─────────────────────────────────────────
    # Employer: Manage Applications
    # ─────────────────────────────────────────

    @pytest.mark.django_db
    def test_employer_can_view_applications(
        self, employer_auth_client, test_application
    ):
        response = employer_auth_client.get("/api/jobs/applications/employer/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] >= 1

    @pytest.mark.django_db
    def test_employer_update_status_success(
        self, employer_auth_client, test_application
    ):
        response = employer_auth_client.patch(
            f"/api/jobs/applications/{test_application.id}/status/",
            {"status": "interview"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "interview"

    @pytest.mark.django_db
    def test_employer_update_invalid_status_fails(
        self, employer_auth_client, test_application
    ):
        response = employer_auth_client.patch(
            f"/api/jobs/applications/{test_application.id}/status/",
            {"status": "invalid_status"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_candidate_cannot_update_status(self, auth_client, test_application):
        response = auth_client.patch(
            f"/api/jobs/applications/{test_application.id}/status/",
            {"status": "hired"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    # ─────────────────────────────────────────
    # Status Flow
    # ─────────────────────────────────────────

    @pytest.mark.django_db
    def test_full_status_flow(self, employer_auth_client, test_application):
        for new_status in ["reviewed", "interview", "hired"]:
            response = employer_auth_client.patch(
                f"/api/jobs/applications/{test_application.id}/status/",
                {"status": new_status},
                format="json",
            )
            assert response.status_code == status.HTTP_200_OK
            assert response.data["status"] == new_status
