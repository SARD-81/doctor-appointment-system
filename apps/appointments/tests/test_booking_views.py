from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from apps.appointments.models import Appointment, AppointmentSlot
from apps.appointments.services import BookingService
from apps.doctors.models import Doctor, Specialty
from apps.wallet.models import Wallet

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
def patient(db):
    return User.objects.create_user(
        username="view_patient",
        email="view-patient@example.com",
        password="StrongPass123!",
    )


@pytest.fixture
def slot(db, doctor):
    return AppointmentSlot.objects.create(
        doctor=doctor,
        starts_at=timezone.now() + timedelta(days=1),
        is_active=True,
    )


@pytest.mark.django_db
class TestBookingViewAccessControl:
    def test_anonymous_request_redirects_and_books_nothing(self, client, slot):
        response = client.post(reverse("appointments:book", args=[slot.pk]))

        assert response.status_code == 302
        assert Appointment.objects.count() == 0

    def test_get_request_redirects_to_doctor_detail_without_side_effects(
        self, client, patient, slot, doctor
    ):
        client.force_login(patient)

        response = client.get(reverse("appointments:book", args=[slot.pk]))

        assert response.status_code == 302
        assert response.url == reverse("doctors:detail", args=[doctor.pk])
        assert Appointment.objects.count() == 0


@pytest.mark.django_db(transaction=True)
class TestBookingViewFlow:
    def test_successful_post_redirects_to_dedicated_success_page(self, client, patient, slot):
        client.force_login(patient)
        Wallet.objects.create(user=patient, balance=Decimal("400000.00"))

        response = client.post(reverse("appointments:book", args=[slot.pk]), follow=True)

        assert response.status_code == 200
        assert response.templates[0].name == "appointments/booking_success.html"
        assert Appointment.objects.count() == 1
        appointment = Appointment.objects.get()
        assert appointment.patient == patient
        assert response.redirect_chain[-1][0] == reverse(
            "appointments:booking_success", args=[appointment.pk]
        )
        assert "کد پیگیری" in response.content.decode("utf-8")

    def test_already_booked_slot_redirects_with_error(self, client, patient, slot, doctor):
        other = User.objects.create_user(
            username="other",
            email="other@example.com",
            password="StrongPass123!",
        )
        Wallet.objects.create(user=other, balance=Decimal("400000.00"))
        BookingService.book_appointment(patient=other, slot_id=slot.pk)

        client.force_login(patient)
        Wallet.objects.create(user=patient, balance=Decimal("400000.00"))

        response = client.post(reverse("appointments:book", args=[slot.pk]), follow=True)

        assert response.redirect_chain[-1][0] == reverse("doctors:detail", args=[doctor.pk])
        messages = [m.message for m in response.context["messages"]]
        assert any("در دسترس نیست" in m for m in messages)
        assert Appointment.objects.count() == 1

    def test_insufficient_balance_redirects_to_wallet(self, client, patient, slot):
        client.force_login(patient)

        response = client.post(reverse("appointments:book", args=[slot.pk]), follow=True)

        assert response.redirect_chain[-1][0] == reverse("wallet:detail")
        messages = [m.message for m in response.context["messages"]]
        assert any("کیف پول" in m for m in messages)
        assert Appointment.objects.count() == 0

    def test_unknown_slot_returns_404(self, client, patient):
        client.force_login(patient)
        response = client.post(reverse("appointments:book", args=[999999]))
        assert response.status_code == 404


@pytest.mark.django_db
class TestBookingSuccessPage:
    def test_success_page_requires_login(self, client):
        response = client.get(reverse("appointments:booking_success", args=[1]))
        assert response.status_code == 302

    def test_success_page_only_shows_to_booking_owner(self, client, patient, doctor, slot):
        owner = User.objects.create_user(
            username="success_owner",
            email="success-owner@example.com",
            password="StrongPass123!",
        )
        appointment = Appointment.objects.create(
            patient=owner,
            slot=slot,
            amount_paid=Decimal("350000.00"),
        )
        client.force_login(patient)

        response = client.get(reverse("appointments:booking_success", args=[appointment.pk]))

        assert response.status_code == 404

    def test_success_page_renders_for_owner(self, client, patient, doctor, slot):
        appointment = Appointment.objects.create(
            patient=patient,
            slot=slot,
            amount_paid=Decimal("350000.00"),
        )
        client.force_login(patient)

        response = client.get(reverse("appointments:booking_success", args=[appointment.pk]))
        html = response.content.decode("utf-8")

        assert response.status_code == 200
        assert "کد پیگیری" in html
        assert "سارا احمدی" in html
