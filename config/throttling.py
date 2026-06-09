from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class ApplyThrottle(UserRateThrottle):
    """Limit job applications"""

    rate = "5/hour"

    def get_cache_key(self, request, view):
        # Rate limit based on user ID
        if request.user.is_authenticated:
            return f"throttle_apply_{request.user.id}"
        return None  # Unauthenticated users cannot apply


class ReviewThrottle(UserRateThrottle):
    """Limit company reviews"""

    rate = "3/day"


class LoginThrottle(AnonRateThrottle):
    """Limit failed login attempts"""

    rate = "10/15min"


class SensitiveActionThrottle(UserRateThrottle):
    """For password change, email change, etc."""

    rate = "3/hour"


class SearchThrottle(AnonRateThrottle):
    """Limit search queries from unauthenticated users"""

    rate = "30/hour"


class BurstThrottle(UserRateThrottle):
    """For very quick repeated requests"""

    rate = "60/minute"
