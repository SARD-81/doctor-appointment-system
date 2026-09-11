from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import CheckConstraint, Q, UniqueConstraint
from django.utils.translation import gettext_lazy as _


class AppointmentStatus(models.TextChoices):
    """وضعیت‌های پایه چرخه حیات نوبت بر اساس معماری پروژه."""

    CONFIRMED = "CONFIRMED", _("Confirmed")
    COMPLETED = "COMPLETED", _("Completed")


class AppointmentSlot(models.Model):
    """مدل بازه‌های زمانی قابل رزرو برای پزشکان."""

    doctor = models.ForeignKey(
        "doctors.Doctor",
        on_delete=models.CASCADE,
        related_name="slots",
        verbose_name=_("Doctor"),
    )
    starts_at = models.DateTimeField(_("Starts at"))
    is_active = models.BooleanField(_("Is active"), default=True)
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)

    class Meta:
        verbose_name = _("Appointment Slot")
        verbose_name_plural = _("Appointment Slots")
        ordering = ["starts_at"]
        constraints = [
            # جلوگیری از ثبت زمان تکراری برای یک پزشک در سطح دیتابیس
            UniqueConstraint(
                fields=["doctor", "starts_at"],
                name="unique_doctor_starts_at",
            )
        ]

    def __str__(self) -> str:
        return f"{self.doctor} - {self.starts_at.strftime('%Y-%m-%d %H:%M')}"

    @property
    def is_available(self) -> bool:
        """بررسی داینامیک در دسترس بودن اسلات بدون نیاز به فیلد اضافی در دیتابیس."""
        if not self.is_active:
            return False
        return not hasattr(self, "appointment")


class Appointment(models.Model):
    """مدل ثبت نوبت رزرو شده بیمار به همراه لاگ تکمیل و بازرسی."""

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="appointments",
        verbose_name=_("Patient"),
    )
    slot = models.OneToOneField(
        AppointmentSlot,
        on_delete=models.CASCADE,
        related_name="appointment",
        verbose_name=_("Slot"),
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=AppointmentStatus.choices,
        default=AppointmentStatus.CONFIRMED,
    )
    amount_paid = models.DecimalField(
        _("Amount paid"),
        max_digits=10,
        decimal_places=2,
    )
    booked_at = models.DateTimeField(_("Booked at"), auto_now_add=True)
    completed_at = models.DateTimeField(
        _("Completed at"),
        null=True,
        blank=True,
    )
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="completed_appointments",
        verbose_name=_("Completed by"),
    )

    class Meta:
        verbose_name = _("Appointment")
        verbose_name_plural = _("Appointments")
        ordering = ["-booked_at"]
        constraints = [
            # قید دیتابیسی مدرن برای تضمین عدم ثبت مبلغ منفی
            CheckConstraint(
                condition=Q(amount_paid__gte=Decimal("0.00")),
                name="appointment_amount_paid_non_negative",
            )
        ]

    def clean(self) -> None:
        """اعتبارسنجی سطح مدل برای فرم‌ها و ادمین جنگو."""
        super().clean()
        if self.amount_paid is not None and self.amount_paid < Decimal("0.00"):
            raise ValidationError({"amount_paid": _("Amount paid cannot be negative.")})

    def __str__(self) -> str:
        return f"Appointment #{self.pk} - {self.patient} ({self.status})"
