from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from apps.appointments.models import Appointment, AppointmentSlot
from apps.doctors.models import Doctor
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
        self.assertEqual(str(wallet), f"کیف پول {self.user} (0.00)")

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

    def test_create_deposit_transaction(self):
        tx = WalletTransaction.objects.create(
            wallet=self.wallet,
            amount=Decimal("50000.00"),
            transaction_type=WalletTransaction.TransactionType.DEPOSIT,
        )
        self.assertEqual(tx.amount, Decimal("50000.00"))
        self.assertEqual(tx.transaction_type, "DEPOSIT")
        self.assertEqual(str(tx), f"DEPOSIT - 50000.00 ({self.user})")

    def test_create_withdraw_transaction(self):
        tx = WalletTransaction.objects.create(
            wallet=self.wallet,
            amount=Decimal("20000.00"),
            transaction_type=WalletTransaction.TransactionType.WITHDRAW,
        )
        self.assertEqual(tx.amount, Decimal("20000.00"))
        self.assertEqual(tx.transaction_type, "WITHDRAW")

    def test_transaction_amount_must_be_positive(self):
        tx = WalletTransaction(
            wallet=self.wallet,
            amount=Decimal("0.00"),
            transaction_type=WalletTransaction.TransactionType.DEPOSIT,
        )
        with self.assertRaises(ValidationError):
            tx.full_clean()

    def test_transaction_ordering_by_created_at_desc(self):
        tx1 = WalletTransaction.objects.create(
            wallet=self.wallet,
            amount=Decimal("1000.00"),
            transaction_type=WalletTransaction.TransactionType.DEPOSIT,
        )
        tx2 = WalletTransaction.objects.create(
            wallet=self.wallet,
            amount=Decimal("2000.00"),
            transaction_type=WalletTransaction.TransactionType.WITHDRAW,
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
            transaction_type=WalletTransaction.TransactionType.DEPOSIT,
        )
        tx_id = tx.pk
        self.wallet.delete()
        self.assertFalse(WalletTransaction.objects.filter(pk=tx_id).exists())

    def test_create_transaction_linked_to_appointment(self):
        doctor_user = User.objects.create_user(
            username="doc_user_1",
            email="doc_user_1@example.com",
            password="testpass123",
        )
        doctor = Doctor.objects.create(
            user=doctor_user,
            specialty="Cardiology",
        )
        slot = AppointmentSlot.objects.create(
            doctor=doctor,
            starts_at=timezone.now() + timedelta(days=1),
        )
        appointment = Appointment.objects.create(
            patient=self.user,
            slot=slot,
            amount_paid=Decimal("50000.00"),
        )

        tx = WalletTransaction.objects.create(
            wallet=self.wallet,
            appointment=appointment,
            amount=Decimal("50000.00"),
            transaction_type=WalletTransaction.TransactionType.WITHDRAW,
        )

        self.assertEqual(tx.appointment, appointment)
        self.assertIn(tx, appointment.wallet_transactions.all())

    def test_transaction_appointment_is_optional(self):
        tx = WalletTransaction.objects.create(
            wallet=self.wallet,
            amount=Decimal("15000.00"),
            transaction_type=WalletTransaction.TransactionType.DEPOSIT,
        )
        self.assertIsNone(tx.appointment)

    def test_deleting_appointment_sets_transaction_appointment_to_null(self):
        doctor_user = User.objects.create_user(
            username="doc_user_2",
            email="doc_user_2@example.com",
            password="testpass123",
        )
        doctor = Doctor.objects.create(
            user=doctor_user,
            specialty="Dermatology",
        )
        slot = AppointmentSlot.objects.create(
            doctor=doctor,
            starts_at=timezone.now() + timedelta(days=2),
        )
        appointment = Appointment.objects.create(
            patient=self.user,
            slot=slot,
            amount_paid=Decimal("30000.00"),
        )

        tx = WalletTransaction.objects.create(
            wallet=self.wallet,
            appointment=appointment,
            amount=Decimal("30000.00"),
            transaction_type=WalletTransaction.TransactionType.WITHDRAW,
        )
        tx_id = tx.pk

        appointment.delete()

        tx.refresh_from_db()
        self.assertTrue(WalletTransaction.objects.filter(pk=tx_id).exists())
        self.assertIsNone(tx.appointment)
