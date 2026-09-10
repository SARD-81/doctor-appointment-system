from decimal import Decimal

import pytest
from django.urls import reverse

from apps.doctors.models import Doctor, Specialty


@pytest.fixture
def specialties(db):
    return {
        "cardiology": Specialty.objects.create(name="قلب و عروق"),
        "neurology": Specialty.objects.create(name="مغز و اعصاب"),
    }


@pytest.fixture
def doctors(specialties):
    return {
        "sara": Doctor.objects.create(
            full_name="سارا احمدی",
            specialty=specialties["cardiology"],
            visit_fee=Decimal("350000.00"),
            is_active=True,
        ),
        "ali": Doctor.objects.create(
            full_name="علی رضایی",
            specialty=specialties["neurology"],
            visit_fee=Decimal("420000.00"),
            is_active=True,
        ),
        "inactive": Doctor.objects.create(
            full_name="مریم کریمی",
            specialty=specialties["cardiology"],
            visit_fee=Decimal("300000.00"),
            is_active=False,
        ),
    }


@pytest.mark.django_db
def test_doctor_discovery_route_is_namespaced(client):
    response = client.get(reverse("doctors:list"))

    assert response.status_code == 200
    assert response.templates[0].name == "doctors/doctor_list.html"


@pytest.mark.django_db
def test_discovery_lists_only_active_doctors(client, doctors):
    response = client.get(reverse("doctors:list"))
    html = response.content.decode("utf-8")

    assert doctors["sara"].full_name in html
    assert doctors["ali"].full_name in html
    assert doctors["inactive"].full_name not in html


@pytest.mark.django_db
def test_name_search_is_case_insensitive_and_partial(client, doctors):
    response = client.get(reverse("doctors:list"), {"q": "احمد"})
    html = response.content.decode("utf-8")

    assert doctors["sara"].full_name in html
    assert doctors["ali"].full_name not in html


@pytest.mark.django_db
def test_specialty_filter_returns_only_matching_active_doctors(client, doctors, specialties):
    response = client.get(
        reverse("doctors:list"),
        {"specialty": specialties["cardiology"].pk},
    )
    html = response.content.decode("utf-8")

    assert doctors["sara"].full_name in html
    assert doctors["ali"].full_name not in html
    assert doctors["inactive"].full_name not in html


@pytest.mark.django_db
def test_combined_name_and_specialty_filters_are_applied_together(client, doctors, specialties):
    response = client.get(
        reverse("doctors:list"),
        {"q": "سارا", "specialty": specialties["cardiology"].pk},
    )
    html = response.content.decode("utf-8")

    assert doctors["sara"].full_name in html
    assert doctors["ali"].full_name not in html


@pytest.mark.django_db
def test_combined_filters_can_return_empty_result(client, doctors, specialties):
    response = client.get(
        reverse("doctors:list"),
        {"q": "سارا", "specialty": specialties["neurology"].pk},
    )
    html = response.content.decode("utf-8")

    assert response.status_code == 200
    assert 'class="doctor-card"' not in html
    assert "پزشکی با این فیلترها پیدا نشد" in html


@pytest.mark.django_db
@pytest.mark.parametrize("invalid_specialty", ["abc", "-1", "999999"])
def test_invalid_specialty_filter_does_not_crash_or_hide_valid_doctors(
    client,
    doctors,
    invalid_specialty,
):
    response = client.get(reverse("doctors:list"), {"specialty": invalid_specialty})
    html = response.content.decode("utf-8")

    assert response.status_code == 200
    assert doctors["sara"].full_name in html
    assert doctors["ali"].full_name in html
    assert "تخصص انتخاب‌شده معتبر نیست" in html


@pytest.mark.django_db
def test_search_and_specialty_values_remain_visible_after_filtering(client, doctors, specialties):
    response = client.get(
        reverse("doctors:list"),
        {"q": "سارا", "specialty": specialties["cardiology"].pk},
    )
    html = response.content.decode("utf-8")

    assert 'value="سارا"' in html
    assert f'value="{specialties["cardiology"].pk}" selected' in html


@pytest.mark.django_db
def test_empty_state_uses_shared_empty_state_component(client, specialties):
    response = client.get(reverse("doctors:list"), {"q": "پزشک-ناموجود"})
    html = response.content.decode("utf-8")

    assert 'class="empty-state"' in html
    assert "پزشکی با این فیلترها پیدا نشد" in html
    assert f'href="{reverse("doctors:list")}"' in html


@pytest.mark.django_db
def test_results_use_shared_doctor_card_contract(client, doctors):
    response = client.get(reverse("doctors:list"))
    html = response.content.decode("utf-8")

    assert 'class="doctor-card"' in html
    assert doctors["sara"].full_name in html
    assert doctors["sara"].specialty.name in html
    assert "350,000" in html
    assert "تومان" in html


@pytest.mark.django_db
def test_doctors_navigation_points_to_discovery(client, doctors):
    response = client.get(reverse("home"))
    html = response.content.decode("utf-8")

    assert f'href="{reverse("doctors:list")}"' in html
    assert ">پزشکان</a>" in html
