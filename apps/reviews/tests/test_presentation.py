from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from apps.appointments.models import Appointment, AppointmentSlot, AppointmentStatus
from apps.doctors.models import Doctor, Specialty
from apps.reviews.models import Review

User = get_user_model()


@pytest.fixture
def specialty(db):
    return Specialty.objects.create(name="مغز و اعصاب")


@pytest.fixture
def presentation_doctor(db, specialty):
    return Doctor.objects.create(
        specialty=specialty,
        full_name="دکتر علی رضایی",
        visit_fee=Decimal("420000.00"),
        is_active=True,
    )


def _add_review(doctor, username, rating):
    """ساخت نوبت تکمیل‌شده + نظر واقعی برای یک بیمار تازه."""
    patient = User.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="StrongPass123!",
    )
    slot = AppointmentSlot.objects.create(
        doctor=doctor,
        starts_at=timezone.now() - timedelta(days=1),
        is_active=True,
    )
    appointment = Appointment.objects.create(
        patient=patient,
        slot=slot,
        amount_paid=Decimal("420000.00"),
        status=AppointmentStatus.COMPLETED,
        completed_at=timezone.now(),
    )
    return Review.objects.create(appointment=appointment, rating=rating)


@pytest.mark.django_db
class TestDoctorRatingPresentation:
    def test_doctor_list_shows_rating_badge_when_reviews_exist(self, client, presentation_doctor):
        _add_review(presentation_doctor, "rating_lister", 5)

        response = client.get(reverse("doctors:list"))
        html = response.content.decode("utf-8")

        assert "rating-inline" in html
        assert "5.0" in html
        assert "(1 نظر)" in html

    def test_doctor_list_hides_rating_badge_without_reviews(self, client, presentation_doctor):
        response = client.get(reverse("doctors:list"))
        assert "rating-inline" not in response.content.decode("utf-8")

    def test_average_rating_rounds_to_one_decimal_place(self, client, presentation_doctor):
        _add_review(presentation_doctor, "rater_a", 4)
        _add_review(presentation_doctor, "rater_b", 5)

        response = client.get(reverse("doctors:list"))
        assert "4.5" in response.content.decode("utf-8")

    def test_doctor_detail_shows_rating_summary(self, client, presentation_doctor):
        _add_review(presentation_doctor, "detail_rater", 4)

        response = client.get(reverse("doctors:detail", args=[presentation_doctor.pk]))
        html = response.content.decode("utf-8")

        assert "میانگین امتیاز" in html
        assert "4.0 از ۵" in html
        assert "1 نظر" in html

    def test_doctor_detail_shows_friendly_empty_state(self, client, presentation_doctor):
        response = client.get(reverse("doctors:detail", args=[presentation_doctor.pk]))
        assert "هنوز نظری ثبت نشده است" in response.content.decode("utf-8")


@pytest.mark.django_db
class TestMyAppointmentsReviewSurface:
    def _complete_appointment(self, doctor, username, *, status):
        patient = User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="StrongPass123!",
        )
        slot = AppointmentSlot.objects.create(
            doctor=doctor,
            starts_at=timezone.now() - timedelta(hours=2),
            is_active=True,
        )
        appointment = Appointment.objects.create(
            patient=patient,
            slot=slot,
            amount_paid=Decimal("420000.00"),
            status=status,
            completed_at=timezone.now() if status == AppointmentStatus.COMPLETED else None,
        )
        return patient, appointment

    def test_completed_appointment_without_review_offers_form(self, client, presentation_doctor):
        patient, appointment = self._complete_appointment(
            presentation_doctor,
            "review_form_owner",
            status=AppointmentStatus.COMPLETED,
        )
        client.force_login(patient)

        response = client.get(reverse("appointments:my_appointments"))
        html = response.content.decode("utf-8")

        assert reverse("reviews:create", args=[appointment.pk]) in html
        assert 'name="rating"' in html

    def test_completed_appointment_with_review_shows_own_rating(self, client, presentation_doctor):
        patient, appointment = self._complete_appointment(
            presentation_doctor,
            "reviewed_owner",
            status=AppointmentStatus.COMPLETED,
        )
        Review.objects.create(appointment=appointment, rating=5, comment="عالی بود")
        client.force_login(patient)

        response = client.get(reverse("appointments:my_appointments"))
        html = response.content.decode("utf-8")

        assert "امتیاز شما:" in html
        assert "star-display" in html
        assert reverse("reviews:create", args=[appointment.pk]) not in html

    def test_confirmed_appointment_does_not_offer_review_form(self, client, presentation_doctor):
        patient, appointment = self._complete_appointment(
            presentation_doctor,
            "confirmed_owner",
            status=AppointmentStatus.CONFIRMED,
        )
        client.force_login(patient)

        response = client.get(reverse("appointments:my_appointments"))
        html = response.content.decode("utf-8")

        assert reverse("reviews:create", args=[appointment.pk]) not in html
        assert 'name="rating"' not in html
