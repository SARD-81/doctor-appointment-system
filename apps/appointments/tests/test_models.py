from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from apps.appointments.models import Appointment, AppointmentSlot, AppointmentStatus
from apps.doctors.models import Doctor, Specialty

User = get_user_model()


# --- فیکسچرهای تست دامنه ---


@pytest.fixture
def specialty(db):
    # ایجاد تخصص پزشکی برای انتساب به پزشک
    return Specialty.objects.create(name="Cardiology")


@pytest.fixture
def doctor(db, specialty):
    # ایجاد نمونه پزشک فعال با ویزیت پایه
    return Doctor.objects.create(
        specialty=specialty,
        full_name="Dr. Arash Davari",
        visit_fee=Decimal("50000.00"),
        is_active=True,
    )


@pytest.fixture
def patient(db):
    # ایجاد کاربر عادی به عنوان بیمار
    return User.objects.create_user(
        username="patient_user",
        email="patient@example.com",
        password="ValidPassword123!",
    )


@pytest.fixture
def admin_user(db):
    # ایجاد کاربر ادمین برای فیلدهای آدیت تکمیل نوبت
    return User.objects.create_user(
        username="admin_user",
        email="admin@example.com",
        password="ValidPassword123!",
        is_staff=True,
    )


@pytest.fixture
def slot(db, doctor):
    # ایجاد یک اسلات نوبت فعال برای فردا
    return AppointmentSlot.objects.create(
        doctor=doctor,
        starts_at=timezone.now() + timedelta(days=1),
        is_active=True,
    )


# --- تست‌های مدل AppointmentSlot ---


@pytest.mark.django_db
class TestAppointmentSlotModel:
    def test_duplicate_doctor_and_starts_at_rejected(self, doctor):
        # بررسی قید یکتایی: رد اسلات تکراری برای یک پزشک در زمان یکسان
        start_time = timezone.now() + timedelta(days=2)
        AppointmentSlot.objects.create(doctor=doctor, starts_at=start_time)

        with pytest.raises(IntegrityError):
            AppointmentSlot.objects.create(doctor=doctor, starts_at=start_time)

    def test_is_available_derived_logic(self, slot, patient):
        # بررسی منطق داینامیک در دسترس بودن اسلات بدون فیلد دیتابیسی اضافی
        assert slot.is_available is True

        # با ثبت نوبت، اسلات دیگر در دسترس نیست
        Appointment.objects.create(
            patient=patient,
            slot=slot,
            amount_paid=Decimal("50000.00"),
        )
        assert slot.is_available is False

        # اسلات غیرفعال حتی بدون نوبت نباید در دسترس باشد
        slot.is_active = False
        slot.save()
        assert slot.is_available is False


# --- تست‌های مدل Appointment ---


@pytest.mark.django_db
class TestAppointmentModel:
    def test_default_status_is_confirmed(self, patient, slot):
        # بررسی وضعیت پیش‌فرض نوبت جدید طبق قرارداد بیزنس
        appointment = Appointment.objects.create(
            patient=patient,
            slot=slot,
            amount_paid=Decimal("50000.00"),
        )
        assert appointment.status == AppointmentStatus.CONFIRMED

    def test_one_slot_cannot_have_multiple_appointments(self, patient, admin_user, slot):
        # بررسی قید OneToOne: امکان اتصال چند نوبت به یک اسلات وجود ندارد
        Appointment.objects.create(
            patient=patient,
            slot=slot,
            amount_paid=Decimal("50000.00"),
        )
        with pytest.raises(IntegrityError):
            Appointment.objects.create(
                patient=admin_user,
                slot=slot,
                amount_paid=Decimal("50000.00"),
            )

    def test_negative_amount_paid_rejected_at_db_level(self, patient, slot):
        # اعتبارسنجی قید دیتابیسی برای مبالغ منفی
        with pytest.raises(IntegrityError):
            Appointment.objects.create(
                patient=patient,
                slot=slot,
                amount_paid=Decimal("-10.00"),
            )

    def test_negative_amount_paid_rejected_at_clean(self, patient, slot):
        # اعتبارسنجی سطح اپلیکیشن برای مبالغ پرداختی منفی
        appointment = Appointment(
            patient=patient,
            slot=slot,
            amount_paid=Decimal("-500.00"),
        )
        with pytest.raises(ValidationError):
            appointment.full_clean()

    def test_completion_audit_fields(self, patient, admin_user, slot):
        # بررسی صحت چرخه تکمیل نوبت و ذخیره اطلاعات رهگیری
        appointment = Appointment.objects.create(
            patient=patient,
            slot=slot,
            amount_paid=Decimal("50000.00"),
        )
        now = timezone.now()
        appointment.status = AppointmentStatus.COMPLETED
        appointment.completed_at = now
        appointment.completed_by = admin_user
        appointment.save()

        appointment.refresh_from_db()
        assert appointment.status == AppointmentStatus.COMPLETED
        assert appointment.completed_at is not None
        assert appointment.completed_by == admin_user
