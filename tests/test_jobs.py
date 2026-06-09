import pytest
from unittest.mock import patch
from django.utils import timezone
from datetime import timedelta

from jobs.tasks import (
    send_application_confirmation,
    send_status_update_email,
    send_job_alert_email,
    send_daily_job_alerts,
    send_application_reminders,
)
from jobs.models import Application, JobAlert


@pytest.mark.django_db
class TestJobTasks:

    @patch("jobs.tasks.send_mail")
    def test_send_application_confirmation(self, mock_send, test_application):
        send_application_confirmation(test_application.id)

        mock_send.assert_called_once()

    @patch("jobs.tasks.send_mail")
    def test_send_application_confirmation_invalid_id(self, mock_send):
        send_application_confirmation(999999)

        mock_send.assert_not_called()

    @patch("jobs.tasks.send_mail")
    def test_send_status_update_email(
        self,
        mock_send,
        test_application
    ):
        send_status_update_email(
            test_application.id,
            "pending",
            "reviewed",
        )

        mock_send.assert_called_once()

    @patch("jobs.tasks.send_mail")
    def test_send_job_alert_email(self, mock_send):
        send_job_alert_email(
            "candidate@test.com",
            "Python Developer"
        )

        mock_send.assert_called_once()

    @patch("jobs.tasks.send_job_alert_email.delay")
    def test_send_daily_job_alerts_sends_email(
        self,
        mock_delay,
        test_candidate,
        test_job
    ):
        JobAlert.objects.create(
            candidate=test_candidate,
            search_keyword="Python",
            location="Remote",
            frequency="daily",
            is_active=True,
        )

        send_daily_job_alerts()

        mock_delay.assert_called_once()

    @patch("jobs.tasks.send_job_alert_email.delay")
    def test_send_daily_job_alerts_no_matches(
        self,
        mock_delay,
        test_candidate
    ):
        JobAlert.objects.create(
            candidate=test_candidate,
            search_keyword="Java",
            frequency="daily",
            is_active=True,
        )

        send_daily_job_alerts()

        mock_delay.assert_not_called()

    @patch("jobs.tasks.send_mail")
    def test_send_application_reminders(
        self,
        mock_send,
        test_application
    ):
        Application.objects.filter(
            id=test_application.id
        ).update(
            applied_at=timezone.now() - timedelta(days=6)
        )

        result = send_application_reminders()

        assert result["reminders_sent"] == 1
        assert mock_send.called