from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from django.urls import reverse

from .models import Wallet, WalletTransaction
from .services import MAX_ALLOWED_BALANCE, MAX_PER_TRANSACTION, WalletService

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
    assert (
        WalletTransaction.objects.filter(
            transaction_type=WalletTransaction.TOP_UP
        ).count()
        == 1
    )
    assert wallet.transactions.first().balance_after == Decimal("100")


@pytest.mark.django_db
def test_top_up_rejects_non_positive_amount():
    user = create_user("wallet-non-positive")

    with pytest.raises(ValueError):
        WalletService.top_up(user=user, amount=Decimal("0"))


def test_top_up_requires_decimal_amount():
    with pytest.raises(TypeError):
        WalletService.top_up(user=None, amount=100)


@pytest.mark.django_db
def test_top_up_rejects_amount_above_per_transaction_limit():
    user = create_user("wallet-per-limit")

    with pytest.raises(ValueError):
        WalletService.top_up(user=user, amount=MAX_PER_TRANSACTION + Decimal("0.01"))

    assert not Wallet.objects.filter(user=user).exists()


@pytest.mark.django_db
def test_top_up_rejects_result_above_max_allowed_balance():
    user = create_user("wallet-balance-limit")
    wallet = Wallet.objects.create(user=user, balance=MAX_ALLOWED_BALANCE)

    with pytest.raises(ValueError):
        WalletService.top_up(user=user, amount=Decimal("0.01"))

    wallet.refresh_from_db()
    assert wallet.balance == MAX_ALLOWED_BALANCE
    assert wallet.transactions.count() == 0


@pytest.mark.django_db
def test_wallet_page_requires_login(client):
    response = client.get(reverse("wallet:detail"))

    assert response.status_code == 302
    assert reverse("accounts:login") in response.url


@pytest.mark.django_db
def test_wallet_page_post_top_up_updates_balance(client):
    user = create_user("wallet-post")
    client.force_login(user)

    response = client.post(reverse("wallet:detail"), {"amount": "150000.00"})

    assert response.status_code == 302
    assert user.wallet.balance == Decimal("150000.00")


@pytest.mark.django_db
def test_wallet_page_rejects_absurd_amount_with_inline_error(client):
    user = create_user("wallet-huge")
    client.force_login(user)

    response = client.post(reverse("wallet:detail"), {"amount": "99999999999999"})

    assert response.status_code == 200
    assert user.wallet.balance == Decimal("0.00")
    html = response.content.decode("utf-8")
    assert "بیش از حد مجاز" in html


@pytest.mark.django_db
def test_wallet_page_rejects_invalid_amount_without_balance_change(client):
    user = create_user("wallet-invalid")
    client.force_login(user)

    response = client.post(reverse("wallet:detail"), {"amount": "abc"})

    assert response.status_code == 200
    assert user.wallet.balance == Decimal("0.00")
    assert "مبلغ وارد شده معتبر نیست" in response.content.decode("utf-8")


@pytest.mark.django_db
@pytest.mark.skipif(connection.vendor != "sqlite", reason="SQLite lacks numeric enforcement")
def test_wallet_page_repairs_oversized_legacy_balance(client):
    user = create_user("wallet-repair")
    client.force_login(user)
    wallet = Wallet.objects.create(user=user, balance=Decimal("0.00"))

    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE wallet_wallet SET balance = 99999999999999 WHERE id = %s",
            [wallet.pk],
        )

    response = client.get(reverse("wallet:detail"))

    assert response.status_code == 200
    assert Wallet.objects.get(pk=wallet.pk).balance == Decimal("0.00")
