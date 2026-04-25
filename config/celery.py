import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
# Celery Configuration
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"

# Email Configuration (SendGrid)
SENDGRID_API_KEY = "your-sendgrid-api-key-here"
EMAIL_BACKEND = "sendgrid_backend.SendgridBackend"
SENDGRID_SANDBOX_MODE_IN_DEBUG = False
DEFAULT_FROM_EMAIL = "noreply@jobboard.com"
from celery.schedules import crontab

app.conf.beat_schedule = {
    "send-daily-job-alerts": {
        "task": "jobs.tasks.send_daily_job_alerts",
        "schedule": crontab(hour=9, minute=0),  # 9 AM daily
    },
    "send-weekly-digest": {
        "task": "jobs.tasks.send_weekly_job_digest",
        "schedule": crontab(hour=9, minute=0, day_of_week="monday"),  # Monday 9 AM
    },
}
