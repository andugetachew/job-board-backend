from django.core.cache import cache
from functools import wraps
from rest_framework.response import Response

CACHE_JOB_LIST = "job_list_{}"
CACHE_JOB_DETAIL = "job_detail_{}"
CACHE_COMPANY_RATING = "company_rating_{}"
CACHE_USER_PROFILE = "user_profile_{}"

CACHE_TTL_SHORT = 60 * 5
CACHE_TTL_MEDIUM = 60 * 15
CACHE_TTL_LONG = 60 * 60


def cache_response(key_prefix, ttl=CACHE_TTL_MEDIUM):
    """
    Decorator to cache API responses.
    Only caches GET requests with status 200.
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            if request.method != "GET":
                return view_func(self, request, *args, **kwargs)

            cache_key = f"{key_prefix}_{request.get_full_path()}"

            cached_response = cache.get(cache_key)
            if cached_response:
                # Reconstruct Response object from cached data
                return Response(
                    cached_response.get("data"), status=cached_response.get("status")
                )

            response = view_func(self, request, *args, **kwargs)

            if response.status_code == 200:
                # Store serializable data instead of Response object
                cache_data = {"data": response.data, "status": response.status_code}
                cache.set(cache_key, cache_data, ttl)

            return response

        return wrapper

    return decorator


def invalidate_job_cache():
    """Clear all job-related caches"""
    # For Django Redis, use pattern delete if available
    try:
        cache.delete_pattern("job_list_*")
        cache.delete_pattern("job_detail_*")
    except AttributeError:
        # If delete_pattern not available, clear all (not ideal but works)
        cache.clear()


def invalidate_job_list_cache():
    """Clear only job list caches"""
    try:
        cache.delete_pattern("job_list_*")
    except AttributeError:
        pass


def invalidate_job_detail_cache(job_id):
    """Clear specific job detail cache"""
    cache.delete(f"job_detail_{job_id}")


def invalidate_company_rating(company_id):
    """Clear company rating cache"""
    cache.delete(f"company_rating_{company_id}")


def invalidate_user_profile(user_id):
    """Clear user profile cache"""
    cache.delete(f"user_profile_{user_id}")


def get_cached_or_set(cache_key, callback, ttl=CACHE_TTL_MEDIUM):
    """
    Get value from cache or set it if not exists.
    """
    cached_value = cache.get(cache_key)
    if cached_value is not None:
        return cached_value

    value = callback()
    cache.set(cache_key, value, ttl)
    return value


def clear_user_caches(user_id):
    """Clear all caches related to a user"""
    try:
        cache.delete_pattern(f"user_profile_{user_id}_*")
        cache.delete_pattern(f"user_notifications_{user_id}_*")
    except AttributeError:
        pass
