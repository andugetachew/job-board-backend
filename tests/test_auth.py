import pytest
from rest_framework import status


class TestAuthentication:
    """Authentication and user management tests"""

    # ─────────────────────────────────────────
    # Registration
    # ─────────────────────────────────────────

    @pytest.mark.django_db
    def test_register_candidate_success(self, api_client):
        response = api_client.post(
            "/api/auth/register/",
            {
                "username": "newcandidate",
                "email": "new@test.com",
                "password": "password123",
                "role": "candidate",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert "access" in response.data
        assert response.data["user"]["role"] == "candidate"

    @pytest.mark.django_db
    def test_register_employer_success(self, api_client):
        response = api_client.post(
            "/api/auth/register/",
            {
                "username": "newemployer",
                "email": "emp@test.com",
                "password": "password123",
                "role": "employer",
                "company": "New Tech Corp",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["user"]["company"] == "New Tech Corp"

    @pytest.mark.django_db
    def test_register_duplicate_email_fails(self, api_client, test_candidate):
        # Email must be unique — same email, different username
        response = api_client.post(
            "/api/auth/register/",
            {
                "username": "differentuser",
                "email": "candidate@test.com",  # same as test_candidate
                "password": "password123",
                "role": "candidate",
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_register_missing_password_fails(self, api_client):
        response = api_client.post(
            "/api/auth/register/",
            {
                "username": "user",
                "email": "u@test.com",
                "role": "candidate",
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # ─────────────────────────────────────────
    # Login — uses username OR email + password
    # ─────────────────────────────────────────

    @pytest.mark.django_db
    def test_login_with_username_success(self, api_client, test_candidate):
        response = api_client.post(
            "/api/auth/login/",
            {
                "username": "testcandidate",
                "password": "candidate123",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

    @pytest.mark.django_db
    def test_login_with_email_success(self, api_client, test_candidate):
        response = api_client.post(
            "/api/auth/login/",
            {
                "email": "candidate@test.com",
                "password": "candidate123",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data

    @pytest.mark.django_db
    def test_login_wrong_password_fails(self, api_client, test_candidate):
        response = api_client.post(
            "/api/auth/login/",
            {
                "username": "testcandidate",
                "password": "wrongpassword",
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_login_nonexistent_user_fails(self, api_client):
        response = api_client.post(
            "/api/auth/login/",
            {
                "username": "nobody",
                "password": "pass123",
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_token_refresh_success(self, api_client, test_candidate):
        login = api_client.post(
            "/api/auth/login/",
            {
                "username": "testcandidate",
                "password": "candidate123",
            },
        )
        assert login.status_code == status.HTTP_200_OK
        refresh_token = login.data["refresh"]
        response = api_client.post(
            "/api/auth/token/refresh/",
            {
                "refresh": refresh_token,
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data

    @pytest.mark.django_db
    def test_invalid_token_rejected(self, api_client):
        api_client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken123")
        response = api_client.get("/api/auth/profile/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # ─────────────────────────────────────────
    # Profile
    # ─────────────────────────────────────────

    @pytest.mark.django_db
    def test_get_profile_authenticated(self, auth_client):
        response = auth_client.get("/api/auth/profile/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["username"] == "testcandidate"

    @pytest.mark.django_db
    def test_get_profile_unauthenticated_fails(self, api_client):
        response = api_client.get("/api/auth/profile/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # ─────────────────────────────────────────
    # Password
    # ─────────────────────────────────────────

    @pytest.mark.django_db
    def test_change_password_success(self, api_client, test_candidate):
        # Login first to get real token (force_authenticate bypasses password check)
        login = api_client.post(
            "/api/auth/login/",
            {
                "username": "testcandidate",
                "password": "candidate123",
            },
        )
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        response = api_client.post(
            "/api/auth/change-password/",
            {
                "old_password": "candidate123",
                "new_password": "newpassword123",
            },
        )
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.django_db
    def test_change_password_wrong_old_fails(self, auth_client):
        response = auth_client.post(
            "/api/auth/change-password/",
            {
                "old_password": "wrongpassword",
                "new_password": "newpassword123",
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_forgot_password_success(self, api_client, test_candidate):
        response = api_client.post(
            "/api/auth/forgot-password/",
            {
                "email": "candidate@test.com",
            },
        )
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.django_db
    def test_forgot_password_nonexistent_email(self, api_client):
        # Should return 200 to avoid email enumeration
        response = api_client.post(
            "/api/auth/forgot-password/",
            {
                "email": "nobody@test.com",
            },
        )
        assert response.status_code == status.HTTP_200_OK
