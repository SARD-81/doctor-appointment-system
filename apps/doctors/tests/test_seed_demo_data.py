import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

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
    first_slot_count = AppointmentSlot.objects.count()

    call_command("seed_demo_data")

    assert Doctor.objects.count() == first_count
    assert AppointmentSlot.objects.count() == first_slot_count


@pytest.mark.django_db
@override_settings(ALLOW_DEMO_DATA=False)
def test_seed_demo_data_is_blocked_in_production():
    with pytest.raises(CommandError, match="disabled"):
        call_command("seed_demo_data")
