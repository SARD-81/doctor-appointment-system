from decimal import Decimal

from django import forms

from apps.wallet.services import MAX_WALLET_BALANCE


class TopUpForm(forms.Form):
    amount = forms.DecimalField(
        min_value=Decimal("0.01"),
        max_value=MAX_WALLET_BALANCE,
        max_digits=12,
        decimal_places=2,
        label="مبلغ افزایش موجودی",
        widget=forms.NumberInput(
            attrs={
                "id": "topup-amount",
                "step": "0.01",
                "min": "0.01",
                "placeholder": "مبلغ دلخواه (تومان)",
                "inputmode": "decimal",
            }
        ),
    )
