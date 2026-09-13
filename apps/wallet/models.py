from decimal import Decimal

from django.conf import settings
from django.db import models


class Wallet(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wallet"
    )
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(balance__gte=0), name="wallet_balance_gte_zero"
            )
        ]


class WalletTransaction(models.Model):
    TOP_UP = "TOP_UP"
    APPOINTMENT_PAYMENT = "APPOINTMENT_PAYMENT"
    TRANSACTION_TYPES = [
        (TOP_UP, "Top Up"),
        (APPOINTMENT_PAYMENT, "Appointment Payment"),
    ]

    wallet = models.ForeignKey(
        Wallet, on_delete=models.CASCADE, related_name="transactions"
    )
    appointment = models.ForeignKey(
        "appointments.Appointment",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    transaction_type = models.CharField(max_length=32, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name="wallet_transaction_amount_gt_zero",
            )
        ]
