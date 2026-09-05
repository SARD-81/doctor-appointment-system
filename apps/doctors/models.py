from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db import models


class Specialty(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Name",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At",
    )

    class Meta:
        verbose_name = "Specialty"
        verbose_name_plural = "Specialties"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Doctor(models.Model):
    specialty = models.ForeignKey(
        Specialty,
        on_delete=models.PROTECT,
        related_name="doctors",
        verbose_name="Specialty",
    )
    full_name = models.CharField(
        max_length=255,
        verbose_name="Full Name",
    )
    visit_fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Visit Fee",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Is Active",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated At",
    )

    class Meta:
        verbose_name = "Doctor"
        verbose_name_plural = "Doctors"

        indexes = [
            models.Index(fields=["specialty", "is_active"]),
        ]

        constraints = [
            models.CheckConstraint(
                condition=models.Q(visit_fee__gte=0),
                name="doctor_visit_fee_gte_zero",
            ),
            models.UniqueConstraint(
                fields=["full_name", "specialty"],
                name="unique_doctor_per_specialty",
            ),
        ]

    def __str__(self):
        return f"Dr. {self.full_name} - {self.specialty.name}"

class AppointmentSlot(models.Model):
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name="slots",
        verbose_name="Doctor",
    )
    starts_at = models.DateTimeField(
        verbose_name="Starts At",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Is Active",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At",
    )

    class Meta:
        verbose_name = "Appointment Slot"
        verbose_name_plural = "Appointment Slots"
        ordering = ["starts_at"]
        indexes = [
            models.Index(fields=["doctor", "starts_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["doctor", "starts_at"],
                name="unique_slot_per_doctor_time",
            )
        ]

    def __str__(self):
        return f"{self.doctor} @ {self.starts_at}"

from django.conf import settings


class Appointment(models.Model):
    class Status(models.TextChoices):
        CONFIRMED = "CONFIRMED", "Confirmed"
        COMPLETED = "COMPLETED", "Completed"

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="appointments",
        verbose_name="Patient",
    )
    slot = models.OneToOneField(
        AppointmentSlot,
        on_delete=models.PROTECT,
        related_name="appointment",
        verbose_name="Slot",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CONFIRMED,
        verbose_name="Status",
    )
    amount_paid = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Amount Paid",
    )
    booked_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Booked At",
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Completed At",
    )
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="completed_appointments",
        verbose_name="Completed By",
    )

    class Meta:
        verbose_name = "Appointment"
        verbose_name_plural = "Appointments"
        ordering = ["-booked_at"]
        indexes = [
            models.Index(fields=["patient", "status"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount_paid__gte=0),
                name="appointment_amount_paid_gte_zero",
            )
        ]

    def __str__(self):
        return f"Appointment #{self.id} - {self.patient}"

from django.core.validators import MaxValueValidator


class Review(models.Model):
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name="review",
        verbose_name="Appointment",
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Rating",
    )
    comment = models.TextField(
        null=True,
        blank=True,
        verbose_name="Comment",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated At",
    )

    class Meta:
        verbose_name = "Review"
        verbose_name_plural = "Reviews"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(rating__gte=1) & models.Q(rating__lte=5),
                name="review_rating_between_1_5",
            )
        ]

    def __str__(self):
        return f"Review for {self.appointment} ({self.rating}/5)"

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
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated At",
    )

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
        return f"Wallet of {self.user}"
class WalletTransaction(models.Model):
    class TransactionType(models.TextChoices):
        TOP_UP = "TOP_UP", "Top Up"
        PAYMENT = "PAYMENT", "Payment"

    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.PROTECT,
        related_name="transactions",
        verbose_name="Wallet",
    )
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="wallet_transactions",
        verbose_name="Appointment",
    )
    type = models.CharField(
        max_length=10,
        choices=TransactionType.choices,
        verbose_name="Type",
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Amount",
    )
    balance_after = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Balance After",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At",
    )

    class Meta:
        verbose_name = "Wallet Transaction"
        verbose_name_plural = "Wallet Transactions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["wallet", "created_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name="wallettransaction_amount_gt_zero",
            ),
            models.CheckConstraint(
                condition=models.Q(balance_after__gte=0),
                name="wallettransaction_balance_after_gte_zero",
            ),
        ]

    def __str__(self):
        return f"{self.type} {self.amount} -> {self.wallet}"
