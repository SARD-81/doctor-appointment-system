from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from .models import WalletTransaction
from .services import WalletService

User = get_user_model()


def create_user(username):
    return User.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="pass12345",
    )


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
