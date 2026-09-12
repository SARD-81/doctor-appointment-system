from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from .models import Wallet, WalletTransaction
from .services import WalletService

User = get_user_model()


@pytest.mark.django_db
def test_top_up_creates_wallet_transaction():
    user = User.objects.create_user(email="wallet@example.com", password="pass12345")

    wallet = WalletService.top_up(user=user, amount=Decimal("100"))

    assert wallet.balance == Decimal("100")
    assert WalletTransaction.objects.filter(transaction_type=WalletTransaction.TOP_UP).count() == 1
    assert wallet.transactions.first().balance_after == Decimal("100")


@pytest.mark.django_db
def test_top_up_rejects_non_positive_amount():
    user = User.objects.create_user(email="wallet2@example.com", password="pass12345")

    with pytest.raises(ValueError):
        WalletService.top_up(user=user, amount=Decimal("0"))
