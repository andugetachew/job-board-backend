from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import timedelta


@shared_task
def send_application_confirmation(application_id):
    from .models import Application

    try:
        app = Application.objects.get(id=application_id)
        subject = f"Application Received: {app.job.title}"
        message = f"""
        Hello {app.candidate.username},
        
        You have successfully applied for {app.job.title} at {app.job.employer.company}.
        
        Status: {app.status}
        Applied on: {app.applied_at}
        
        We will notify you when your application is reviewed.
        
        Best regards,
        Job Board Team
        """
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [app.candidate.email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Email error: {e}")


@shared_task
def send_status_update_email(application_id, old_status, new_status):
    from .models import Application

    try:
        app = Application.objects.get(id=application_id)
        subject = f"Application Status Update: {app.job.title}"
        message = f"""
        Hello {app.candidate.username},
        
        Your application for {app.job.title} has been updated.
        
        Status changed from: {old_status}
        Status changed to: {new_status}
        
        Login to your account for more details.
        
        Best regards,
        Job Board Team
        """
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [app.candidate.email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Email error: {e}")


@shared_task
def send_job_alert_email(candidate_email, jobs_list):
    subject = "New Jobs Match Your Profile"
    message = f"""
    Hello,
    
    New jobs matching your profile:
    
    {jobs_list}
    
    Login to apply now!
    
    Best regards,
    Job Board Team
    """
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [candidate_email],
        fail_silently=False,
    )


@shared_task
def send_daily_job_alerts():
    from .models import JobAlert, Job
    from django.utils import timezone
    from datetime import timedelta

    alerts = JobAlert.objects.filter(is_active=True, frequency="daily")

    for alert in alerts:
        # Find matching jobs
        jobs = Job.objects.filter(is_active=True)

        if alert.search_keyword:
            jobs = jobs.filter(title__icontains=alert.search_keyword)
        if alert.location:
            jobs = jobs.filter(location__icontains=alert.location)
        if alert.is_remote:
            jobs = jobs.filter(is_remote=True)
        if alert.employment_type:
            jobs = jobs.filter(employment_type=alert.employment_type)
        if alert.salary_min:
            jobs = jobs.filter(salary_min__gte=alert.salary_min)

        # Only new jobs since last alert
        if alert.last_sent_at:
            jobs = jobs.filter(created_at__gt=alert.last_sent_at)

        if jobs.exists():
            jobs_list = "\n".join(
                [f"- {job.title} at {job.employer.company}" for job in jobs[:10]]
            )
            send_job_alert_email.delay(alert.candidate.email, jobs_list)
            alert.last_sent_at = timezone.now()
            alert.save()


@shared_task
def send_application_reminders():
    """Send reminders for pending applications (5+ days old)"""
    from .models import Application

    pending_apps = Application.objects.filter(
        status="pending", applied_at__lte=timezone.now() - timedelta(days=5)
    )

    for app in pending_apps:
        send_mail(
            "Application Still Pending",
            f"Your application for {app.job.title} is still under review.",
            settings.DEFAULT_FROM_EMAIL,
            [app.candidate.email],
            fail_silently=False,
        )

    return {"reminders_sent": pending_apps.count()}
@shared_task
def parse_resume_task(application_id):
    from .models import Application
    from .resume_parser import parse_resume

    try:
        app = Application.objects.get(id=application_id)
        if app.resume:
            app.resume.open()
            resume_data = parse_resume(app.resume)
            app.resume.close()

            app.parsed_email = resume_data.get("email")
            app.parsed_phone = resume_data.get("phone")
            app.extracted_skills = resume_data.get("skills", [])
            app.save()
    except Exception as e:
        print(f"Resume parsing error: {e}")