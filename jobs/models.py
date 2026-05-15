# jobs/models.py
from django.db import models
from django.conf import settings
from accounts.models import User


class Job(models.Model):
    EMPLOYMENT_TYPES = [
        ("full", "Full-time"),
        ("part", "Part-time"),
        ("contract", "Contract"),
        ("internship", "Internship"),
        ("remote", "Remote"),
    ]

    employer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="jobs"
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    requirements = models.TextField()
    responsibilities = models.TextField(blank=True)
    benefits = models.TextField(blank=True)
    salary_min = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    salary_max = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    location = models.CharField(max_length=200)
    is_remote = models.BooleanField(default=False)
    employment_type = models.CharField(
        max_length=20, choices=EMPLOYMENT_TYPES, default="full"
    )
    experience_level = models.CharField(
        max_length=50,
        choices=[
            ("entry", "Entry Level"),
            ("mid", "Mid Level"),
            ("senior", "Senior Level"),
            ("lead", "Lead"),
            ("executive", "Executive"),
        ],
        default="mid",
    )
    skills_required = models.JSONField(default=list)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    views_count = models.IntegerField(default=0)
    applications_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["employer", "is_active"]),
            models.Index(fields=["location", "is_remote"]),
            models.Index(fields=["title"]),
            models.Index(fields=["salary_min", "salary_max"]),
        ]

    def __str__(self):
        return f"{self.title} at {self.employer.company or self.employer.username}"


class Application(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending Review"),
        ("reviewed", "Reviewed"),
        ("interview", "Interview Scheduled"),
        ("rejected", "Rejected"),
        ("hired", "Hired"),
    ]

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    candidate = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="applications"
    )
    resume = models.FileField(upload_to="resumes/")
    cover_letter = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    employer_notes = models.TextField(blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Fields for parsed resume data
    parsed_email = models.EmailField(blank=True, null=True)
    parsed_phone = models.CharField(max_length=20, blank=True, null=True)
    extracted_skills = models.JSONField(default=list)

    class Meta:
        unique_together = ("job", "candidate")
        ordering = ["-applied_at"]

    def __str__(self):
        return f"{self.candidate.username} - {self.job.title}"


class SavedJob(models.Model):
    candidate = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_jobs"
    )
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="saved_by")
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("candidate", "job")

    def __str__(self):
        return f"{self.candidate.username} saved {self.job.title}"


class JobAlert(models.Model):
    candidate = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="job_alerts"
    )
    search_keyword = models.CharField(max_length=200, blank=True)
    location = models.CharField(max_length=200, blank=True)
    is_remote = models.BooleanField(default=False)
    employment_type = models.CharField(max_length=20, blank=True)
    salary_min = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    frequency = models.CharField(
        max_length=20,
        choices=[("daily", "Daily"), ("weekly", "Weekly")],
        default="weekly",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_sent_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Alert for {self.candidate.username}"


class StatusHistory(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.application} -> {self.status} at {self.changed_at}"
