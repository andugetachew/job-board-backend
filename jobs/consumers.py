import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Application, Job


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope["url_route"]["kwargs"]["user_id"]
        self.room_group_name = f"user_{self.user_id}"

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        """Handle incoming messages (if needed)"""
        pass

    async def application_status_update(self, event):
        """Send status update notification"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "application_status_update",
                    "application_id": event["application_id"],
                    "job_title": event["job_title"],
                    "old_status": event["old_status"],
                    "new_status": event["new_status"],
                    "message": event["message"],
                    "timestamp": event["timestamp"],
                }
            )
        )

    async def new_job_posted(self, event):
        """Send new job notification"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "new_job_posted",
                    "job_id": event["job_id"],
                    "job_title": event["job_title"],
                    "company": event["company"],
                    "message": event["message"],
                }
            )
        )
