import time
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from apps.wallet.models import Wallet, WalletTransaction

User = get_user_model()


class WalletModelTest(TestCase):
    """تست‌های واحد مدل Wallet"""

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
    """تست‌های واحد مدل WalletTransaction"""

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

        # ست کردن زمان برای تضمین ترتیب در دیتابیس تست
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
