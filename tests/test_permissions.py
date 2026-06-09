import pytest
from rest_framework import status


class TestPermissions:
    """Role-based access control tests"""

    # ─────────────────────────────────────────
    # Unauthenticated
    # ─────────────────────────────────────────

    @pytest.mark.django_db
    def test_unauthenticated_cannot_create_job(self, api_client):
        response = api_client.post("/api/jobs/", {"title": "Test"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_unauthenticated_cannot_apply(self, api_client, test_job):
        response = api_client.post(f"/api/jobs/{test_job.id}/apply/", {})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_unauthenticated_cannot_view_profile(self, api_client):
        response = api_client.get("/api/auth/profile/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # ─────────────────────────────────────────
    # Candidate restrictions
    # ─────────────────────────────────────────

    @pytest.mark.django_db
    def test_candidate_cannot_create_job(self, auth_client):
        response = auth_client.post(
            "/api/jobs/",
            {
                "title": "Fake Job",
                "description": "Not allowed",
            },
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_candidate_cannot_delete_job(self, auth_client, test_job):
        response = auth_client.delete(f"/api/jobs/{test_job.id}/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_candidate_cannot_update_job(self, auth_client, test_job):
        response = auth_client.patch(f"/api/jobs/{test_job.id}/", {"title": "Hacked"})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_candidate_cannot_update_application_status(
        self, auth_client, test_application
    ):
        response = auth_client.patch(
            f"/api/jobs/applications/{test_application.id}/status/",
            {"status": "hired"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    # ─────────────────────────────────────────
    # Employer restrictions
    # ─────────────────────────────────────────

    @pytest.mark.django_db
    def test_employer_cannot_apply(self, employer_auth_client, test_job, resume_file):
        response = employer_auth_client.post(
            f"/api/jobs/{test_job.id}/apply/",
            {"cover_letter": "Test", "resume": resume_file},
            format="multipart",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_employer_cannot_edit_other_employer_job(
        self, api_client, test_employer_2, test_job
    ):
        api_client.force_authenticate(user=test_employer_2)
        response = api_client.patch(f"/api/jobs/{test_job.id}/", {"title": "Stolen"})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_employer_cannot_delete_other_employer_job(
        self, api_client, test_employer_2, test_job
    ):
        api_client.force_authenticate(user=test_employer_2)
        response = api_client.delete(f"/api/jobs/{test_job.id}/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    # ─────────────────────────────────────────
    # Admin access
    # ─────────────────────────────────────────

    @pytest.mark.django_db
    def test_admin_can_view_stats(self, admin_auth_client):
        response = admin_auth_client.get("/api/admin/stats/")
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.django_db
    def test_admin_can_view_all_applications(self, admin_auth_client):
        response = admin_auth_client.get("/api/admin/recent-users/")
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.django_db
    def test_admin_can_delete_any_job(self, admin_auth_client, test_job):
        # Admin uses the admin-specific delete endpoint
        response = admin_auth_client.delete(f"/api/admin/jobs/{test_job.id}/")
        assert response.status_code in [
            status.HTTP_204_NO_CONTENT,
            status.HTTP_200_OK,
        ]
