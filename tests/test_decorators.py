import pytest
from django.core.cache import cache
from rest_framework.test import APIRequestFactory
from rest_framework.response import Response
from jobs.decorators import cache_for_jobs, invalidate_job_cache


@pytest.mark.django_db
class TestCacheForJobsDecorator:

    def setup_method(self):
        cache.clear()

    def test_cache_for_jobs_caches_get_requests(self):
        factory = APIRequestFactory()
        request = factory.get("/api/jobs/?page=1")

        call_count = 0

        @cache_for_jobs(timeout=60)
        def dummy_view(self, request):
            nonlocal call_count
            call_count += 1
            return Response({"jobs": []})

        response1 = dummy_view(None, request)
        response2 = dummy_view(None, request)

        assert call_count == 1
        assert response1.data == response2.data

    def test_cache_for_jobs_skips_post_requests(self):
        factory = APIRequestFactory()
        request = factory.post("/api/jobs/")

        call_count = 0

        @cache_for_jobs(timeout=60)
        def dummy_view(self, request):
            nonlocal call_count
            call_count += 1
            return Response({"message": "Created"}, status=201)

        dummy_view(None, request)
        dummy_view(None, request)

        assert call_count == 2

    def test_cache_for_jobs_skips_non_200_responses(self):
        factory = APIRequestFactory()
        request = factory.get("/api/jobs/error/")

        call_count = 0

        @cache_for_jobs(timeout=60)
        def dummy_view(self, request):
            nonlocal call_count
            call_count += 1
            return Response({"error": "Bad request"}, status=400)

        dummy_view(None, request)
        dummy_view(None, request)

        assert call_count == 2

    def test_cache_for_jobs_different_urls_have_different_cache(self):
        factory = APIRequestFactory()

        request1 = factory.get("/api/jobs/?page=1")
        request2 = factory.get("/api/jobs/?page=2")

        call_count = 0

        @cache_for_jobs(timeout=60)
        def dummy_view(self, request):
            nonlocal call_count
            call_count += 1
            return Response({"page": request.GET.get("page")})

        dummy_view(None, request1)
        dummy_view(None, request2)
        dummy_view(None, request1)
        dummy_view(None, request2)

        assert call_count == 2


@pytest.mark.django_db
class TestInvalidateJobCache:

    def setup_method(self):
        cache.clear()

    def test_invalidate_job_cache_clears_cached_jobs(self):
        factory = APIRequestFactory()
        request = factory.get("/api/jobs/")

        call_count = 0

        @cache_for_jobs(timeout=60)
        def dummy_view(self, request):
            nonlocal call_count
            call_count += 1
            return Response({"jobs": []})

        dummy_view(None, request)
        dummy_view(None, request)

        assert call_count == 1

        invalidate_job_cache()

        dummy_view(None, request)

        assert call_count == 2