import pytest
from django.utils import timezone
from datetime import timedelta
from rest_framework import status


class TestVerifyEmailView:
    """Covers VerifyEmailView.post - entirely untested (lines 64-90)"""

    @pytest.mark.django_db
    def test_verify_with_valid_token_succeeds(self, api_client, test_candidate):
        test_candidate.is_email_verified = False
        test_candidate.email_verification_token = "validtoken123"
        test_candidate.email_verification_sent_at = timezone.now()
        test_candidate.save()

        response = api_client.post(
            "/api/auth/verify-email/",
            {"email": test_candidate.email, "token": "validtoken123"},
        )
        assert response.status_code == status.HTTP_200_OK
        test_candidate.refresh_from_db()
        assert test_candidate.is_email_verified is True
        assert test_candidate.email_verification_token is None

    @pytest.mark.django_db
    def test_verify_with_expired_token_fails(self, api_client, test_candidate):
        test_candidate.is_email_verified = False
        test_candidate.email_verification_token = "expiredtoken"
        test_candidate.email_verification_sent_at = timezone.now() - timedelta(hours=25)
        test_candidate.save()

        response = api_client.post(
            "/api/auth/verify-email/",
            {"email": test_candidate.email, "token": "expiredtoken"},
        )
        assert response.status_code == 400
        assert "expired" in response.data["error"].lower()

    @pytest.mark.django_db
    def test_verify_with_invalid_token_fails(self, api_client, test_candidate):
        response = api_client.post(
            "/api/auth/verify-email/",
            {"email": test_candidate.email, "token": "wrongtoken"},
        )
        assert response.status_code == 400
        assert "invalid" in response.data["error"].lower()


class TestResendVerificationEmailView:
    """Covers ResendVerificationEmailView.post - entirely untested (lines 97-116)"""

    @pytest.mark.django_db
    def test_resend_for_unverified_user_succeeds(self, api_client, test_candidate):
        test_candidate.is_email_verified = False
        test_candidate.save()

        response = api_client.post(
            "/api/auth/resend-verification/", {"email": test_candidate.email}
        )
        assert response.status_code == 200
        test_candidate.refresh_from_db()
        assert test_candidate.email_verification_token is not None

    @pytest.mark.django_db
    def test_resend_for_already_verified_user_fails(self, api_client, test_candidate):
        test_candidate.is_email_verified = True
        test_candidate.save()

        response = api_client.post(
            "/api/auth/resend-verification/", {"email": test_candidate.email}
        )
        assert response.status_code == 400
        assert "already verified" in response.data["error"].lower()

    @pytest.mark.django_db
    def test_resend_for_nonexistent_user_returns_404(self, api_client):
        response = api_client.post(
            "/api/auth/resend-verification/", {"email": "nobody@test.com"}
        )
        assert response.status_code == 404


class TestLoginViewUnverifiedBranch:
    """Covers the unverified-email rejection branch in LoginView (line 130)"""

    @pytest.mark.django_db
    def test_login_blocked_for_unverified_email(self, api_client, test_candidate):
        test_candidate.is_email_verified = False
        test_candidate.save()

        response = api_client.post(
            "/api/auth/login/",
            {"username": test_candidate.username, "password": "candidate123"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "verify" in response.data["error"].lower()


class TestForgotPasswordNonexistentUser:
    """Covers the DoesNotExist branch in ForgotPasswordView (line 189)"""

    @pytest.mark.django_db
    def test_forgot_password_for_nonexistent_email_returns_generic_message(
        self, api_client
    ):
        response = api_client.post(
            "/api/auth/forgot-password/", {"email": "ghost@test.com"}
        )
        # Deliberately returns 200 with a generic message to avoid leaking
        # which emails are registered.
        assert response.status_code == 200
        assert "if an account exists" in response.data["message"].lower()


class TestResetPasswordView:
    """Covers ResetPasswordView.post - mostly untested (lines 218-238)"""

    @pytest.mark.django_db
    def test_reset_with_valid_token_succeeds(self, api_client, test_candidate):
        test_candidate.reset_password_token = "validresettoken"
        test_candidate.reset_password_sent_at = timezone.now()
        test_candidate.save()

        response = api_client.post(
            "/api/auth/reset-password/",
            {
                "email": test_candidate.email,
                "token": "validresettoken",
                "new_password": "brandnewpass123",
            },
        )
        assert response.status_code == 200
        test_candidate.refresh_from_db()
        assert test_candidate.check_password("brandnewpass123")
        assert test_candidate.reset_password_token is None

    @pytest.mark.django_db
    def test_reset_with_expired_token_fails(self, api_client, test_candidate):
        test_candidate.reset_password_token = "oldtoken"
        test_candidate.reset_password_sent_at = timezone.now() - timedelta(hours=2)
        test_candidate.save()

        response = api_client.post(
            "/api/auth/reset-password/",
            {
                "email": test_candidate.email,
                "token": "oldtoken",
                "new_password": "newpass456",
            },
        )
        assert response.status_code == 400
        assert "expired" in response.data["error"].lower()

    @pytest.mark.django_db
    def test_reset_with_invalid_token_fails(self, api_client, test_candidate):
        response = api_client.post(
            "/api/auth/reset-password/",
            {
                "email": test_candidate.email,
                "token": "wrongtoken",
                "new_password": "whatever123",
            },
        )
        assert response.status_code == 400
        assert "invalid" in response.data["error"].lower()


class TestAdminBlockUserView:
    """Covers AdminBlockUserView.post and .delete - entirely untested (lines 245-260)"""

    @pytest.mark.django_db
    def test_admin_can_block_user(self, admin_auth_client, test_candidate):
        response = admin_auth_client.post(
            f"/api/auth/admin/users/{test_candidate.id}/block/"
        )
        assert response.status_code == 200
        test_candidate.refresh_from_db()
        assert test_candidate.is_active is False

    @pytest.mark.django_db
    def test_admin_can_unblock_user(self, admin_auth_client, test_candidate):
        test_candidate.is_active = False
        test_candidate.save()

        response = admin_auth_client.delete(
            f"/api/auth/admin/users/{test_candidate.id}/block/"
        )
        assert response.status_code == 200
        test_candidate.refresh_from_db()
        assert test_candidate.is_active is True

    @pytest.mark.django_db
    def test_block_nonexistent_user_returns_404(self, admin_auth_client):
        response = admin_auth_client.post("/api/auth/admin/users/99999/block/")
        assert response.status_code == 404

    @pytest.mark.django_db
    def test_non_admin_cannot_block_user(self, auth_client, test_candidate):
        response = auth_client.post(
            f"/api/auth/admin/users/{test_candidate.id}/block/"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN