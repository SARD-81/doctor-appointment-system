from django.db import IntegrityError, transaction

from apps.appointments.models import Appointment, AppointmentStatus
from apps.reviews.exceptions import (
    AppointmentNotCompletedError,
    ReviewAlreadyExistsError,
    ReviewOwnershipError,
)
from apps.reviews.models import Review


class ReviewService:
    """نقطه ورود دامنه‌ای ثبت نظر.

    قواعد مالکیت، وضعیت تکمیل و جلوگیری از تکرار فقط در همین لایه enforce می‌شوند؛
    ردیف appointment داخل تراکنش با SELECT FOR UPDATE قفل می‌شود تا در race
    هم‌زمان، فقط یک Review ثبت شود و برخورد دیتابیسی نیز به خطای دامنه‌ای ترجمه شود.
    """

    @staticmethod
    def create_review(*, patient, appointment_id: int, rating: int, comment: str = "") -> Review:
        if patient is None:
            raise TypeError("Patient is required")
        if appointment_id is None:
            raise TypeError("appointment_id is required")

        with transaction.atomic():
            appointment = (
                Appointment.objects.select_for_update()
                .filter(pk=appointment_id, patient=patient)
                .first()
            )
            if appointment is None:
                # بدون افشای این‌که چنین نوبتی برای کاربر دیگری وجود دارد یا نه
                raise ReviewOwnershipError(
                    "No appointment exists for this patient with the given id."
                )
            if appointment.status != AppointmentStatus.COMPLETED:
                raise AppointmentNotCompletedError(
                    "Reviews are only allowed for COMPLETED appointments."
                )
            if hasattr(appointment, "review"):
                raise ReviewAlreadyExistsError("This appointment already has a review.")

            review = Review(
                appointment=appointment,
                rating=rating,
                comment=comment or "",
            )
            review.full_clean()
            try:
                review.save()
            except IntegrityError as exc:
                # خط دفاع دوم: اگر دو تراکنش هم‌زمان از قفل عبور کنند، OneToOne جلوگیری می‌کند
                raise ReviewAlreadyExistsError("This appointment already has a review.") from exc

        return review
