from decimal import Decimal

from django.db import transaction

from .models import Wallet, WalletTransaction


class WalletService:
    @staticmethod
    def top_up(*, user, amount: Decimal):
        if user is None:
            raise TypeError("User is required")

        if not isinstance(amount, Decimal):
            raise TypeError("Amount must be Decimal")

        if amount <= 0:
            raise ValueError("Amount must be positive")

        with transaction.atomic():
            wallet, _ = Wallet.objects.select_for_update().get_or_create(user=user)
            wallet.balance += amount
            wallet.save(update_fields=["balance", "updated_at"])

            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type=WalletTransaction.TOP_UP,
                amount=amount,
                balance_after=wallet.balance,
            )

        return wallet
