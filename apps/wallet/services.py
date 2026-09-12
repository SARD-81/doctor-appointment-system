from decimal import Decimal

from django.db import transaction

from .models import Wallet, WalletTransaction


class WalletService:
    @staticmethod
    @transaction.atomic
    def top_up(*, user, amount: Decimal):
        if amount <= 0:
            raise ValueError("Amount must be positive")

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
