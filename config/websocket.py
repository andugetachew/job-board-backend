from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone


def send_status_update_notification(
    user_id, application_id, job_title, old_status, new_status
):
    """Send real-time WebSocket notification for status update"""
    try:
        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            f"user_{user_id}",
            {
                "type": "application_status_update",
                "application_id": application_id,
                "job_title": job_title,
                "old_status": old_status,
                "new_status": new_status,
                "message": f"Your application for {job_title} status changed from {old_status} to {new_status}",
                "timestamp": timezone.now().isoformat(),
            },
        )
    except Exception as e:
        print(f"WebSocket notification error: {e}")


def send_new_job_notification(user_ids, job_id, job_title, company):
    """Send real-time WebSocket notification for new job posting"""
    try:
        channel_layer = get_channel_layer()

        for user_id in user_ids:
            async_to_sync(channel_layer.group_send)(
                f"user_{user_id}",
                {
                    "type": "new_job_posted",
                    "job_id": job_id,
                    "job_title": job_title,
                    "company": company,
                    "message": f"New job posted: {job_title} at {company}",
                },
            )
    except Exception as e:
        print(f"WebSocket notification error: {e}")
