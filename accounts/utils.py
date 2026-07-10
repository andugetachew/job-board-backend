import secrets


def generate_verification_token():
    """Generate a secure random token for email verification"""
    return secrets.token_urlsafe(32)