from django.core.management import call_command

from apps.appointments.models import AppointmentSlot
from apps.doctors.models import Doctor, Specialty


def test_seed_demo_data_creates_records(db):
    call_command("seed_demo_data")

    assert Specialty.objects.exists()
    assert Doctor.objects.exists()
    assert AppointmentSlot.objects.exists()


def test_seed_demo_data_is_idempotent(db):
    call_command("seed_demo_data")
    first_count = Doctor.objects.count()

    call_command("seed_demo_data")

    assert Doctor.objects.count() == first_count
