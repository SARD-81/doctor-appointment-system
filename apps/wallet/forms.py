from decimal import Decimal

from django import forms

from .services import MAX_PER_TRANSACTION


class TopUpForm(forms.Form):
    amount = forms.DecimalField(
        label="مبلغ افزایش موجودی (تومان)",
        min_value=Decimal("0.01"),
        max_value=MAX_PER_TRANSACTION,
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={
                "step": "0.01",
                "inputmode": "decimal",
                "dir": "ltr",
                "placeholder": "مثلاً 250000",
            }
        ),
        error_messages={
            "required": "مبلغ را وارد کنید.",
            "invalid": "مبلغ وارد شده معتبر نیست.",
            "min_value": "مبلغ باید بزرگ‌تر از صفر باشد.",
            "max_value": "مبلغ از سقف مجاز هر تراکنش بیشتر است.",
            "max_digits": "تعداد ارقام مبلغ بیش از حد مجاز است.",
            "max_decimal_places": "حداکثر دو رقم اعشار مجاز است.",
        },
    )
