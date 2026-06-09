import pytest
from unittest.mock import patch
from django.utils import timezone
from datetime import timedelta

from accounts.tasks import (
    send_verification_email,
    send_password_reset_email,
    send_welcome_email,
    clean_expired_tokens,
)


@pytest.mark.django_db
class TestAccountTasks:

    @patch("accounts.tasks.send_mail")
    def test_send_verification_email(self, mock_send_mail):
        result = send_verification_email(
            1,
            "user@test.com",
            "abc123"
        )

        assert mock_send_mail.called
        assert result == "Verification email sent to user@test.com"

    @patch("accounts.tasks.send_mail")
    def test_send_password_reset_email(self, mock_send_mail):
        result = send_password_reset_email(
            1,
            "user@test.com",
            "reset123"
        )

        assert mock_send_mail.called
        assert result == "Password reset email sent to user@test.com"

    @patch("accounts.tasks.send_mail")
    def test_send_welcome_email(self, mock_send_mail):
        result = send_welcome_email(
            1,
            "user@test.com",
            "john"
        )

        assert mock_send_mail.called
        assert result == "Welcome email sent to user@test.com"

    @patch("accounts.tasks.send_mail")
    def test_verification_email_recipient(self, mock_send_mail):
        send_verification_email(
            1,
            "user@test.com",
            "abc123"
        )

        recipients = mock_send_mail.call_args[0][3]

        assert "user@test.com" in recipients

    @patch("accounts.tasks.send_mail")
    def test_password_reset_email_recipient(self, mock_send_mail):
        send_password_reset_email(
            1,
            "user@test.com",
            "reset123"
        )

        recipients = mock_send_mail.call_args[0][3]

        assert "user@test.com" in recipients

    @patch("accounts.tasks.send_mail")
    def test_welcome_email_recipient(self, mock_send_mail):
        send_welcome_email(
            1,
            "user@test.com",
            "john"
        )

        recipients = mock_send_mail.call_args[0][3]

        assert "user@test.com" in recipients

    def test_clean_expired_verification_tokens(self, test_candidate):
        test_candidate.email_verification_token = "abc"
        test_candidate.email_verification_sent_at = (
            timezone.now() - timedelta(days=2)
        )
        test_candidate.is_email_verified = False
        test_candidate.save()

        result = clean_expired_tokens()

        test_candidate.refresh_from_db()

        assert test_candidate.email_verification_token is None
        assert result["expired_verification_tokens"] == 1

    def test_clean_expired_reset_tokens(self, test_candidate):
        test_candidate.reset_password_token = "reset123"
        test_candidate.reset_password_sent_at = (
            timezone.now() - timedelta(hours=2)
        )
        test_candidate.save()

        result = clean_expired_tokens()

        test_candidate.refresh_from_db()

        assert test_candidate.reset_password_token is None
        assert result["expired_reset_tokens"] == 1

    def test_clean_expired_tokens_no_expired_users(self):
        result = clean_expired_tokens()

        assert "expired_verification_tokens" in result
        assert "expired_reset_tokens" in result

    @patch("accounts.tasks.send_mail")
    def test_verification_email_subject(self, mock_send_mail):
        send_verification_email(
            1,
            "user@test.com",
            "abc123"
        )

        subject = mock_send_mail.call_args[0][0]

        assert "Verify" in subject