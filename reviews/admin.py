# from django.contrib import admin
# from .models import CompanyReview


# @admin.register(CompanyReview)
# class CompanyReviewAdmin(admin.ModelAdmin):
#     list_display = ["company", "reviewer", "rating", "is_verified", "created_at"]
#     list_filter = ["rating", "is_verified", "created_at"]
#     search_fields = ["company__username", "reviewer__username", "comment"]
#     actions = ["verify_reviews"]

#     def verify_reviews(self, request, queryset):
#         queryset.update(is_verified=True)

#     verify_reviews.short_description = "Mark selected reviews as verified"

from django.contrib import admin
from django.utils.translation import ngettext
from .models import CompanyReview


@admin.register(CompanyReview)
class CompanyReviewAdmin(admin.ModelAdmin):
    list_display = ("company", "reviewer", "rating", "is_verified", "created_at")
    list_filter = ("rating", "is_verified", "created_at")
    search_fields = ("company__username", "reviewer__username", "comment")
    actions = ["mark_as_verified"]

    @admin.action(description="Mark selected reviews as verified")
    def mark_as_verified(self, request, queryset):
        updated = queryset.update(is_verified=True)

        self.message_user(
            request,
            ngettext(
                "%d review was successfully marked as verified.",
                "%d reviews were successfully marked as verified.",
                updated,
            )
            % updated,
        )
