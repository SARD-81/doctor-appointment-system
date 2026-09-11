from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from apps.appointments.models import Appointment, AppointmentSlot
from apps.doctors.models import Doctor, Specialty
from apps.wallet.models import Wallet, WalletTransaction

User = get_user_model()


class WalletModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="wallet_user_1",
            email="wallet_user_1@example.com",
            password="testpass123",
        )

    def test_create_wallet_default_balance(self):
        wallet = Wallet.objects.create(user=self.user)
        self.assertEqual(wallet.balance, Decimal("0.00"))
        self.assertEqual(str(wallet), f"Wallet for {self.user} (0.00)")

    def test_create_wallet_with_initial_balance(self):
        wallet = Wallet.objects.create(user=self.user, balance=Decimal("50000.00"))
        self.assertEqual(wallet.balance, Decimal("50000.00"))

    def test_one_wallet_per_user_unique(self):
        Wallet.objects.create(user=self.user)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Wallet.objects.create(user=self.user)

    def test_balance_cannot_be_negative_validation(self):
        wallet = Wallet(user=self.user, balance=Decimal("-10.00"))
        with self.assertRaises(ValidationError):
            wallet.full_clean()

    def test_balance_cannot_be_negative_db_constraint(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Wallet.objects.create(user=self.user, balance=Decimal("-50.00"))

    def test_delete_user_cascades_wallet(self):
        wallet = Wallet.objects.create(user=self.user)
        wallet_id = wallet.pk
        self.user.delete()
        self.assertFalse(Wallet.objects.filter(pk=wallet_id).exists())


class WalletTransactionModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="tx_user_1",
            email="tx_user_1@example.com",
            password="testpass123",
        )
        self.wallet = Wallet.objects.create(user=self.user, balance=Decimal("100000.00"))
        self.specialty = Specialty.objects.create(name="عمومی")

    def _create_doctor(self, full_name="دکتر تستی", visit_fee=Decimal("100000.00")):
        return Doctor.objects.create(
            specialty=self.specialty,
            full_name=full_name,
            visit_fee=visit_fee,
        )

    def _create_appointment(self, amount_paid=Decimal("50000.00"), days_ahead=1):
        doctor = self._create_doctor(visit_fee=amount_paid)
        slot = AppointmentSlot.objects.create(
            doctor=doctor,
            starts_at=timezone.now() + timedelta(days=days_ahead),
        )
        return Appointment.objects.create(
            patient=self.user,
            slot=slot,
            amount_paid=amount_paid,
        )

    def test_create_top_up_transaction(self):
        tx = WalletTransaction.objects.create(
            wallet=self.wallet,
            amount=Decimal("50000.00"),
            transaction_type=WalletTransaction.TransactionType.TOP_UP,
        )
        self.assertEqual(tx.amount, Decimal("50000.00"))
        self.assertEqual(tx.transaction_type, "TOP_UP")
        self.assertEqual(str(tx), f"TOP_UP - 50000.00 ({self.user})")

    def test_create_appointment_payment_transaction(self):
        appointment = self._create_appointment(amount_paid=Decimal("20000.00"))

        tx = WalletTransaction.objects.create(
            wallet=self.wallet,
            appointment=appointment,
            amount=Decimal("20000.00"),
            transaction_type=WalletTransaction.TransactionType.APPOINTMENT_PAYMENT,
        )
        self.assertEqual(tx.amount, Decimal("20000.00"))
        self.assertEqual(tx.transaction_type, "APPOINTMENT_PAYMENT")

    def test_transaction_amount_must_be_positive(self):
        tx = WalletTransaction(
            wallet=self.wallet,
            amount=Decimal("0.00"),
            transaction_type=WalletTransaction.TransactionType.TOP_UP,
        )
        with self.assertRaises(ValidationError):
            tx.full_clean()

    def test_transaction_ordering_by_created_at_desc(self):
        appointment = self._create_appointment(amount_paid=Decimal("2000.00"))

        tx1 = WalletTransaction.objects.create(
            wallet=self.wallet,
            amount=Decimal("1000.00"),
            transaction_type=WalletTransaction.TransactionType.TOP_UP,
        )
        tx2 = WalletTransaction.objects.create(
            wallet=self.wallet,
            appointment=appointment,
            amount=Decimal("2000.00"),
            transaction_type=WalletTransaction.TransactionType.APPOINTMENT_PAYMENT,
        )

        WalletTransaction.objects.filter(pk=tx1.pk).update(
            created_at=timezone.now() - timedelta(minutes=10)
        )
        WalletTransaction.objects.filter(pk=tx2.pk).update(
            created_at=timezone.now() - timedelta(minutes=5)
        )

        transactions = list(self.wallet.transactions.all())
        self.assertEqual(transactions, [tx2, tx1])

    def test_delete_wallet_cascades_transactions(self):
        tx = WalletTransaction.objects.create(
            wallet=self.wallet,
            amount=Decimal("1000.00"),
            transaction_type=WalletTransaction.TransactionType.TOP_UP,
        )
        tx_id = tx.pk
        self.wallet.delete()
        self.assertFalse(WalletTransaction.objects.filter(pk=tx_id).exists())

    def test_create_transaction_linked_to_appointment(self):
        appointment = self._create_appointment(amount_paid=Decimal("50000.00"))

        tx = WalletTransaction.objects.create(
            wallet=self.wallet,
            appointment=appointment,
            amount=Decimal("50000.00"),
            transaction_type=WalletTransaction.TransactionType.APPOINTMENT_PAYMENT,
        )

        self.assertEqual(tx.appointment, appointment)
        self.assertIn(tx, appointment.wallet_transactions.all())

    def test_transaction_appointment_is_optional_for_top_up(self):
        tx = WalletTransaction.objects.create(
            wallet=self.wallet,
            amount=Decimal("15000.00"),
            transaction_type=WalletTransaction.TransactionType.TOP_UP,
        )
        self.assertIsNone(tx.appointment)

    def test_top_up_with_appointment_is_invalid(self):
        """Enforces the rule: TOP_UP -> appointment must be NULL."""
        appointment = self._create_appointment(amount_paid=Decimal("10000.00"))
        tx = WalletTransaction(
            wallet=self.wallet,
            appointment=appointment,
            amount=Decimal("10000.00"),
            transaction_type=WalletTransaction.TransactionType.TOP_UP,
        )
        with self.assertRaises(ValidationError):
            tx.full_clean()

    def test_appointment_payment_without_appointment_is_invalid(self):
        """Enforces the rule: APPOINTMENT_PAYMENT -> appointment is required."""
        tx = WalletTransaction(
            wallet=self.wallet,
            amount=Decimal("10000.00"),
            transaction_type=WalletTransaction.TransactionType.APPOINTMENT_PAYMENT,
        )
        with self.assertRaises(ValidationError):
            tx.full_clean()

    def test_deleting_appointment_sets_transaction_appointment_to_null(self):
        appointment = self._create_appointment(amount_paid=Decimal("30000.00"), days_ahead=2)

        tx = WalletTransaction.objects.create(
            wallet=self.wallet,
            appointment=appointment,
            amount=Decimal("30000.00"),
            transaction_type=WalletTransaction.TransactionType.APPOINTMENT_PAYMENT,
        )
        tx_id = tx.pk

        appointment.delete()

        tx.refresh_from_db()
        self.assertTrue(WalletTransaction.objects.filter(pk=tx_id).exists())
        self.assertIsNone(tx.appointment)
