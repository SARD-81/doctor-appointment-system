from datetime import datetime, time, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.appointments.models import AppointmentSlot
from apps.doctors.models import Doctor, Specialty


class Command(BaseCommand):
    help = "Create deterministic demo data for local development."

    def handle(self, *args, **options):
        if not settings.ALLOW_DEMO_DATA:
            raise CommandError("seed_demo_data is disabled in this environment.")

        specialties = [
            "Cardiology",
            "Dermatology",
            "Orthopedics",
        ]

        created_specialties = [
            Specialty.objects.get_or_create(name=name)[0] for name in specialties
        ]

        doctors = [
            ("Dr. Ali Ahmadi", created_specialties[0]),
            ("Dr. Sara Mohammadi", created_specialties[1]),
            ("Dr. Reza Karimi", created_specialties[2]),
        ]

        created_doctors = [
            Doctor.objects.get_or_create(
                full_name=name,
                specialty=specialty,
                defaults={
                    "visit_fee": Decimal("250000.00"),
                    "is_active": True,
                },
            )[0]
            for name, specialty in doctors
        ]

        local_today = timezone.localdate()
        current_timezone = timezone.get_current_timezone()
        slot_times = (
            (local_today + timedelta(days=1), time(hour=9), True),
            (local_today - timedelta(days=1), time(hour=9), True),
            (local_today + timedelta(days=2), time(hour=14), False),
        )
        for doctor in created_doctors:
            for slot_date, slot_time, is_active in slot_times:
                starts_at = timezone.make_aware(
                    datetime.combine(slot_date, slot_time),
                    current_timezone,
                )
                AppointmentSlot.objects.update_or_create(
                    doctor=doctor,
                    starts_at=starts_at,
                    defaults={"is_active": is_active},
                )

        self.stdout.write(self.style.SUCCESS("Demo data created successfully."))
