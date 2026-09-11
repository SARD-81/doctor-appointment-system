from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class Wallet(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wallet",
        verbose_name="User",
    )
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Balance",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Wallet"
        verbose_name_plural = "Wallets"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(balance__gte=0),
                name="wallet_balance_gte_zero",
            )
        ]

    def __str__(self):
        return f"Wallet for {self.user} ({self.balance})"


class WalletTransaction(models.Model):
    class TransactionType(models.TextChoices):
        TOP_UP = "TOP_UP", "Top Up"
        APPOINTMENT_PAYMENT = "APPOINTMENT_PAYMENT", "Appointment Payment"

    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name="transactions",
        verbose_name="Wallet",
    )
    # Optional link to Appointment for payment tracing and audit trail.
    # Uses lazy reference 'appointments.Appointment' to prevent circular dependencies.
    # Set to null on delete to preserve financial transaction history
    # even if the appointment is removed.
    appointment = models.ForeignKey(
        "appointments.Appointment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="wallet_transactions",
        verbose_name="Appointment",
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Amount",
    )
    transaction_type = models.CharField(
        max_length=25,
        choices=TransactionType.choices,
        verbose_name="Transaction Type",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Wallet Transaction"
        verbose_name_plural = "Wallet Transactions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["wallet", "created_at"]),
            models.Index(fields=["appointment"]),
        ]
        # Enforces the payment-trace contract at the DB level as well:
        # TOP_UP must never carry an appointment reference, and
        # APPOINTMENT_PAYMENT must always carry one.
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(
                        transaction_type="TOP_UP",
                        appointment__isnull=True,
                    )
                    | models.Q(
                        transaction_type="APPOINTMENT_PAYMENT",
                        appointment__isnull=False,
                    )
                ),
                name="wallet_transaction_appointment_rule",
            ),
        ]

    def clean(self):
        super().clean()
        if self.transaction_type == self.TransactionType.TOP_UP and self.appointment_id:
            raise ValidationError(
                {"appointment": "TOP_UP transactions not linked to an Appointment."}
            )
        if (
            self.transaction_type == self.TransactionType.APPOINTMENT_PAYMENT
            and not self.appointment_id
        ):
            raise ValidationError(
                {"appointment": "APPOINTMENT_PAYMENT transactions linked to an Appointment."}
            )

    def __str__(self):
        return f"{self.transaction_type} - {self.amount} ({self.wallet.user})"
