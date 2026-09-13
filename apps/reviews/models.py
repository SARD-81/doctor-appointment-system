from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class Review(models.Model):
    """نظر و امتیاز بیمار برای یک نوبت؛ بر اساس ADR-008 حداکثر یک Review برای هر Appointment."""

    appointment = models.OneToOneField(
        "appointments.Appointment",
        on_delete=models.CASCADE,
        related_name="review",
        verbose_name=_("Appointment"),
    )
    rating = models.PositiveSmallIntegerField(
        _("Rating"),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    comment = models.TextField(_("Comment"), blank=True, default="")
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)

    class Meta:
        verbose_name = _("Review")
        verbose_name_plural = _("Reviews")
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(rating__gte=1, rating__lte=5),
                name="review_rating_between_1_and_5",
            ),
        ]

    def __str__(self) -> str:
        return f"Review #{self.pk} - Appointment {self.appointment_id} ({self.rating}/5)"
