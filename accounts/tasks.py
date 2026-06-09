

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import User


@shared_task
def send_verification_email(user_id, email, token):
    verification_link = f"{settings.FRONTEND_URL}/verify-email?email={email}&token={token}"

    send_mail(
        "Verify Your Email Address",
        f"Click to verify: {verification_link}",
        settings.DEFAULT_FROM_EMAIL,
        [email],
    )
    return f"Verification email sent to {email}"


@shared_task
def send_password_reset_email(user_id, email, token):
    reset_link = f"{settings.FRONTEND_URL}/reset-password?email={email}&token={token}"

    send_mail(
        "Password Reset Request",
        f"Reset here: {reset_link}",
        settings.DEFAULT_FROM_EMAIL,
        [email],
    )
    return f"Password reset email sent to {email}"


@shared_task
def send_welcome_email(user_id, email, username):
    send_mail(
        "Welcome to Job Board!",
        f"Hello {username}, welcome!",
        settings.DEFAULT_FROM_EMAIL,
        [email],
    )
    return f"Welcome email sent to {email}"


@shared_task
def clean_expired_tokens():
    expiry_time = timezone.now() - timedelta(hours=24)

    expired_users = User.objects.filter(
        email_verification_sent_at__lt=expiry_time,
        is_email_verified=False
    )

    for user in expired_users:
        user.email_verification_token = None
        user.email_verification_sent_at = None
        user.save(update_fields=["email_verification_token", "email_verification_sent_at"])

    # password reset cleanup (SAFE VERSION)
    reset_expiry = timezone.now() - timedelta(hours=1)

    reset_users = User.objects.filter(
        reset_password_sent_at__isnull=False,
        reset_password_sent_at__lt=reset_expiry,
        reset_password_token__isnull=False
    )

    for user in reset_users:
        user.reset_password_token = None
        user.reset_password_sent_at = None
        user.save(update_fields=["reset_password_token", "reset_password_sent_at"])

    return {
        "expired_verification_tokens": expired_users.count(),
        "expired_reset_tokens": reset_users.count(),
    }