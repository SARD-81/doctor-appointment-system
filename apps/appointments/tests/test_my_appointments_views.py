from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from apps.appointments.models import Appointment, AppointmentSlot, AppointmentStatus
from apps.doctors.models import Doctor, Specialty

User = get_user_model()


@pytest.fixture
def specialty(db):
    return Specialty.objects.create(name="قلب و عروق")


@pytest.fixture
def doctor(db, specialty):
    return Doctor.objects.create(
        specialty=specialty,
        full_name="دکتر سارا احمدی",
        visit_fee=Decimal("350000.00"),
        is_active=True,
    )


@pytest.fixture
def patients(db):
    owner = User.objects.create_user(
        username="appointment_owner",
        email="owner@example.com",
        password="StrongPass123!",
    )
    other = User.objects.create_user(
        username="other_patient",
        email="other@example.com",
        password="StrongPass123!",
    )
    return owner, other


@pytest.mark.django_db
class TestMyAppointmentsView:
    def test_my_appointments_requires_login(self, client):
        response = client.get(reverse("appointments:my_appointments"))
        assert response.status_code == 302

    def test_only_current_users_appointments_are_rendered(self, client, doctor, patients):
        owner, other = patients
        owner_slot = AppointmentSlot.objects.create(
            doctor=doctor,
            starts_at=timezone.now() + timedelta(days=1),
        )
        other_slot = AppointmentSlot.objects.create(
            doctor=doctor,
            starts_at=timezone.now() + timedelta(days=2),
        )
        owner_appointment = Appointment.objects.create(
            patient=owner,
            slot=owner_slot,
            amount_paid=Decimal("350000.00"),
        )
        other_appointment = Appointment.objects.create(
            patient=other,
            slot=other_slot,
            amount_paid=Decimal("350000.00"),
        )
        client.force_login(owner)

        response = client.get(reverse("appointments:my_appointments"))
        html = response.content.decode("utf-8")

        assert response.status_code == 200
        assert f"کد پیگیری #{owner_appointment.pk}" in html
        assert f"کد پیگیری #{other_appointment.pk}" not in html

    def test_completed_appointment_has_completed_status(self, client, doctor, patients):
        owner, _ = patients
        slot = AppointmentSlot.objects.create(
            doctor=doctor,
            starts_at=timezone.now() + timedelta(days=1),
        )
        Appointment.objects.create(
            patient=owner,
            slot=slot,
            amount_paid=Decimal("350000.00"),
            status=AppointmentStatus.COMPLETED,
            completed_at=timezone.now(),
        )
        client.force_login(owner)

        response = client.get(reverse("appointments:my_appointments"))

        assert response.status_code == 200
        assert "تکمیل‌شده" in response.content.decode("utf-8")

    def test_empty_state_links_to_doctor_search(self, client, patients):
        owner, _ = patients
        client.force_login(owner)

        response = client.get(reverse("appointments:my_appointments"))
        html = response.content.decode("utf-8")

        assert response.status_code == 200
        assert "هنوز نوبتی رزرو نکرده‌اید" in html
        assert reverse("doctors:list") in html
