from functools import wraps
from django.core.cache import cache
from rest_framework.renderers import JSONRenderer


def cache_for_jobs(timeout=60 * 15):
    """Cache job listings for 15 minutes"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            if request.method != "GET":
                return view_func(self, request, *args, **kwargs)

            cache_key = f"job_list_{request.get_full_path()}"
            cached_response = cache.get(cache_key)
            if cached_response:
                return cached_response

            response = view_func(self, request, *args, **kwargs)

            if response.status_code == 200:
                if not response.is_rendered:
                    response.accepted_renderer = JSONRenderer()
                    response.accepted_media_type = "application/json"
                    response.renderer_context = {}
                    response.render()
                cache.set(cache_key, response, timeout)

            return response
        return wrapper
    return decorator


def invalidate_job_cache():
    """Invalidate all job list caches"""
    from django.core.cache import cache
    cache.delete_pattern("job_list_*")