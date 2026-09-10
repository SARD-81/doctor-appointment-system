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
            
        ]

    def __str__(self):
        return f"Dr. {self.full_name} - {self.specialty.name}"

