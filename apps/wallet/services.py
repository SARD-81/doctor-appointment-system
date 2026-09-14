from decimal import Decimal

from django.db import transaction

from .models import Wallet, WalletTransaction

MAX_WALLET_BALANCE = Decimal("9999999999.99")


class WalletService:
    @staticmethod
    def top_up(*, user, amount: Decimal):
        if user is None:
            raise TypeError("User is required")

        if not isinstance(amount, Decimal):
            raise TypeError("Amount must be Decimal")

        if not amount.is_finite() or amount <= 0:
            raise ValueError("Amount must be a positive finite number")
        if amount > MAX_WALLET_BALANCE:
            raise ValueError("Amount exceeds the wallet storage limit")

        with transaction.atomic():
            wallet, _ = Wallet.objects.select_for_update().get_or_create(user=user)
            new_balance = wallet.balance + amount
            if new_balance > MAX_WALLET_BALANCE:
                raise ValueError("Top-up would exceed the maximum wallet balance")

            wallet.balance = new_balance
            wallet.save(update_fields=["balance", "updated_at"])

            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type=WalletTransaction.TOP_UP,
                amount=amount,
                balance_after=wallet.balance,
            )

        return wallet
