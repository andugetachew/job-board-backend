from rest_framework import serializers
from .models import Job, Application, SavedJob, JobAlert


class JobSerializer(serializers.ModelSerializer):
    employer_name = serializers.CharField(source="employer.company", read_only=True)
    employer_id = serializers.IntegerField(source="employer.id", read_only=True)

    class Meta:
        model = Job
        fields = "__all__"
        read_only_fields = (
            "employer",
            "views_count",
            "applications_count",
            "created_at",
        )


class ApplicationSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source="job.title", read_only=True)
    candidate_name = serializers.CharField(source="candidate.username", read_only=True)
    candidate_email = serializers.EmailField(source="candidate.email", read_only=True)

    # CRITICAL: Override foreign keys to be read-only AND not required
    job = serializers.PrimaryKeyRelatedField(read_only=True)
    candidate = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Application
        fields = "__all__"
        read_only_fields = ("candidate", "job", "applied_at", "updated_at")

    def validate_resume(self, value):
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Resume file too large. Max 5MB.")
        ext = value.name.split(".")[-1].lower()
        if ext not in ["pdf", "doc", "docx", "txt"]:
            raise serializers.ValidationError(
                "Invalid file type. Allowed: PDF, DOC, DOCX, TXT"
            )
        return value


class SavedJobSerializer(serializers.ModelSerializer):
    job = JobSerializer(read_only=True)

    class Meta:
        model = SavedJob
        fields = ("id", "job", "saved_at")


class JobAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobAlert
        fields = "__all__"
        read_only_fields = ("candidate", "created_at", "last_sent_at")
