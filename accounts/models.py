from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ("candidate", "Candidate"),
        ("employer", "Employer"),
        ("admin", "Admin"),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="candidate")
    company = models.CharField(max_length=200, blank=True)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    website = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True, null=True)
    receive_email_notifications = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.username} - {self.role}"

    @property
    def is_employer(self):
        return self.role == "employer"

    @property
    def is_candidate(self):
        return self.role == "candidate"


class Company(models.Model):
    employer = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="company_profile"
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to="company_logos/", null=True, blank=True)
    founded_year = models.IntegerField(null=True, blank=True)
    employee_count = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
