from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import ProtectedError
from django.db.utils import IntegrityError
from django.test import TestCase
from django.utils import timezone

from apps.appointments.models import Appointment, AppointmentSlot
from apps.doctors.models import Doctor, Specialty

User = get_user_model()


class AppointmentSlotModelTest(TestCase):
    def setUp(self):
        self.specialty = Specialty.objects.create(name="قلب و عروق")
        self.doctor = Doctor.objects.create(
            specialty=self.specialty,
            full_name="دکتر محمدی",
            visit_fee=Decimal("150000.00"),
        )
        self.starts_at = timezone.now() + timedelta(days=1)

    def test_create_appointment_slot_success(self):
        slot = AppointmentSlot.objects.create(
            doctor=self.doctor,
            starts_at=self.starts_at,
        )
        self.assertEqual(str(slot), f"{self.doctor} @ {slot.starts_at}")
        self.assertTrue(slot.is_active)

    def test_slot_default_is_active_true(self):
        slot = AppointmentSlot.objects.create(
            doctor=self.doctor,
            starts_at=self.starts_at,
        )
        self.assertTrue(slot.is_active)

    def test_unique_slot_per_doctor_time_constraint(self):
        AppointmentSlot.objects.create(
            doctor=self.doctor,
            starts_at=self.starts_at,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                AppointmentSlot.objects.create(
                    doctor=self.doctor,
                    starts_at=self.starts_at,
                )

    def test_same_time_different_doctor_allowed(self):
        other_doctor = Doctor.objects.create(
            specialty=self.specialty,
            full_name="دکتر حسینی",
            visit_fee=Decimal("100000.00"),
        )
        AppointmentSlot.objects.create(
            doctor=self.doctor,
            starts_at=self.starts_at,
        )
        second_slot = AppointmentSlot.objects.create(
            doctor=other_doctor,
            starts_at=self.starts_at,
        )
        self.assertIsNotNone(second_slot.id)

    def test_ordering_by_starts_at(self):
        later_slot = AppointmentSlot.objects.create(
            doctor=self.doctor,
            starts_at=self.starts_at + timedelta(days=2),
        )
        earlier_slot = AppointmentSlot.objects.create(
            doctor=self.doctor,
            starts_at=self.starts_at,
        )
        slots = list(AppointmentSlot.objects.all())
        self.assertEqual(slots, [earlier_slot, later_slot])

    def test_deleting_doctor_cascades_to_slot(self):
        slot = AppointmentSlot.objects.create(
            doctor=self.doctor,
            starts_at=self.starts_at,
        )
        slot_id = slot.id
        self.doctor.delete()
        self.assertFalse(AppointmentSlot.objects.filter(id=slot_id).exists())


class AppointmentModelTest(TestCase):
    def setUp(self):
        self.specialty = Specialty.objects.create(name="اطفال")
        self.doctor = Doctor.objects.create(
            specialty=self.specialty,
            full_name="دکتر کریمی",
            visit_fee=Decimal("120000.00"),
        )
        self.patient = User.objects.create_user(
            username="patient1",
            email="patient1@example.com",
            password="testpass123",
        )
        self.slot = AppointmentSlot.objects.create(
            doctor=self.doctor,
            starts_at=timezone.now() + timedelta(days=1),
        )

    def test_create_appointment_success(self):
        appointment = Appointment.objects.create(
            patient=self.patient,
            slot=self.slot,
            amount_paid=Decimal("120000.00"),
        )
        self.assertEqual(
            str(appointment),
            f"Appointment #{appointment.id} - {self.patient}",
        )

    def test_appointment_default_status_confirmed(self):
        appointment = Appointment.objects.create(
            patient=self.patient,
            slot=self.slot,
            amount_paid=Decimal("120000.00"),
        )
        self.assertEqual(appointment.status, Appointment.Status.CONFIRMED)

    def test_appointment_completed_fields_default_none(self):
        appointment = Appointment.objects.create(
            patient=self.patient,
            slot=self.slot,
            amount_paid=Decimal("120000.00"),
        )
        self.assertIsNone(appointment.completed_at)
        self.assertIsNone(appointment.completed_by)

    def test_amount_paid_negative_constraint(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Appointment.objects.create(
                    patient=self.patient,
                    slot=self.slot,
                    amount_paid=Decimal("-50000.00"),
                )

    def test_unique_appointment_per_slot_constraint(self):
        Appointment.objects.create(
            patient=self.patient,
            slot=self.slot,
            amount_paid=Decimal("120000.00"),
        )
        other_patient = User.objects.create_user(
            username="patient2",
            email="patient2@example.com",
            password="testpass123",
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Appointment.objects.create(
                    patient=other_patient,
                    slot=self.slot,
                    amount_paid=Decimal("120000.00"),
                )

    def test_mark_appointment_completed(self):
        staff_user = User.objects.create_user(
            username="staff1",
            email="staff1@example.com",
            password="testpass123",
            is_staff=True,
        )
        appointment = Appointment.objects.create(
            patient=self.patient,
            slot=self.slot,
            amount_paid=Decimal("120000.00"),
        )
        appointment.status = Appointment.Status.COMPLETED
        appointment.completed_at = timezone.now()
        appointment.completed_by = staff_user
        appointment.save()

        appointment.refresh_from_db()
        self.assertEqual(appointment.status, Appointment.Status.COMPLETED)
        self.assertIsNotNone(appointment.completed_at)
        self.assertEqual(appointment.completed_by, staff_user)

    def test_deleting_completed_by_user_sets_null(self):
        staff_user = User.objects.create_user(
            username="staff2",
            email="staff2@example.com",
            password="testpass123",
            is_staff=True,
        )
        appointment = Appointment.objects.create(
            patient=self.patient,
            slot=self.slot,
            amount_paid=Decimal("120000.00"),
            completed_by=staff_user,
        )
        staff_user.delete()
        appointment.refresh_from_db()
        self.assertIsNone(appointment.completed_by)

    def test_deleting_patient_is_protected(self):
        Appointment.objects.create(
            patient=self.patient,
            slot=self.slot,
            amount_paid=Decimal("120000.00"),
        )
        with self.assertRaises(ProtectedError):
            self.patient.delete()

    def test_deleting_slot_with_appointment_is_protected(self):
        Appointment.objects.create(
            patient=self.patient,
            slot=self.slot,
            amount_paid=Decimal("120000.00"),
        )
        with self.assertRaises(ProtectedError):
            self.slot.delete()

    def test_ordering_by_booked_at_descending(self):
        # نوبت‌ها باید بر اساس زمان رزرو نزولی مرتب شوند
        other_patient = User.objects.create_user(
            username="patient3",
            email="patient3@example.com",
            password="testpass123",
        )
        other_slot = AppointmentSlot.objects.create(
            doctor=self.doctor,
            starts_at=timezone.now() + timedelta(days=2),
        )

        first_time = timezone.now() - timedelta(minutes=2)
        second_time = timezone.now() - timedelta(minutes=1)

        first_appointment = Appointment.objects.create(
            patient=self.patient,
            slot=self.slot,
            amount_paid=Decimal("120000.00"),
        )
        second_appointment = Appointment.objects.create(
            patient=other_patient,
            slot=other_slot,
            amount_paid=Decimal("100000.00"),
        )

        Appointment.objects.filter(pk=first_appointment.pk).update(booked_at=first_time)
        Appointment.objects.filter(pk=second_appointment.pk).update(booked_at=second_time)

        appointments = list(Appointment.objects.all())
        self.assertEqual(appointments, [second_appointment, first_appointment])
