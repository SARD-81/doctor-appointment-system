from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.wallet.models import Wallet, WalletTransaction

User = get_user_model()


@pytest.fixture
def patient(db):
    return User.objects.create_user(
        username="wallet_page_user",
        email="wallet-page@example.com",
        password="StrongPass123!",
    )


@pytest.fixture
def funded_wallet(db, patient):
    return Wallet.objects.create(user=patient, balance=Decimal("751002.00"))


@pytest.mark.django_db
class TestWalletPage:
    def test_wallet_page_requires_login(self, client):
        response = client.get(reverse("wallet:detail"))
        assert response.status_code == 302

    def test_wallet_page_renders_balance_and_persian_labels(self, client, funded_wallet):
        WalletTransaction.objects.create(
            wallet=funded_wallet,
            transaction_type=WalletTransaction.TOP_UP,
            amount=Decimal("751002.00"),
            balance_after=Decimal("751002.00"),
        )
        client.force_login(funded_wallet.user)

        response = client.get(reverse("wallet:detail"))
        html = response.content.decode("utf-8")

        assert response.status_code == 200
        assert "751002.00" in html
        assert "موجودی فعلی" in html
        assert "شارژ کیف پول" in html
        assert "TOP_UP" not in html

    def test_preset_chip_posts_top_up_directly(self, client, funded_wallet):
        client.force_login(funded_wallet.user)

        response = client.post(reverse("wallet:detail"), {"amount": "100000"})

        assert response.status_code == 302
        funded_wallet.refresh_from_db()
        assert funded_wallet.balance == Decimal("851002.00")
        tx = funded_wallet.transactions.order_by("-created_at").first()
        assert tx is not None and tx.transaction_type == WalletTransaction.TOP_UP
        assert tx.amount == Decimal("100000")
        assert tx.balance_after == Decimal("851002.00")
