import pytest
import json
from unittest.mock import AsyncMock, MagicMock

from jobs.consumers import NotificationConsumer


@pytest.mark.asyncio
class TestNotificationConsumer:

    @pytest.fixture
    def consumer(self):
        consumer = NotificationConsumer()
        consumer.scope = {"url_route": {"kwargs": {"user_id": "1"}}}
        consumer.channel_layer = MagicMock()
        consumer.channel_name = "test_channel"
        consumer.channel_layer.group_add = AsyncMock()
        consumer.channel_layer.group_discard = AsyncMock()
        return consumer

    async def test_connect(self, consumer):
        consumer.accept = AsyncMock()

        await consumer.connect()

        consumer.channel_layer.group_add.assert_called_once_with(
            "user_1", "test_channel"
        )
        assert consumer.room_group_name == "user_1"
        consumer.accept.assert_called_once()

    async def test_disconnect(self, consumer):
        # room_group_name is set by connect — set it directly for isolation
        consumer.room_group_name = "user_1"

        await consumer.disconnect(1000)

        consumer.channel_layer.group_discard.assert_called_once_with(
            "user_1", "test_channel"
        )

    async def test_application_status_update(self, consumer):
        consumer.send = AsyncMock()

        event = {
            "application_id": 1,
            "job_title": "Dev",
            "old_status": "pending",
            "new_status": "reviewed",
            "message": "test message",
            "timestamp": "now",
        }

        await consumer.application_status_update(event)

        consumer.send.assert_called_once()
        sent = json.loads(consumer.send.call_args[1]["text_data"])
        assert sent["type"] == "application_status_update"
        assert sent["new_status"] == "reviewed"

    async def test_new_job_posted(self, consumer):
        consumer.send = AsyncMock()

        event = {
            "job_id": 1,
            "job_title": "Dev",
            "company": "TestCorp",
            "message": "new job",
        }

        await consumer.new_job_posted(event)

        consumer.send.assert_called_once()
        sent = json.loads(consumer.send.call_args[1]["text_data"])
        assert sent["type"] == "new_job_posted"
        assert sent["company"] == "TestCorp"