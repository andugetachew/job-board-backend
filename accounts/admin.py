from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
        "role",
        "company",
        "is_active",
        "is_email_verified",
    )
    list_filter = ("role", "is_active", "is_email_verified")
    search_fields = ("username", "email", "company")
    fieldsets = UserAdmin.fieldsets + (
        (
            "Additional Info",
            {
                "fields": (
                    "role",
                    "company",
                    "phone",
                    "bio",
                    "location",
                    "website",
                    "is_email_verified",
                )
            },
        ),
    )
