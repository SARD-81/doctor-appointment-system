import time
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from apps.appointments.models import Appointment, AppointmentSlot
from apps.doctors.models import Doctor, Specialty
from apps.reviews.models import Review

User = get_user_model()


class ReviewModelTest(TestCase):

    def setUp(self):
        self.specialty = Specialty.objects.create(name="قلب و عروق")
        self.doctor = Doctor.objects.create(
            specialty=self.specialty,
            full_name="دکتر محمدی",
            visit_fee=Decimal("150000.00"),
        )
        self.patient = User.objects.create_user(
            username="review_patient_1",
            email="review_patient_1@example.com",
            password="testpass123",
        )
        self.slot = AppointmentSlot.objects.create(
            doctor=self.doctor,
            starts_at=timezone.now() + timedelta(days=1),
        )
        self.appointment = Appointment.objects.create(
            patient=self.patient,
            slot=self.slot,
            amount_paid=Decimal("150000.00"),
        )

    def _create_review(self, appointment=None, **kwargs):
        defaults = {"rating": 5}
        defaults.update(kwargs)
        return Review.objects.create(
            appointment=appointment or self.appointment,
            **defaults,
        )


    def test_create_review_success(self):
        review = self._create_review(rating=4, comment="دکتر خوبی بود")
        self.assertIsNotNone(review.pk)
        self.assertEqual(review.rating, 4)
        self.assertEqual(review.comment, "دکتر خوبی بود")

    def test_review_str_method(self):
        review = self._create_review(rating=5)
        self.assertEqual(
            str(review),
            f"Review for {self.appointment} (5/5)",
        )

    def test_review_created_without_comment(self):
        review = self._create_review(rating=3)
        self.assertEqual(review.comment, "")

    def test_reverse_relation_from_appointment(self):
        review = self._create_review(rating=4)
        self.assertEqual(self.appointment.review, review)


    def test_rating_min_valid(self):
        review = self._create_review(rating=1)
        review.full_clean()
        self.assertEqual(review.rating, 1)

    def test_rating_max_valid(self):
        review = self._create_review(rating=5)
        review.full_clean()
        self.assertEqual(review.rating, 5)

    def test_rating_below_min_invalid(self):
        review = Review(appointment=self.appointment, rating=0)
        with self.assertRaises(ValidationError):
            review.full_clean()

    def test_rating_above_max_invalid(self):
        review = Review(appointment=self.appointment, rating=6)
        with self.assertRaises(ValidationError):
            review.full_clean()

    def test_rating_check_constraint_enforced_at_db(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Review.objects.create(
                    appointment=self.appointment,
                    rating=0,
                )


    def test_one_review_per_appointment(self):
        self._create_review(rating=5)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Review.objects.create(
                    appointment=self.appointment,
                    rating=4,
                )

    def test_new_review_allowed_after_deleting_old_one(self):
        review = self._create_review(rating=5)
        review.delete()
        new_review = self._create_review(rating=2)
        self.assertEqual(Review.objects.count(), 1)
        self.assertIsNotNone(new_review.pk)


    def test_deleting_appointment_cascades_review(self):
        review = self._create_review(rating=5)
        review_id = review.pk
        self.appointment.delete()
        self.assertFalse(Review.objects.filter(pk=review_id).exists())


    def test_created_and_updated_at_auto_set(self):
        review = self._create_review(rating=5)
        self.assertIsNotNone(review.created_at)
        self.assertIsNotNone(review.updated_at)

    def test_updated_at_changes_on_save(self):
        review = self._create_review(rating=5)
        old_updated_at = review.updated_at
        time.sleep(0.01)
        review.rating = 1
        review.save()
        review.refresh_from_db()
        self.assertGreater(review.updated_at, old_updated_at)


    def test_ordering_by_created_at_descending(self):
        other_patient = User.objects.create_user(
            username="review_patient_2",
            email="review_patient_2@example.com",
            password="testpass123",
        )
        other_slot = AppointmentSlot.objects.create(
            doctor=self.doctor,
            starts_at=timezone.now() + timedelta(days=2),
        )
        other_appointment = Appointment.objects.create(
            patient=other_patient,
            slot=other_slot,
            amount_paid=Decimal("120000.00"),
        )

        older_review = self._create_review(rating=3, comment="قدیمی")
        newer_review = self._create_review(
            appointment=other_appointment,
            rating=5,
            comment="جدید",
        )

        Review.objects.filter(pk=older_review.pk).update(
            created_at=timezone.now() - timedelta(hours=2)
        )
        Review.objects.filter(pk=newer_review.pk).update(
            created_at=timezone.now() - timedelta(hours=1)
        )

        reviews = list(Review.objects.all())
        self.assertEqual(reviews, [newer_review, older_review])
