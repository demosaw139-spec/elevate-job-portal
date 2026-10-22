from rest_framework import serializers, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated

from .models import Application, Job, User


class JobSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)

    class Meta:
        model = Job
        fields = (
            "id",
            "title",
            "summary",
            "description",
            "company_name",
            "location",
            "employment_type",
            "work_mode",
            "salary_min",
            "salary_max",
            "created_at",
        )


class ApplicationSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source="job.title", read_only=True)

    class Meta:
        model = Application
        fields = ("id", "job", "job_title", "cover_letter", "status", "created_at")
        read_only_fields = ("status", "created_at")

    def validate_job(self, job):
        if job.status != Job.Status.PUBLISHED:
            raise serializers.ValidationError("This role is not accepting applications.")
        if self.context["request"].user.role != User.Role.CANDIDATE:
            raise serializers.ValidationError("Only candidates can apply.")
        if Application.objects.filter(job=job, candidate=self.context["request"].user).exists():
            raise serializers.ValidationError("You have already applied to this role.")
        return job

    def create(self, validated_data):
        return Application.objects.create(
            candidate=self.context["request"].user, **validated_data
        )


class JobViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = JobSerializer
    permission_classes = (AllowAny,)

    def get_queryset(self):
        jobs = Job.objects.filter(status=Job.Status.PUBLISHED).select_related("company")
        query = self.request.query_params.get("q", "").strip()
        location = self.request.query_params.get("location", "").strip()
        work_mode = self.request.query_params.get("work_mode", "").strip()
        if query:
            jobs = jobs.filter(title__icontains=query) | jobs.filter(
                company__name__icontains=query
            )
        if location:
            jobs = jobs.filter(location__icontains=location)
        if work_mode in Job.WorkMode.values:
            jobs = jobs.filter(work_mode=work_mode)
        return jobs.order_by("-created_at")


class ApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ("get", "post", "head", "options")

    def get_queryset(self):
        return Application.objects.filter(candidate=self.request.user).select_related("job")
