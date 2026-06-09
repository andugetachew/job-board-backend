import secrets
from django.core.mail import send_mail
from django.conf import settings


def generate_verification_token():
    """Generate a secure random token for email verification"""
    return secrets.token_urlsafe(32)


def send_verification_email(user_email, token):
    """Backend only sends the email - NO HTML generation"""
    subject = "Verify Your Email"
    message = f"Your verification token: {token}"
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user_email],
        fail_silently=False,
    )


def send_password_reset_email(user_email, token):
    """Send password reset email"""
    subject = "Password Reset Request"
    message = f"Your password reset token: {token}"
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user_email],
        fail_silently=False,
    )


def send_welcome_email(user_email, username):
    """Send welcome email after successful registration"""
    subject = "Welcome to Job Board!"
    message = f"Hi {username}, welcome to Job Board! Your account has been created successfully."
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user_email],
        fail_silently=False,
    )