from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.db import IntegrityError
from django.utils import timezone

from apps.appointments.exceptions import (
    InsufficientBalanceError,
    SlotUnavailableError,
)
from apps.appointments.models import (
    Appointment,
    AppointmentSlot,
    AppointmentStatus,
)
from apps.appointments.services import BookingService
from apps.doctors.models import Doctor, Specialty
from apps.wallet.models import Wallet, WalletTransaction

User = get_user_model()

VISIT_FEE = Decimal("50000.00")


@pytest.fixture
def specialty(db):
    return Specialty.objects.create(name="Cardiology")


@pytest.fixture
def doctor(db, specialty):
    return Doctor.objects.create(
        specialty=specialty,
        full_name="Dr. Arash Davari",
        visit_fee=VISIT_FEE,
        is_active=True,
    )


@pytest.fixture
def patient(db):
    return User.objects.create_user(
        username="booking_patient",
        email="booking-patient@example.com",
        password="ValidPassword123!",
    )


@pytest.fixture
def funded_wallet(db, patient):
    return Wallet.objects.create(user=patient, balance=Decimal("80000.00"))


@pytest.fixture
def slot(db, doctor):
    return AppointmentSlot.objects.create(
        doctor=doctor,
        starts_at=timezone.now() + timedelta(days=1),
        is_active=True,
    )


@pytest.mark.django_db(transaction=True)
class TestBookingServiceSuccess:
    def test_successful_booking_creates_confirmed_appointment_with_fee_snapshot(
        self, patient, funded_wallet, slot
    ):
        appointment = BookingService.book_appointment(patient=patient, slot_id=slot.pk)

        assert appointment.status == AppointmentStatus.CONFIRMED
        assert appointment.patient == patient
        assert appointment.slot == slot
        assert appointment.amount_paid == VISIT_FEE
        slot.refresh_from_db()
        assert slot.is_available is False

    def test_successful_booking_debits_wallet_and_writes_ledger_entry(
        self, patient, funded_wallet, slot
    ):
        appointment = BookingService.book_appointment(patient=patient, slot_id=slot.pk)

        funded_wallet.refresh_from_db()
        assert funded_wallet.balance == Decimal("30000.00")

        tx = funded_wallet.transactions.get()
        assert tx.transaction_type == WalletTransaction.APPOINTMENT_PAYMENT
        assert tx.amount == VISIT_FEE
        assert tx.balance_after == Decimal("30000.00")
        assert tx.appointment == appointment

    def test_confirmation_email_is_sent_after_commit(
        self, django_capture_on_commit_callbacks, patient, funded_wallet, slot
    ):
        callbacks = django_capture_on_commit_callbacks(execute=True)
        BookingService.book_appointment(patient=patient, slot_id=slot.pk)

        assert len(callbacks) == 1
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == ["booking-patient@example.com"]


@pytest.mark.django_db(transaction=True)
class TestBookingServiceFailures:
    def test_slot_already_booked_raises_and_keeps_wallet_intact(
        self, patient, funded_wallet, slot
    ):
        other = User.objects.create_user(
            username="other_patient",
            email="other@example.com",
            password="ValidPassword123!",
        )
        Wallet.objects.create(user=other, balance=VISIT_FEE)
        BookingService.book_appointment(patient=other, slot_id=slot.pk)

        with pytest.raises(SlotUnavailableError):
            BookingService.book_appointment(patient=patient, slot_id=slot.pk)

        funded_wallet.refresh_from_db()
        assert funded_wallet.balance == Decimal("80000.00")
        assert funded_wallet.transactions.count() == 0

    def test_inactive_slot_raises(self, patient, funded_wallet, doctor):
        inactive = AppointmentSlot.objects.create(
            doctor=doctor,
            starts_at=timezone.now() + timedelta(days=2),
            is_active=False,
        )
        with pytest.raises(SlotUnavailableError):
            BookingService.book_appointment(patient=patient, slot_id=inactive.pk)

    def test_past_slot_raises(self, patient, funded_wallet, doctor):
        past = AppointmentSlot.objects.create(
            doctor=doctor,
            starts_at=timezone.now() - timedelta(hours=1),
            is_active=True,
        )
        with pytest.raises(SlotUnavailableError):
            BookingService.book_appointment(patient=patient, slot_id=past.pk)

    def test_inactive_doctor_slot_raises(self, patient, funded_wallet, slot, doctor):
        doctor.is_active = False
        doctor.save()
        with pytest.raises(SlotUnavailableError):
            BookingService.book_appointment(patient=patient, slot_id=slot.pk)

    def test_unknown_slot_raises(self, patient, funded_wallet):
        with pytest.raises(SlotUnavailableError):
            BookingService.book_appointment(patient=patient, slot_id=999999)

    def test_missing_wallet_raises(self, patient, slot):
        with pytest.raises(InsufficientBalanceError):
            BookingService.book_appointment(patient=patient, slot_id=slot.pk)
        assert Appointment.objects.count() == 0

    def test_insufficient_balance_raises_and_writes_nothing(self, patient, slot):
        wallet = Wallet.objects.create(user=patient, balance=Decimal("10000.00"))

        with pytest.raises(InsufficientBalanceError) as exc_info:
            BookingService.book_appointment(patient=patient, slot_id=slot.pk)

        assert exc_info.value.balance == Decimal("10000.00")
        assert exc_info.value.required == VISIT_FEE
        assert Appointment.objects.count() == 0
        assert WalletTransaction.objects.count() == 0
        wallet.refresh_from_db()
        assert wallet.balance == Decimal("10000.00")

    def test_database_error_rolls_back_and_maps_to_slot_unavailable(
        self, patient, funded_wallet, slot
    ):
        with patch.object(
            Appointment.objects,
            "create",
            side_effect=IntegrityError("duplicate slot"),
        ):
            with pytest.raises(SlotUnavailableError):
                BookingService.book_appointment(patient=patient, slot_id=slot.pk)

        assert Appointment.objects.count() == 0
        assert WalletTransaction.objects.count() == 0
        funded_wallet.refresh_from_db()
        assert funded_wallet.balance == Decimal("80000.00")
        slot.refresh_from_db()
        assert slot.is_available is True

    def test_no_email_sent_on_failure(self, patient, slot):
        with pytest.raises(InsufficientBalanceError):
            BookingService.book_appointment(patient=patient, slot_id=slot.pk)
        assert len(mail.outbox) == 0

    def test_patient_is_required(self, slot):
        with pytest.raises(TypeError):
            BookingService.book_appointment(patient=None, slot_id=slot.pk)
