from rest_framework import serializers
from .models import CompanyReview


class CompanyReviewSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.CharField(source="reviewer.username", read_only=True)

    class Meta:
        model = CompanyReview
        fields = ["id", "rating", "comment", "reviewer_name", "created_at"]
        read_only_fields = ["reviewer_name", "created_at"]
