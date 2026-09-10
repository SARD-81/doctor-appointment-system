from django.shortcuts import render

from apps.doctors.models import Doctor, Specialty


def _format_visit_fee(amount):
    return f"{amount:,.0f} تومان"


def _doctor_card_data(doctor):
    return {
        "name": doctor.full_name,
        "specialty": doctor.specialty.name,
        "fee": _format_visit_fee(doctor.visit_fee),
        "initials": doctor.full_name[:1] or "د",
    }


def doctor_list_view(request):
    query = request.GET.get("q", "").strip()
    raw_specialty = request.GET.get("specialty", "").strip()

    doctors = Doctor.objects.filter(is_active=True).select_related("specialty")
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
