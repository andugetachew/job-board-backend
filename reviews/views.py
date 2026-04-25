from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Avg, Count
from .models import CompanyReview
from .serializers import CompanyReviewSerializer
from accounts.models import User


class CompanyReviewListCreateView(generics.ListCreateAPIView):
    serializer_class = CompanyReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        company_id = self.kwargs["company_id"]
        return CompanyReview.objects.filter(company_id=company_id, is_verified=True)

    def perform_create(self, serializer):
        company_id = self.kwargs["company_id"]
        company = User.objects.get(id=company_id, role="employer")
        serializer.save(reviewer=self.request.user, company=company)


class CompanyRatingSummaryView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, company_id):
        reviews = CompanyReview.objects.filter(company_id=company_id, is_verified=True)

        if not reviews.exists():
            return Response(
                {
                    "average_rating": 0,
                    "total_reviews": 0,
                    "rating_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
                }
            )

        average = reviews.aggregate(Avg("rating"))["rating__avg"]
        distribution = reviews.values("rating").annotate(count=Count("rating"))
        dist_dict = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for d in distribution:
            dist_dict[d["rating"]] = d["count"]

        return Response(
            {
                "average_rating": round(average, 1),
                "total_reviews": reviews.count(),
                "rating_distribution": dist_dict,
            }
        )
