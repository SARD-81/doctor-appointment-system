from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.appointments.exceptions import InsufficientBalanceError, SlotUnavailableError
from apps.appointments.models import Appointment, AppointmentSlot
from apps.appointments.services import BookingService


@login_required
def book_appointment_view(request, slot_id: int):
    """POST-only booking endpoint with Post/Redirect/Get pattern."""
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

    return redirect("appointments:booking_success", appointment_id=appointment.pk)


@login_required
def booking_success_view(request, appointment_id: int):
    """Dedicated GET page; only the booking owner may view it."""
    appointment = get_object_or_404(
        Appointment.objects.select_related("slot__doctor__specialty"),
        pk=appointment_id,
        patient=request.user,
    )
    return render(
        request,
        "appointments/booking_success.html",
        {"appointment": appointment},
    )


@login_required
def my_appointments_view(request):
    """Render only the appointments owned by the authenticated patient."""
    appointments = (
        Appointment.objects.filter(patient=request.user)
        .select_related("slot__doctor__specialty")
        .order_by("-slot__starts_at", "pk")
    )
    return render(
        request,
        "appointments/my_appointments.html",
        {"appointments": appointments},
    )
