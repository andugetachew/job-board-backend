import pytest
from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status


class TestEmailNotifications:
    """Email notification and Celery task tests"""

    @pytest.mark.django_db
    def test_verification_email_sent_on_register(self, api_client, mock_celery_tasks):
        response = api_client.post(
            "/api/auth/register/",
            {
                "username": "emailtest",
                "email": "email@test.com",
                "password": "pass123",
                "role": "candidate",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        mock_celery_tasks["verify"].assert_called_once()

    @pytest.mark.django_db
    def test_password_reset_email_sent(
        self, api_client, test_candidate, mock_celery_tasks
    ):
        response = api_client.post(
            "/api/auth/forgot-password/", {"email": "candidate@test.com"}
        )
        assert response.status_code == status.HTTP_200_OK
        mock_celery_tasks["reset"].assert_called_once()

    @pytest.mark.django_db
    def test_email_task_triggered_on_application(
        self, auth_client, test_job, resume_file
    ):
        with patch("jobs.views.send_application_confirmation") as mock_task:
            response = auth_client.post(
                f"/api/jobs/{test_job.id}/apply/",
                {"cover_letter": "I am interested.", "resume": resume_file},
                format="multipart",
            )
            assert response.status_code == 201
            mock_task.assert_called_once()

    @pytest.mark.django_db
    def test_email_task_triggered_on_status_update(
        self, employer_auth_client, test_application
    ):
        with patch("jobs.views.send_status_update_email") as mock_task:
            response = employer_auth_client.patch(
                f"/api/jobs/applications/{test_application.id}/status/",
                {"status": "interview"},
                format="json",
            )
            assert response.status_code == 200
            mock_task.assert_called_once()

    @pytest.mark.django_db
    def test_email_not_sent_on_failed_application(self, auth_client, test_job):
        """No email task should fire if application fails (no resume)"""
        with patch("jobs.views.send_application_confirmation") as mock_task:
            response = auth_client.post(
                f"/api/jobs/{test_job.id}/apply/",
                {"cover_letter": "No resume attached"},
                format="multipart",
            )
            assert response.status_code in [400, 422]
            mock_task.assert_not_called()
