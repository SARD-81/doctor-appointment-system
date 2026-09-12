from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from apps.appointments.models import Appointment, AppointmentSlot, AppointmentStatus
from apps.doctors.models import Doctor, Specialty
from apps.wallet.models import Wallet


@pytest.fixture
def specialty(db):
    return Specialty.objects.create(name="قلب و عروق")


@pytest.fixture
def doctor(specialty):
    return Doctor.objects.create(
        full_name="سارا احمدی",
        specialty=specialty,
        visit_fee=Decimal("350000.50"),
        is_active=True,
    )


@pytest.fixture
def inactive_doctor(specialty):
    return Doctor.objects.create(
        full_name="پزشک غیرفعال",
        specialty=specialty,
        visit_fee=Decimal("200000.00"),
        is_active=False,
    )


@pytest.fixture
def patient(db):
    return get_user_model().objects.create_user(
        username="detail_patient",
        email="detail-patient@example.com",
        password="StrongPass123!",
    )


@pytest.mark.django_db
def test_doctor_detail_route_is_namespaced_and_renders_active_doctor(client, doctor):
    response = client.get(reverse("doctors:detail", args=[doctor.pk]))
    html = response.content.decode("utf-8")

    assert response.status_code == 200
    assert response.templates[0].name == "doctors/doctor_detail.html"
    assert doctor.full_name in html
    assert doctor.specialty.name in html
    assert "350,000.50 تومان" in html


@pytest.mark.django_db
def test_inactive_doctor_detail_returns_404(client, inactive_doctor):
    response = client.get(reverse("doctors:detail", args=[inactive_doctor.pk]))

    assert response.status_code == 404


@pytest.mark.django_db
def test_unknown_doctor_detail_returns_404(client):
    response = client.get(reverse("doctors:detail", args=[999999]))

    assert response.status_code == 404


@pytest.mark.django_db
def test_detail_lists_only_active_future_unbooked_slots(client, doctor, patient):
    now = timezone.now()
    available = AppointmentSlot.objects.create(
        doctor=doctor,
        starts_at=now + timedelta(days=1),
        is_active=True,
    )
    inactive = AppointmentSlot.objects.create(
        doctor=doctor,
        starts_at=now + timedelta(days=2),
        is_active=False,
    )
    past = AppointmentSlot.objects.create(
        doctor=doctor,
        starts_at=now - timedelta(hours=1),
        is_active=True,
    )
    occupied = AppointmentSlot.objects.create(
        doctor=doctor,
        starts_at=now + timedelta(days=3),
        is_active=True,
    )
    Appointment.objects.create(
        patient=patient,
        slot=occupied,
        status=AppointmentStatus.CONFIRMED,
        amount_paid=doctor.visit_fee,
    )

    response = client.get(reverse("doctors:detail", args=[doctor.pk]))
    html = response.content.decode("utf-8")

    assert response.status_code == 200
    assert f'value="{available.pk}"' in html
    assert f'value="{inactive.pk}"' not in html
    assert f'value="{past.pk}"' not in html
    assert f'value="{occupied.pk}"' not in html


@pytest.mark.django_db
def test_slot_selection_uses_native_radio_with_real_slot_id(client, doctor):
    slot = AppointmentSlot.objects.create(
        doctor=doctor,
        starts_at=timezone.now() + timedelta(days=1),
        is_active=True,
    )

    response = client.get(reverse("doctors:detail", args=[doctor.pk]))
    html = response.content.decode("utf-8")

    assert 'type="radio"' in html
    assert 'name="slot"' in html
    assert f'value="{slot.pk}"' in html
    assert "data-slot-radio" in html


@pytest.mark.django_db
def test_valid_slot_selection_is_preserved_and_confirmed_without_booking_mutation(client, doctor):
    slot = AppointmentSlot.objects.create(
        doctor=doctor,
        starts_at=timezone.now() + timedelta(days=1),
        is_active=True,
    )

    response = client.get(
        reverse("doctors:detail", args=[doctor.pk]),
        {"slot": slot.pk},
    )
    html = response.content.decode("utf-8")

    assert response.status_code == 200
    assert f'value="{slot.pk}"' in html
    assert "checked" in html
    assert "زمان انتخاب‌شده" in html
    assert Appointment.objects.count() == 0


@pytest.mark.django_db
def test_invalid_or_unavailable_selected_slot_is_rejected_safely(client, doctor):
    unavailable = AppointmentSlot.objects.create(
        doctor=doctor,
        starts_at=timezone.now() - timedelta(days=1),
        is_active=True,
    )

    response = client.get(
        reverse("doctors:detail", args=[doctor.pk]),
        {"slot": unavailable.pk},
    )
    html = response.content.decode("utf-8")

    assert response.status_code == 200
    assert "زمان انتخاب‌شده معتبر یا در دسترس نیست" in html


@pytest.mark.django_db
def test_no_available_slots_uses_shared_empty_state(client, doctor):
    response = client.get(reverse("doctors:detail", args=[doctor.pk]))
    html = response.content.decode("utf-8")

    assert response.status_code == 200
    assert 'class="empty-state"' in html
    assert "در حال حاضر نوبت آزادی برای این پزشک وجود ندارد" in html


@pytest.mark.django_db
def test_discovery_cards_link_to_doctor_detail(client, doctor):
    response = client.get(reverse("doctors:list"))
    html = response.content.decode("utf-8")

    assert f'href="{reverse("doctors:detail", args=[doctor.pk])}"' in html
    assert "مشاهده پروفایل" in html


@pytest.mark.django_db
def test_detail_shows_wallet_balance_state_for_authenticated_user(client, doctor, patient):
    client.force_login(patient)
    Wallet.objects.create(user=patient, balance=Decimal("150000.00"))

    response = client.get(reverse("doctors:detail", args=[doctor.pk]))
    html = response.content.decode("utf-8")

    assert "موجودی کیف پول" in html
    assert "150,000.00 تومان" in html
    assert "موجودی کافی نیست" in html


@pytest.mark.django_db
def test_detail_hides_wallet_state_for_anonymous_user(client, doctor):
    response = client.get(reverse("doctors:detail", args=[doctor.pk]))

    assert "موجودی کیف پول" not in response.content.decode("utf-8")


@pytest.mark.django_db
def test_reconfirming_already_selected_slot_surfaces_notice(client, doctor, patient):
    slot = AppointmentSlot.objects.create(
        doctor=doctor,
        starts_at=timezone.now() + timedelta(days=1),
        is_active=True,
    )
    client.force_login(patient)

    first = client.get(reverse("doctors:detail", args=[doctor.pk]), {"slot": slot.pk})
    assert "قبلاً به‌عنوان انتخاب" not in first.content.decode("utf-8")

    second = client.get(reverse("doctors:detail", args=[doctor.pk]), {"slot": slot.pk})
    assert "قبلاً به‌عنوان انتخاب" in second.content.decode("utf-8")
