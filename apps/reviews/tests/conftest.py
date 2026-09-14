from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
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
def patient(db):
    return User.objects.create_user(
        username="review_patient",
        email="review-patient@example.com",
        password="StrongPass123!",
    )


@pytest.fixture
def other_patient(db):
    return User.objects.create_user(
        username="review_other_patient",
        email="review-other-patient@example.com",
        password="StrongPass123!",
    )


@pytest.fixture
def slot(db, doctor):
    return AppointmentSlot.objects.create(
        doctor=doctor,
        starts_at=timezone.now() + timedelta(days=1),
        is_active=True,
    )


@pytest.fixture
def completed_appointment(db, patient, slot):
    return Appointment.objects.create(
        patient=patient,
        slot=slot,
        amount_paid=Decimal("350000.00"),
        status=AppointmentStatus.COMPLETED,
        completed_at=timezone.now(),
    )


@pytest.fixture
def confirmed_slot(db, doctor):
    return AppointmentSlot.objects.create(
        doctor=doctor,
        starts_at=timezone.now() + timedelta(days=2),
        is_active=True,
    )


@pytest.fixture
def confirmed_appointment(db, patient, confirmed_slot):
    return Appointment.objects.create(
        patient=patient,
        slot=confirmed_slot,
        amount_paid=Decimal("350000.00"),
        status=AppointmentStatus.CONFIRMED,
    )
