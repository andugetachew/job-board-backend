from django_filters import rest_framework as filters
from .models import Job


class JobFilter(filters.FilterSet):
    salary_min_gte = filters.NumberFilter(field_name="salary_min", lookup_expr="gte")
    salary_max_lte = filters.NumberFilter(field_name="salary_max", lookup_expr="lte")
    location = filters.CharFilter(lookup_expr="icontains")
    title = filters.CharFilter(lookup_expr="icontains")
    skills_required_contains = filters.CharFilter(
        field_name="skills_required", lookup_expr="contains"
    )
    salary_range = filters.RangeFilter(
        field_name="salary_min", method="filter_salary_range"
    )

    def filter_salary_range(self, queryset, name, value):
        if value.start and value.stop:
            return queryset.filter(
                salary_min__gte=value.start, salary_max__lte=value.stop
            )
        return queryset

    class Meta:
        model = Job
        fields = {
            "employment_type": ["exact"],
            "experience_level": ["exact"],
            "is_remote": ["exact"],
            "is_active": ["exact"],
        }
