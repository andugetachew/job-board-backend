import os
import subprocess
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = "Backup PostgreSQL database"

    def handle(self, *args, **options):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(settings.BASE_DIR, "backups")

        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        backup_file = os.path.join(backup_dir, f"backup_{timestamp}.sql")

        db = settings.DATABASES["default"]

        cmd = [
            "pg_dump",
            "-h",
            db["HOST"],
            "-p",
            str(db["PORT"]),
            "-U",
            db["USER"],
            "-d",
            db["NAME"],
            "-f",
            backup_file,
        ]

        try:
            subprocess.run(cmd, check=True, env={"PGPASSWORD": db["PASSWORD"]})
            self.stdout.write(self.style.SUCCESS(f"Backup created: {backup_file}"))

            # Clean old backups (keep last 7 days)
            self.clean_old_backups(backup_dir)
        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f"Backup failed: {e}"))

    def clean_old_backups(self, backup_dir, days=7):
        """Delete backups older than specified days"""
        import time

        current_time = time.time()

        for filename in os.listdir(backup_dir):
            filepath = os.path.join(backup_dir, filename)
            if os.path.isfile(filepath):
                file_age = current_time - os.path.getmtime(filepath)
                if file_age > days * 24 * 60 * 60:
                    os.remove(filepath)
                    self.stdout.write(f"Deleted old backup: {filename}")
