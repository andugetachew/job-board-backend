
from django.urls import path
from .views import CompanyReviewListCreateView, CompanyRatingSummaryView

urlpatterns = [
    path(
        "companies/<int:company_id>/reviews/",
        CompanyReviewListCreateView.as_view(),
        name="company-reviews",
    ),
    path(
        "companies/<int:company_id>/reviews/summary/",
        CompanyRatingSummaryView.as_view(),
        name="company-rating-summary",
    ),
]
