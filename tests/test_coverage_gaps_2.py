import pytest
from rest_framework import status


class TestEmailPreferencesView:
    """Covers EmailPreferencesView.get / post"""

    @pytest.mark.django_db
    def test_get_returns_default_preferences(self, auth_client):
        response = auth_client.get("/api/jobs/email-preferences/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["receive_email_notifications"] is True
        assert response.data["receive_marketing_emails"] is False
        assert response.data["receive_alert_emails"] is True

    @pytest.mark.django_db
    def test_post_updates_persistable_preference(self, auth_client, test_candidate):
        response = auth_client.post(
            "/api/jobs/email-preferences/",
            {
                "receive_email_notifications": False,
                "receive_marketing_emails": True,
                "receive_alert_emails": False,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        test_candidate.refresh_from_db()
        # Only receive_email_notifications is a real model field;
        # receive_marketing_emails / receive_alert_emails are not persisted.
        assert test_candidate.receive_email_notifications is False

    @pytest.mark.django_db
    def test_post_does_not_persist_non_model_fields_to_db(
        self, auth_client, test_candidate
    ):
        """
        receive_marketing_emails / receive_alert_emails are not real fields
        on User (confirmed against accounts/models.py). Querying the DB
        directly - bypassing the test client and any in-memory user object -
        proves whether the POST actually persisted anything for these keys.
        """
        from django.contrib.auth import get_user_model

        User = get_user_model()

        auth_client.post(
            "/api/jobs/email-preferences/",
            {"receive_marketing_emails": True, "receive_alert_emails": False},
            format="json",
        )

        # Fresh query straight from the DB, independent of any cached
        # in-memory object the test client may be holding onto.
        from_db = User.objects.get(id=test_candidate.id)
        assert not hasattr(from_db, "receive_marketing_emails")

    @pytest.mark.django_db
    def test_unauthenticated_cannot_access_preferences(self, api_client):
        response = api_client.get("/api/jobs/email-preferences/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestRestoreJobView:
    """Covers RestoreJobView"""

    @pytest.mark.django_db
    def test_admin_can_restore_soft_deleted_job(self, admin_auth_client, test_job):
        test_job.soft_delete()
        response = admin_auth_client.post(f"/api/jobs/admin/jobs/{test_job.id}/restore/")
        assert response.status_code == status.HTTP_200_OK
        test_job.refresh_from_db()
        assert test_job.is_deleted is False
        assert test_job.is_active is True

    @pytest.mark.django_db
    def test_restore_nonexistent_deleted_job_returns_404(self, admin_auth_client, test_job):
        # test_job is not deleted, so it shouldn't match is_deleted=True
        response = admin_auth_client.post(f"/api/jobs/admin/jobs/{test_job.id}/restore/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.django_db
    def test_non_admin_cannot_restore_job(self, employer_auth_client, test_job):
        test_job.soft_delete()
        response = employer_auth_client.post(
            f"/api/jobs/admin/jobs/{test_job.id}/restore/"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestWithdrawApplicationView:
    """Covers WithdrawApplicationView, including the blocked-status branch"""

    @pytest.mark.django_db
    def test_candidate_can_withdraw_pending_application(
        self, auth_client, test_application
    ):
        response = auth_client.delete(
            f"/api/jobs/applications/{test_application.id}/withdraw/"
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

    @pytest.mark.django_db
    def test_cannot_withdraw_after_interview_status(
        self, auth_client, test_application
    ):
        test_application.status = "interview"
        test_application.save()
        response = auth_client.delete(
            f"/api/jobs/applications/{test_application.id}/withdraw/"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_cannot_withdraw_after_hired_status(self, auth_client, test_application):
        test_application.status = "hired"
        test_application.save()
        response = auth_client.delete(
            f"/api/jobs/applications/{test_application.id}/withdraw/"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_withdraw_nonexistent_application_returns_404(self, auth_client):
        response = auth_client.delete("/api/jobs/applications/99999/withdraw/")
        assert response.status_code == status.HTTP_404_NOT_FOUND