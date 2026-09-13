from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.appointments.exceptions import InsufficientBalanceError, SlotUnavailableError
from apps.appointments.models import AppointmentSlot
from apps.appointments.services import BookingService


@login_required
def book_appointment_view(request, slot_id: int):
    """POST-only booking endpoint; GET/HEAD safely redirect to the doctor page."""
    slot = get_object_or_404(AppointmentSlot.objects.select_related("doctor"), pk=slot_id)

    if request.method != "POST":
        return redirect("doctors:detail", doctor_id=slot.doctor.pk)

    try:
        appointment = BookingService.book_appointment(patient=request.user, slot_id=slot_id)
    except SlotUnavailableError:
        messages.error(
            request,
            "این زمان دیگر در دسترس نیست. لطفاً یکی از نوبت‌های آزاد را انتخاب کنید.",
        )
        return redirect("doctors:detail", doctor_id=slot.doctor.pk)
    except InsufficientBalanceError:
        messages.error(
            request,
            "موجودی کیف پول برای پرداخت هزینه این ویزیت کافی نیست.",
        )
        return redirect("wallet:detail")

    return render(
        request,
        "appointments/booking_success.html",
        {"appointment": appointment},
    )
