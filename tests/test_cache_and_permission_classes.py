import pytest
from unittest.mock import Mock, patch
from django.core.cache import cache
from rest_framework.response import Response

from config.cache import (
    cache_response,
    invalidate_job_cache,
    invalidate_job_list_cache,
    invalidate_job_detail_cache,
    invalidate_company_rating,
    invalidate_user_profile,
    get_cached_or_set,
    clear_user_caches,
)
from config.permissions import (
    IsEmployerOrReadOnly,
    IsCandidate,
    IsEmployer,
    IsAdmin,
    IsOwnerOrReadOnly,
    IsJobOwnerOrAdmin,
    IsApplicationOwnerOrEmployer,
    IsApplicationEmployer,
)


class FakeView:
    """Minimal stand-in so cache_response's decorated method has a 'self'"""

    @cache_response("test_prefix")
    def get(self, request, *args, **kwargs):
        return Response({"hello": "world"}, status=200)

    @cache_response("test_prefix")
    def get_error(self, request, *args, **kwargs):
        return Response({"error": "nope"}, status=400)


@pytest.mark.django_db
class TestCacheResponseDecorator:
    def setup_method(self):
        cache.clear()

    def test_non_get_request_bypasses_cache(self):
        view = FakeView()
        request = Mock(method="POST")
        response = view.get(request)
        assert response.status_code == 200

    def test_get_request_caches_response(self):
        view = FakeView()
        request = Mock(method="GET")
        request.get_full_path.return_value = "/api/test/"

        first = view.get(request)
        assert first.status_code == 200

        second = view.get(request)
        assert second.status_code == 200
        assert second.data == {"hello": "world"}

    def test_non_200_response_not_cached(self):
        view = FakeView()
        request = Mock(method="GET")
        request.get_full_path.return_value = "/api/test-error/"

        response = view.get_error(request)
        assert response.status_code == 400


@pytest.mark.django_db
class TestCacheInvalidationHelpers:
    def setup_method(self):
        cache.clear()

    def test_invalidate_job_cache_runs_without_error(self):
        invalidate_job_cache()  # should not raise, regardless of backend

    def test_invalidate_job_list_cache_runs_without_error(self):
        invalidate_job_list_cache()

    def test_invalidate_job_detail_cache(self):
        cache.set("job_detail_5", {"id": 5})
        invalidate_job_detail_cache(5)
        assert cache.get("job_detail_5") is None

    def test_invalidate_company_rating(self):
        cache.set("company_rating_2", 4.5)
        invalidate_company_rating(2)
        assert cache.get("company_rating_2") is None

    def test_invalidate_user_profile(self):
        cache.set("user_profile_9", {"name": "test"})
        invalidate_user_profile(9)
        assert cache.get("user_profile_9") is None

    def test_clear_user_caches_runs_without_error(self):
        clear_user_caches(3)


@pytest.mark.django_db
class TestGetCachedOrSet:
    def setup_method(self):
        cache.clear()

    def test_returns_cached_value_if_present(self):
        cache.set("mykey", "cached_value")
        result = get_cached_or_set("mykey", lambda: "fresh_value")
        assert result == "cached_value"

    def test_calls_callback_and_sets_cache_if_missing(self):
        result = get_cached_or_set("missingkey", lambda: "computed_value")
        assert result == "computed_value"
        assert cache.get("missingkey") == "computed_value"


def make_request(role=None, authenticated=True, is_superuser=False, is_staff=False, method="GET"):
    user = Mock(
        is_authenticated=authenticated,
        role=role,
        is_superuser=is_superuser,
        is_staff=is_staff,
    )
    request = Mock(user=user, method=method)
    return request


class TestPermissions:
    def test_is_employer_or_readonly_allows_safe_methods(self):
        request = make_request(role="candidate", method="GET")
        assert IsEmployerOrReadOnly().has_permission(request, None) is True

    def test_is_employer_or_readonly_blocks_non_employer_write(self):
        request = make_request(role="candidate", method="POST")
        assert IsEmployerOrReadOnly().has_permission(request, None) is False

    def test_is_employer_or_readonly_allows_employer_write(self):
        request = make_request(role="employer", method="POST")
        assert IsEmployerOrReadOnly().has_permission(request, None) is True

    def test_is_candidate_true_for_candidate(self):
        request = make_request(role="candidate")
        assert IsCandidate().has_permission(request, None) is True

    def test_is_candidate_false_for_employer(self):
        request = make_request(role="employer")
        assert IsCandidate().has_permission(request, None) is False

    def test_is_employer_true_for_employer(self):
        request = make_request(role="employer")
        assert IsEmployer().has_permission(request, None) is True

    def test_is_admin_true_for_admin_role(self):
        request = make_request(role="admin")
        assert IsAdmin().has_permission(request, None) is True

    def test_is_admin_true_for_superuser(self):
        request = make_request(role="candidate", is_superuser=True)
        assert IsAdmin().has_permission(request, None) is True

    def test_is_admin_false_for_regular_candidate(self):
        request = make_request(role="candidate")
        assert IsAdmin().has_permission(request, None) is False

    def test_is_owner_or_readonly_allows_safe_methods(self):
        request = make_request(method="GET")
        obj = Mock()
        assert IsOwnerOrReadOnly().has_object_permission(request, None, obj) is True

    def test_is_owner_or_readonly_allows_owner_write(self):
        request = make_request(method="POST")
        obj = Mock(employer=request.user)
        assert IsOwnerOrReadOnly().has_object_permission(request, None, obj) is True

    def test_is_owner_or_readonly_blocks_non_owner_write(self):
        request = make_request(method="POST")
        obj = Mock(employer=Mock())
        assert IsOwnerOrReadOnly().has_object_permission(request, None, obj) is False

    def test_is_job_owner_or_admin_allows_safe_methods(self):
        request = make_request(method="GET")
        obj = Mock()
        assert IsJobOwnerOrAdmin().has_object_permission(request, None, obj) is True

    def test_is_job_owner_or_admin_allows_superuser(self):
        request = make_request(method="DELETE", is_superuser=True)
        obj = Mock(employer=Mock())
        assert IsJobOwnerOrAdmin().has_object_permission(request, None, obj) is True

    def test_is_job_owner_or_admin_allows_owner(self):
        request = make_request(method="DELETE", role="employer")
        obj = Mock(employer=request.user)
        assert IsJobOwnerOrAdmin().has_object_permission(request, None, obj) is True

    def test_is_job_owner_or_admin_blocks_non_owner(self):
        request = make_request(method="DELETE", role="employer")
        obj = Mock(employer=Mock())
        assert IsJobOwnerOrAdmin().has_object_permission(request, None, obj) is False

    def test_is_application_owner_or_employer_candidate_owns(self):
        request = make_request(role="candidate")
        obj = Mock(candidate=request.user)
        assert IsApplicationOwnerOrEmployer().has_object_permission(request, None, obj) is True

    def test_is_application_owner_or_employer_employer_owns_job(self):
        request = make_request(role="employer")
        obj = Mock(job=Mock(employer=request.user))
        assert IsApplicationOwnerOrEmployer().has_object_permission(request, None, obj) is True

    def test_is_application_owner_or_employer_denies_other_role(self):
        request = make_request(role="admin")
        obj = Mock()
        assert IsApplicationOwnerOrEmployer().has_object_permission(request, None, obj) is False

    def test_is_application_employer_matches_job_employer(self):
        request = make_request(role="employer")
        obj = Mock(job=Mock(employer=request.user))
        assert IsApplicationEmployer().has_object_permission(request, None, obj) is True