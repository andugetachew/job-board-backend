import pytest
from unittest.mock import patch, MagicMock

from jobs.notifications_utils import (
    send_status_update_notification,
    send_new_job_notification,
)


class TestJobNotificationsUtils:

    @patch("jobs.notifications_utils.get_channel_layer")
    @patch("jobs.notifications_utils.async_to_sync")
    def test_send_status_update_notification(self, mock_async, mock_channel_layer):
        mock_group = MagicMock()
        mock_channel_layer.return_value = MagicMock()
        mock_async.return_value = lambda func: func  # bypass async wrapper

        send_status_update_notification(
            user_id=1,
            application_id=10,
            job_title="Python Dev",
            old_status="pending",
            new_status="reviewed",
        )

        # Ensure group_send was called
        channel = mock_channel_layer.return_value
        assert channel.group_send.called

    @patch("jobs.notifications_utils.get_channel_layer")
    @patch("jobs.notifications_utils.async_to_sync")
    def test_send_new_job_notification(self, mock_async, mock_channel_layer):
        mock_channel_layer.return_value = MagicMock()
        mock_async.return_value = lambda func: func

        send_new_job_notification(
            user_ids=[1, 2],
            job_id=99,
            job_title="Backend Dev",
            company="TestCorp",
        )

        channel = mock_channel_layer.return_value
        assert channel.group_send.called

    @patch("jobs.notifications_utils.get_channel_layer")
    def test_notification_error_handling(self, mock_channel_layer):
        mock_channel_layer.side_effect = Exception("fail")

        # should NOT crash
        send_status_update_notification(
            user_id=1,
            application_id=1,
            job_title="Test",
            old_status="a",
            new_status="b",
        )