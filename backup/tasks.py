from celery import shared_task
from django.core.management import call_command


@shared_task
def automated_database_backup():
    """Automated database backup task for Celery Beat"""
    call_command("backup_db")
    return {"status": "Backup completed"}
