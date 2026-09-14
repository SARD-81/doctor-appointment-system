from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.utils import timezone

from apps.appointments.models import Appointment, AppointmentSlot
from apps.doctors.models import Doctor, Specialty

from .models import Wallet, WalletTransaction
from .services import WalletService

User = get_user_model()


def create_user(username):
    return User.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="pass12345",
    )


@pytest.fixture
def patient_booking(db):
    user = create_user("ledger-patient")
    specialty = Specialty.objects.create(name="Ledger specialty")
    doctor = Doctor.objects.create(
        specialty=specialty,
        full_name="Ledger doctor",
        visit_fee=Decimal("100.00"),
    )
    slot = AppointmentSlot.objects.create(
        doctor=doctor,
        starts_at=timezone.now() + timedelta(days=1),
    )
    appointment = Appointment.objects.create(
        patient=user,
        slot=slot,
        amount_paid=Decimal("100.00"),
    )
    return Wallet.objects.create(user=user, balance=Decimal("100.00")), appointment


@pytest.mark.django_db
def test_top_up_creates_wallet_transaction():
    user = create_user("wallet")

    wallet = WalletService.top_up(user=user, amount=Decimal("100"))

    assert wallet.balance == Decimal("100")
    assert WalletTransaction.objects.filter(transaction_type=WalletTransaction.TOP_UP).count() == 1
    assert wallet.transactions.first().balance_after == Decimal("100")


@pytest.mark.django_db
def test_top_up_rejects_non_positive_amount():
    user = create_user("wallet2")

    with pytest.raises(ValueError):
        WalletService.top_up(user=user, amount=Decimal("0"))


def test_top_up_requires_decimal_amount():
    with pytest.raises(TypeError):
        WalletService.top_up(user=None, amount=100)


@pytest.mark.django_db
@pytest.mark.parametrize("amount", [Decimal("NaN"), Decimal("Infinity"), Decimal("-Infinity")])
def test_top_up_rejects_non_finite_amounts(amount):
    user = create_user(f"wallet-{str(amount).lower()}")

    with pytest.raises(ValueError):
        WalletService.top_up(user=user, amount=amount)


@pytest.mark.django_db
def test_top_up_rejects_balance_overflow():
    user = create_user("wallet-overflow")
    WalletService.top_up(user=user, amount=Decimal("9999999999.99"))

    with pytest.raises(ValueError):
        WalletService.top_up(user=user, amount=Decimal("0.01"))


@pytest.mark.django_db(transaction=True)
def test_ledger_rejects_top_up_with_appointment(patient_booking):
    wallet, appointment = patient_booking

    with pytest.raises(IntegrityError):
        WalletTransaction.objects.create(
            wallet=wallet,
            appointment=appointment,
            transaction_type=WalletTransaction.TOP_UP,
            amount=Decimal("1.00"),
            balance_after=wallet.balance,
        )


@pytest.mark.django_db(transaction=True)
def test_ledger_rejects_payment_without_appointment(patient_booking):
    wallet, _ = patient_booking

    with pytest.raises(IntegrityError):
        WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type=WalletTransaction.APPOINTMENT_PAYMENT,
            amount=Decimal("1.00"),
            balance_after=wallet.balance,
        )


@pytest.mark.django_db(transaction=True)
def test_ledger_rejects_duplicate_appointment_payment(patient_booking):
    wallet, appointment = patient_booking
    transaction = {
        "wallet": wallet,
        "appointment": appointment,
        "transaction_type": WalletTransaction.APPOINTMENT_PAYMENT,
        "amount": Decimal("1.00"),
        "balance_after": Decimal("99.00"),
    }
    WalletTransaction.objects.create(**transaction)

    with pytest.raises(IntegrityError):
        WalletTransaction.objects.create(**transaction)
