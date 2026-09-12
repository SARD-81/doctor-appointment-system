from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.appointments.models import AppointmentSlot
from apps.doctors.models import Doctor, Specialty


class Command(BaseCommand):
    help = "Create deterministic demo data for local development."

    def handle(self, *args, **options):
        specialties = [
            "Cardiology",
            "Dermatology",
            "Orthopedics",
        ]

        created_specialties = [
            Specialty.objects.get_or_create(name=name)[0]
            for name in specialties
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

        now = timezone.now()
        for doctor in created_doctors:
            AppointmentSlot.objects.get_or_create(
                doctor=doctor,
                starts_at=now + timedelta(days=1),
                defaults={"is_active": True},
            )
            AppointmentSlot.objects.get_or_create(
                doctor=doctor,
                starts_at=now - timedelta(days=1),
                defaults={"is_active": True},
            )
            AppointmentSlot.objects.get_or_create(
                doctor=doctor,
                starts_at=now + timedelta(days=2),
                defaults={"is_active": False},
            )

        self.stdout.write(self.style.SUCCESS("Demo data created successfully."))
