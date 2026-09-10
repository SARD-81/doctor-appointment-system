from decimal import Decimal

from django.db.models import ProtectedError
from django.db.utils import IntegrityError
from django.test import TestCase

from apps.doctors.models import Doctor, Specialty


class SpecialtyModelTest(TestCase):
    def test_create_specialty_success(self):
        specialty = Specialty.objects.create(name="قلب و عروق")
        self.assertEqual(str(specialty), "قلب و عروق")

    def test_specialty_name_unique(self):
        Specialty.objects.create(name="چشم‌پزشکی")
        with self.assertRaises(IntegrityError):
            Specialty.objects.create(name="چشم‌پزشکی")


class DoctorModelTest(TestCase):
    def setUp(self):
        self.specialty = Specialty.objects.create(name="عمومی")

    def test_create_doctor_success(self):
        doctor = Doctor.objects.create(
            specialty=self.specialty,
            full_name="علی رضایی",
            visit_fee=Decimal("150000.00"),
        )
        self.assertEqual(str(doctor), f"Dr. علی رضایی - {self.specialty.name}")
        self.assertTrue(doctor.is_active)

    def test_doctor_visit_fee_negative_constraint(self):
        with self.assertRaises(IntegrityError):
            Doctor.objects.create(
                specialty=self.specialty,
                full_name="پزشک تستی",
                visit_fee=Decimal("-1000.00"),
            )

    def test_doctor_without_specialty_cannot_be_saved(self):
        with self.assertRaises(IntegrityError):
            Doctor.objects.create(
                full_name="پزشک بدون تخصص",
                visit_fee=Decimal("100000.00"),
            )

    def test_specialty_protected_when_doctor_exists(self):
        Doctor.objects.create(
            specialty=self.specialty,
            full_name="سارا احمدی",
            visit_fee=Decimal("200000.00"),
        )
        with self.assertRaises(ProtectedError):
            self.specialty.delete()
