from django.utils import timezone

from apps.appointments.models import AppointmentSlot


def available_slots_for_doctor(doctor, *, at=None):
    """Return selectable slots for an active doctor at a point in time.

    Availability for the patient-facing surface means the slot is active,
    starts in the future, and has no Appointment linked to it.
    """
    reference_time = at or timezone.now()
    return (
        AppointmentSlot.objects.filter(
            doctor=doctor,
            is_active=True,
            starts_at__gt=reference_time,
            appointment__isnull=True,
        )
        .select_related("doctor")
        .order_by("starts_at", "pk")
    )
