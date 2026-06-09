import pytest
from rest_framework import status


class TestProfiles:
    """User profile features"""

    @pytest.mark.django_db
    def test_get_profile_success(self, auth_client):
        response = auth_client.get("/api/auth/profile/")
        assert response.status_code == status.HTTP_200_OK
        assert "username" in response.data

    @pytest.mark.django_db
    def test_update_profile_success(self, auth_client):
        response = auth_client.patch(
            "/api/auth/profile/update/",
            {"bio": "Backend developer", "location": "Remote"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.django_db
    def test_unauthenticated_profile_access_fails(self, api_client):
        response = api_client.get("/api/auth/profile/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
