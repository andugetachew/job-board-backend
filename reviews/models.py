from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class CompanyReview(models.Model):
    company = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews"
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="my_reviews"
    )
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField()
    is_verified = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("company", "reviewer")

    def __str__(self):
        return f"{self.reviewer.username} rated {self.company.username}: {self.rating}★"
