from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from apps.appointments.selectors import available_slots_for_doctor
from apps.doctors.models import Doctor, Specialty


def _format_visit_fee(amount):
    formatted_amount = f"{amount:,.2f}"
    if formatted_amount.endswith(".00"):
        formatted_amount = formatted_amount[:-3]
    return f"{formatted_amount} تومان"


def _format_average_rating(value):
    """میانگین امتیاز با یک رقم اعشار؛ بدون نظر یعنی نمایش nothing."""
    if value is None:
        return None
    return f"{value:.1f}"


def _with_rating_aggregates(queryset):
    """میانگین امتیاز و تعداد نظر هر پزشک را در یک کوئری annotation می‌کند."""
    return queryset.annotate(
        average_rating=Avg("slots__appointment__review__rating"),
        review_count=Count("slots__appointment__review"),
    )


def _doctor_card_data(doctor):
    return {
        "name": doctor.full_name,
        "specialty": doctor.specialty.name,
        "fee": _format_visit_fee(doctor.visit_fee),
        "initials": doctor.full_name[:1] or "د",
        "profile_url": reverse("doctors:detail", args=[doctor.pk]),
        "rating": _format_average_rating(doctor.average_rating),
        "reviews_count": doctor.review_count,
    }


def doctor_list_view(request):
    query = request.GET.get("q", "").replace("\x00", "").strip()
    raw_specialty = request.GET.get("specialty", "").strip()

    doctors = _with_rating_aggregates(
        Doctor.objects.filter(is_active=True).select_related("specialty")
    )
    specialties = Specialty.objects.all()

    if query:
        doctors = doctors.filter(full_name__icontains=query)

    selected_specialty_id = None
    specialty_filter_invalid = False

    if raw_specialty:
        try:
            specialty_id = int(raw_specialty)
        except (TypeError, ValueError):
            specialty_filter_invalid = True
        else:
            selected_specialty = specialties.filter(pk=specialty_id).first()
            if selected_specialty is None:
                specialty_filter_invalid = True
            else:
                selected_specialty_id = selected_specialty.pk
                doctors = doctors.filter(specialty_id=selected_specialty.pk)

    doctors = list(doctors.order_by("full_name", "pk"))
    doctor_cards = [_doctor_card_data(doctor) for doctor in doctors]

    return render(
        request,
        "doctors/doctor_list.html",
        {
            "doctor_cards": doctor_cards,
            "specialties": specialties,
            "query": query,
            "selected_specialty_id": selected_specialty_id,
            "specialty_filter_invalid": specialty_filter_invalid,
            "has_filters": bool(query or raw_specialty),
            "result_count": len(doctor_cards),
        },
    )


def doctor_detail_view(request, doctor_id):
    doctor = get_object_or_404(
        _with_rating_aggregates(Doctor.objects.select_related("specialty")),
        pk=doctor_id,
        is_active=True,
    )
    available_slots = available_slots_for_doctor(doctor)

    selected_slot = None
    selected_slot_invalid = False
    raw_slot = request.GET.get("slot", "").strip()

    if raw_slot:
        try:
            slot_id = int(raw_slot)
        except (TypeError, ValueError):
            selected_slot_invalid = True
        else:
            selected_slot = available_slots.filter(pk=slot_id).first()
            if selected_slot is None:
                selected_slot_invalid = True

    slots = list(available_slots)

    return render(
        request,
        "doctors/doctor_detail.html",
        {
            "doctor": doctor,
            "visit_fee": _format_visit_fee(doctor.visit_fee),
            "average_rating": _format_average_rating(doctor.average_rating),
            "review_count": doctor.review_count,
            "slots": slots,
            "selected_slot": selected_slot,
            "selected_slot_id": selected_slot.pk if selected_slot else None,
            "selected_slot_invalid": selected_slot_invalid,
        },
    )
