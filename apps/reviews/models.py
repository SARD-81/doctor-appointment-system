from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.appointments.models import Appointment


class Review(models.Model):
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name="review",
        verbose_name="Appointment",
    )
    rating = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5),
        ],
        verbose_name="Rating",
    )
    comment = models.TextField(
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
        ordering = ("-created_at",)
        constraints = [
            models.CheckConstraint(
                condition=models.Q(rating__gte=1, rating__lte=5),
                name="reviews_review_rating_between_1_5",
            ),
        ]

    def __str__(self):
        return f"Review for {self.appointment} ({self.rating}/5)"
