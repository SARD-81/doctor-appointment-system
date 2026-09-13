import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.reviews.models import Review


@pytest.mark.django_db
class TestReviewModel:
    def test_rating_1_and_5_are_valid(self, completed_appointment, other_patient, specialty):
        review_min = Review(appointment=completed_appointment, rating=1, comment="حداقل امتیاز")
        review_min.full_clean()
        assert review_min.rating == 1

        review_max = Review(appointment=completed_appointment, rating=5)
        review_max.full_clean()
        assert review_max.rating == 5

    def test_rating_0_is_rejected_at_application_level(self, completed_appointment):
        review = Review(appointment=completed_appointment, rating=0)
        with pytest.raises(ValidationError):
            review.full_clean()

    def test_rating_6_is_rejected_at_application_level(self, completed_appointment):
        review = Review(appointment=completed_appointment, rating=6)
        with pytest.raises(ValidationError):
            review.full_clean()

    def test_rating_out_of_range_rejected_at_database_level(self, completed_appointment):
        # بدون full_clean؛ فقط CheckConstraint دیتابیسی می‌تواند ممانعت کند
        with pytest.raises(IntegrityError):
            Review.objects.create(appointment=completed_appointment, rating=0)

    def test_oneappointment_cannot_have_multiple_reviews(self, completed_appointment):
        Review.objects.create(appointment=completed_appointment, rating=5)
        with pytest.raises(IntegrityError):
            Review.objects.create(appointment=completed_appointment, rating=4)

    def test_blank_comment_stored_as_empty_string(self, completed_appointment):
        review = Review.objects.create(appointment=completed_appointment, rating=4, comment="")
        review.refresh_from_db()
        assert review.comment == ""

    def test_comment_defaults_to_empty_string(self, completed_appointment):
        review = Review.objects.create(appointment=completed_appointment, rating=3)
        review.refresh_from_db()
        assert review.comment == ""

    def test_timestamps_are_written_and_refreshable(self, completed_appointment):
        review = Review.objects.create(appointment=completed_appointment, rating=5)
        assert review.created_at is not None
        assert review.updated_at is not None

        original = review.updated_at
        review.comment = "ویرایش نظر"
        review.save()
        review.refresh_from_db()
        assert review.updated_at > original

    def test_default_ordering_is_newest_first(self, patient, other_patient, doctor):
        from datetime import timedelta

        from django.utils import timezone

        from apps.appointments.models import Appointment, AppointmentSlot, AppointmentStatus

        first_slot = AppointmentSlot.objects.create(
            doctor=doctor,
            starts_at=timezone.now() + timedelta(days=1),
        )
        second_slot = AppointmentSlot.objects.create(
            doctor=doctor,
            starts_at=timezone.now() + timedelta(days=2),
        )
        first_appointment = Appointment.objects.create(
            patient=patient,
            slot=first_slot,
            amount_paid="350000.00",
            status=AppointmentStatus.COMPLETED,
        )
        second_appointment = Appointment.objects.create(
            patient=other_patient,
            slot=second_slot,
            amount_paid="350000.00",
            status=AppointmentStatus.COMPLETED,
        )
        first = Review.objects.create(appointment=first_appointment, rating=4)
        second = Review.objects.create(appointment=second_appointment, rating=5)

        reviews = list(Review.objects.all())
        assert reviews[0] == second
        assert reviews[1] == first
