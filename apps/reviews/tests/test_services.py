import pytest
from django.core.exceptions import ValidationError

from apps.reviews.exceptions import (
    AppointmentNotCompletedError,
    ReviewAlreadyExistsError,
    ReviewOwnershipError,
)
from apps.reviews.models import Review
from apps.reviews.services import ReviewService


@pytest.mark.django_db
class TestReviewServiceSuccess:
    def test_owner_can_review_completed_appointment(self, completed_appointment, patient):
        review = ReviewService.create_review(
            patient=patient,
            appointment_id=completed_appointment.pk,
            rating=5,
            comment="تجربهٔ عالی بود.",
        )

        assert review.appointment == completed_appointment
        assert review.rating == 5
        assert review.comment == "تجربهٔ عالی بود."
        assert Review.objects.count() == 1

    def test_review_is_created_atomically_with_empty_comment(self, completed_appointment, patient):
        review = ReviewService.create_review(
            patient=patient,
            appointment_id=completed_appointment.pk,
            rating=4,
        )

        assert review.comment == ""
        assert Review.objects.count() == 1


@pytest.mark.django_db(transaction=True)
class TestReviewServiceFailures:
    def test_confirmed_appointment_is_not_reviewable(self, confirmed_appointment, patient):
        with pytest.raises(AppointmentNotCompletedError):
            ReviewService.create_review(
                patient=patient,
                appointment_id=confirmed_appointment.pk,
                rating=5,
            )
        assert Review.objects.count() == 0

    def test_review_for_other_users_appointment_is_denied(
        self, completed_appointment, other_patient
    ):
        with pytest.raises(ReviewOwnershipError):
            ReviewService.create_review(
                patient=other_patient,
                appointment_id=completed_appointment.pk,
                rating=5,
            )
        assert Review.objects.count() == 0

    def test_nonexistent_appointment_maps_to_ownership_error(self, patient):
        # بدون افشای وجود/عدم وجود رکورد؛ تصمیم امنیتی است
        with pytest.raises(ReviewOwnershipError):
            ReviewService.create_review(patient=patient, appointment_id=999999, rating=5)
        assert Review.objects.count() == 0

    def test_duplicate_review_is_rejected(self, completed_appointment, patient):
        ReviewService.create_review(
            patient=patient,
            appointment_id=completed_appointment.pk,
            rating=5,
        )

        with pytest.raises(ReviewAlreadyExistsError):
            ReviewService.create_review(
                patient=patient,
                appointment_id=completed_appointment.pk,
                rating=3,
            )
        assert Review.objects.count() == 1

    def test_invalid_rating_rolls_everything_back(self, completed_appointment, patient):
        with pytest.raises(ValidationError):
            ReviewService.create_review(
                patient=patient,
                appointment_id=completed_appointment.pk,
                rating=7,
            )
        assert Review.objects.count() == 0

    def test_patient_is_required(self, completed_appointment):
        with pytest.raises(TypeError):
            ReviewService.create_review(
                patient=None,
                appointment_id=completed_appointment.pk,
                rating=5,
            )
