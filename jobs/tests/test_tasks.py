from django.core.mail import send_mail
from django.conf import settings
from jobs.models import Application
import logging

logger = logging.getLogger(__name__)


def send_application_confirmation(application_id):
    try:
        application = Application.objects.select_related("candidate", "job").get(
            id=application_id
        )
    except Application.DoesNotExist:
        logger.warning("Application %s does not exist", application_id)
        return

    subject = "Application Received"
    message = f"""
Hi {application.candidate.username},

Your application for "{application.job.title}" has been received successfully.

We will review your application and update you soon.

Thanks,
Job Board Team
"""

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [application.candidate.email],
        fail_silently=False,
    )


def send_status_update_email(application_id, old_status, new_status):
    try:
        application = Application.objects.select_related("candidate", "job").get(
            id=application_id
        )
    except Application.DoesNotExist:
        logger.warning("Application %s does not exist", application_id)
        return

    subject = "Status Update"
    message = f"""
Hi {application.candidate.username},

Your application for "{application.job.title}" has been updated.

Previous status: {old_status}
New status: {new_status}

Thanks,
Job Board Team
"""

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [application.candidate.email],
        fail_silently=False,
    )
