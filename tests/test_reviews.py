import pytest
from reviews.models import CompanyReview


@pytest.mark.django_db
class TestReviewsAPI:

    def test_list_company_reviews(
        self,
        api_client,
        test_review,
        test_employer,
    ):
        test_review.is_verified = True
        test_review.save()

        response = api_client.get(
            f"/companies/{test_employer.id}/reviews/"
        )

        assert response.status_code == 200
        assert len(response.data) == 1

    def test_company_review_summary_no_reviews(
        self,
        api_client,
        test_employer,
    ):
        response = api_client.get(
            f"/companies/{test_employer.id}/reviews/summary/"
        )

        assert response.status_code == 200
        assert response.data["average_rating"] == 0
        assert response.data["total_reviews"] == 0

    def test_company_review_summary_with_reviews(
        self,
        api_client,
        test_review,
        test_employer,
    ):
        test_review.is_verified = True
        test_review.save()

        response = api_client.get(
            f"/companies/{test_employer.id}/reviews/summary/"
        )

        assert response.status_code == 200
        assert response.data["average_rating"] == 4.0
        assert response.data["total_reviews"] == 1
        assert response.data["rating_distribution"][4] == 1

    def test_create_review_authenticated(
        self,
        auth_client,
        test_employer,
    ):
        response = auth_client.post(
            f"/companies/{test_employer.id}/reviews/",
            {
                "rating": 5,
                "comment": "Excellent company"
            },
            format="json",
        )

        assert response.status_code == 201

    def test_create_review_unauthenticated(
        self,
        api_client,
        test_employer,
    ):
        response = api_client.post(
            f"/companies/{test_employer.id}/reviews/",
            {
                "rating": 5,
                "comment": "Excellent company"
            },
            format="json",
        )

        assert response.status_code in [401, 403]

    def test_only_verified_reviews_are_returned(
        self,
        api_client,
        test_candidate,
        test_employer,
    ):
        CompanyReview.objects.create(
            reviewer=test_candidate,
            company=test_employer,
            rating=5,
            comment="Hidden review",
            is_verified=False,
        )

        response = api_client.get(
            f"/companies/{test_employer.id}/reviews/"
        )

        assert response.status_code == 200
        assert len(response.data) == 0

    def test_rating_distribution_multiple_reviews(
        self,
        api_client,
        test_candidate,
        test_employer,
    ):
        CompanyReview.objects.create(
            reviewer=test_candidate,
            company=test_employer,
            rating=5,
            comment="Great",
            is_verified=True,
        )

        second_user = type(test_candidate).objects.create_user(
            username="candidate2",
            email="candidate2@test.com",
            password="password123",
            role="candidate",
        )

        CompanyReview.objects.create(
            reviewer=second_user,
            company=test_employer,
            rating=3,
            comment="Average",
            is_verified=True,
        )

        response = api_client.get(
            f"/companies/{test_employer.id}/reviews/summary/"
        )

        assert response.status_code == 200
        assert response.data["total_reviews"] == 2
        assert response.data["rating_distribution"][5] == 1
        assert response.data["rating_distribution"][3] == 1