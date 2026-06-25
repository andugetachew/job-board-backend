import pytest
from rest_framework import status


class TestJobDetailView:
    """Covers JobDetailView.retrieve / perform_update / perform_destroy"""

    @pytest.mark.django_db
    def test_retrieve_increments_views_and_caches(self, api_client, test_job):
        response = api_client.get(f"/api/jobs/{test_job.id}/")
        assert response.status_code == status.HTTP_200_OK

        test_job.refresh_from_db()
        assert test_job.views_count == 1

        # second hit should come from cache but still succeed
        response_2 = api_client.get(f"/api/jobs/{test_job.id}/")
        assert response_2.status_code == status.HTTP_200_OK

    @pytest.mark.django_db
    def test_employer_can_update_own_job(self, employer_auth_client, test_job):
        response = employer_auth_client.patch(
            f"/api/jobs/{test_job.id}/", {"title": "Senior Python Developer"}
        )
        assert response.status_code == status.HTTP_200_OK
        test_job.refresh_from_db()
        assert test_job.title == "Senior Python Developer"

    @pytest.mark.django_db
    def test_employer_cannot_update_other_employers_job(
        self, api_client, test_employer_2, test_job
    ):
        api_client.force_authenticate(user=test_employer_2)
        response = api_client.patch(
            f"/api/jobs/{test_job.id}/", {"title": "Hijacked Title"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_employer_can_soft_delete_own_job(self, employer_auth_client, test_job):
        response = employer_auth_client.delete(f"/api/jobs/{test_job.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        test_job.refresh_from_db()
        assert test_job.is_deleted is True
        assert test_job.is_active is False

    @pytest.mark.django_db
    def test_admin_can_delete_any_job(self, admin_auth_client, test_job):
        response = admin_auth_client.delete(f"/api/jobs/{test_job.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        test_job.refresh_from_db()
        assert test_job.is_deleted is True

    @pytest.mark.django_db
    def test_other_employer_cannot_delete_job(
        self, api_client, test_employer_2, test_job
    ):
        api_client.force_authenticate(user=test_employer_2)
        response = api_client.delete(f"/api/jobs/{test_job.id}/")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestSavedJobs:
    """Covers SavedJobView and UnsaveJobView"""

    @pytest.mark.django_db
    def test_candidate_can_save_job(self, auth_client, test_job):
        response = auth_client.post("/api/jobs/saved/", {"job_id": test_job.id})
        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.django_db
    def test_candidate_can_list_saved_jobs(self, auth_client, test_saved_job):
        response = auth_client.get("/api/jobs/saved/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

    @pytest.mark.django_db
    def test_candidate_can_unsave_job(self, auth_client, test_saved_job):
        response = auth_client.delete(f"/api/jobs/saved/{test_saved_job.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    @pytest.mark.django_db
    def test_candidate_cannot_unsave_other_candidates_saved_job(
        self, api_client, test_job, test_saved_job
    ):
        other = api_client
        from django.contrib.auth import get_user_model

        User = get_user_model()
        other_candidate = User.objects.create_user(
            username="othercandidate",
            email="other@test.com",
            password="other12345",
            role="candidate",
            is_email_verified=True,
        )
        other.force_authenticate(user=other_candidate)
        response = other.delete(f"/api/jobs/saved/{test_saved_job.id}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestJobAlerts:
    """Covers JobAlertListCreateView and JobAlertDeleteView"""

    @pytest.mark.django_db
    def test_candidate_can_create_job_alert(self, auth_client):
        response = auth_client.post(
            "/api/jobs/alerts/",
            {
                "search_keyword": "Django",
                "location": "Remote",
                "frequency": "weekly",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.django_db
    def test_candidate_can_list_own_alerts(self, auth_client, test_job_alert):
        response = auth_client.get("/api/jobs/alerts/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

    @pytest.mark.django_db
    def test_candidate_can_delete_own_alert(self, auth_client, test_job_alert):
        response = auth_client.delete(f"/api/jobs/alerts/{test_job_alert.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT


class TestCompanyJobsView:
    """Covers CompanyJobsView"""

    @pytest.mark.django_db
    def test_lists_active_jobs_for_employer(self, api_client, test_employer, test_job):
        response = api_client.get(f"/api/jobs/company/{test_employer.id}/jobs/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

    @pytest.mark.django_db
    def test_anonymous_user_can_view_company_jobs(
        self, api_client, test_employer, test_job
    ):
        response = api_client.get(f"/api/jobs/company/{test_employer.id}/jobs/")
        assert response.status_code == status.HTTP_200_OK


class TestApplicantProfileView:
    """Covers ApplicantProfileView"""

    @pytest.mark.django_db
    def test_employer_can_view_profile_of_real_applicant(
        self, employer_auth_client, test_application, test_candidate
    ):
        response = employer_auth_client.get(
            f"/api/jobs/applicant/{test_candidate.id}/"
        )
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.django_db
    def test_employer_cannot_view_profile_of_non_applicant(
        self, employer_auth_client, test_candidate
    ):
        response = employer_auth_client.get(
            f"/api/jobs/applicant/{test_candidate.id}/"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestJobShareView:
    """Covers JobShareView"""

    @pytest.mark.django_db
    def test_returns_share_links(self, api_client, test_job):
        response = api_client.get(f"/api/jobs/{test_job.id}/share/")
        assert response.status_code == status.HTTP_200_OK
        assert "twitter_url" in response.data
        assert "linkedin_url" in response.data
        assert "facebook_url" in response.data

    @pytest.mark.django_db
    def test_uses_custom_frontend_url_if_provided(self, api_client, test_job):
        response = api_client.get(
            f"/api/jobs/{test_job.id}/share/?frontend_url=https://myfrontend.com"
        )
        assert response.status_code == status.HTTP_200_OK
        assert "myfrontend.com" in response.data["url"]


class TestUpdateResumeView:
    """Covers UpdateResumeView"""

    @pytest.mark.django_db
    def test_candidate_can_update_resume_on_latest_application(
        self, auth_client, test_application, resume_file
    ):
        response = auth_client.put(
            "/api/jobs/update-resume/",
            {"resume": resume_file},
            format="multipart",
        )
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.django_db
    def test_returns_404_when_candidate_has_no_application(
        self, auth_client, resume_file
    ):
        response = auth_client.put(
            "/api/jobs/update-resume/",
            {"resume": resume_file},
            format="multipart",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

