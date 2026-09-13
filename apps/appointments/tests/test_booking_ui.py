from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from apps.appointments.models import AppointmentSlot
from apps.doctors.models import Doctor, Specialty
from apps.wallet.models import Wallet

User = get_user_model()

VISIT_FEE = Decimal("350000.50")


@pytest.fixture
def specialty(db):
    return Specialty.objects.create(name="قلب و عروق")


@pytest.fixture
def doctor(db, specialty):
    return Doctor.objects.create(
        specialty=specialty,
        full_name="سارا احمدی",
        visit_fee=VISIT_FEE,
        is_active=True,
    )


@pytest.fixture
def slot(db, doctor):
    return AppointmentSlot.objects.create(
        doctor=doctor,
        starts_at=timezone.now() + timedelta(days=1),
        is_active=True,
    )


@pytest.fixture
def patient(db):
    return User.objects.create_user(
        username="booking_ui_patient",
        email="booking-ui-patient@example.com",
        password="StrongPass123!",
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

    def test_authenticated_user_sees_booking_form(self, client, patient, doctor, slot):
        Wallet.objects.create(user=patient, balance=Decimal("900000.00"))
        client.force_login(patient)

        response = client.get(
            reverse("doctors:detail", args=[doctor.pk]),
            {"slot": slot.pk},
        )
        html = response.content.decode("utf-8")

        assert response.status_code == 200
        assert "data-booking-summary" in html
        assert "data-booking-form" in html
        assert reverse("appointments:book", args=[slot.pk]) in html
        assert "900000.00" in html
        assert "data-booking-insufficient" not in html
        assert "data-booking-login-cta" not in html

    def test_authenticated_insufficient_wallet_gets_topup_guidance(self, client, patient, doctor, slot):
        Wallet.objects.create(user=patient, balance=Decimal("10000.00"))
        client.force_login(patient)

        response = client.get(
            reverse("doctors:detail", args=[doctor.pk]),
            {"slot": slot.pk},
        )
        html = response.content.decode("utf-8")

        assert response.status_code == 200
        assert "data-booking-insufficient" in html
        assert "موجودی کیف پول کافی نیست" in html
        assert "data-booking-form" not in html
        assert reverse("wallet:detail") in html

    def test_authenticated_without_wallet_is_guided_to_topup(self, client, patient, doctor, slot):
        client.force_login(patient)

        response = client.get(
            reverse("doctors:detail", args=[doctor.pk]),
            {"slot": slot.pk},
        )
        html = response.content.decode("utf-8")

        assert response.status_code == 200
        assert "data-booking-no-wallet" in html
        assert "کیف پول شما هنوز شارژ نشده است" in html
        assert "data-booking-form" not in html
        assert reverse("wallet:detail") in html
