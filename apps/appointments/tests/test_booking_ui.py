from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from apps.appointments.models import AppointmentSlot
from apps.doctors.models import Doctor, Specialty

User = get_user_model()


@pytest.fixture
def specialty(db):
    return Specialty.objects.create(name="قلب و عروق")


@pytest.fixture
def doctor(db, specialty):
    return Doctor.objects.create(
        specialty=specialty,
        full_name="سارا احمدی",
        visit_fee=Decimal("350000.50"),
        is_active=True,
    )


@pytest.fixture
def slot(db, doctor):
    return AppointmentSlot.objects.create(
        doctor=doctor,
        starts_at=timezone.now() + timedelta(days=1),
        is_active=True,
    )


@pytest.mark.django_db
class TestBookingActionVisibility:
    def test_anonymous_user_gets_login_cta_not_booking_form(self, client, doctor, slot):
        response = client.get(
            reverse("doctors:detail", args=[doctor.pk]),
            {"slot": slot.pk},
        )
        html = response.content.decode("utf-8")

        assert response.status_code == 200
        assert "data-booking-form" not in html
        assert "data-booking-login-cta" in html
        assert "برای رزرو وارد شوید" in html
        assert "appointments/book" not in html
        login_url = reverse("accounts:login")
        assert login_url in html
        assert "next=" in html

    def test_authenticated_user_sees_booking_form(self, client, doctor, slot):
        user = User.objects.create_user(
            username="booking_ui_patient",
            email="booking-ui-patient@example.com",
            password="StrongPass123!",
        )
        client.force_login(user)

        response = client.get(
            reverse("doctors:detail", args=[doctor.pk]),
            {"slot": slot.pk},
        )
        html = response.content.decode("utf-8")

        assert response.status_code == 200
        assert "data-booking-form" in html
        assert reverse("appointments:book", args=[slot.pk]) in html
        assert "data-booking-login-cta" not in html
