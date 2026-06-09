
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone


def send_status_update_notification(
    user_id, application_id, job_title, old_status, new_status
):
    try:
        channel_layer = get_channel_layer()

        channel_layer.group_send(
            f"user_{user_id}",
            {
                "type": "application_status_update",
                "application_id": application_id,
                "job_title": job_title,
                "old_status": old_status,
                "new_status": new_status,
                "message": f"{job_title} changed from {old_status} to {new_status}",
                "timestamp": timezone.now().isoformat(),
            },
        )
    except Exception:
        pass

    return True


def send_new_job_notification(user_ids, job_id, job_title, company):
    try:
        channel_layer = get_channel_layer()

        for user_id in user_ids:
            channel_layer.group_send(
                f"user_{user_id}",
                {
                    "type": "new_job_posted",
                    "job_id": job_id,
                    "job_title": job_title,
                    "company": company,
                    "message": f"New job: {job_title} at {company}",
                },
            )
    except Exception:
        pass

    return True