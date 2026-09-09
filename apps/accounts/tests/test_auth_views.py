from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

User = get_user_model()
PENDING_SESSION_KEY = "pending_verification_user_id"


def registration_payload(**overrides):
    data = {
        "username": "new_patient",
        "email": "patient@example.com",
        "password": "StrongPass987!",
        "confirm_password": "StrongPass987!",
    }
    data.update(overrides)
    return data


@pytest.mark.django_db
@patch("apps.accounts.views.generate_and_send_otp", return_value=(True, "کد ارسال شد."))
def test_registration_creates_inactive_user_and_starts_verification(mock_send_otp):
    client = Client()

    response = client.post(reverse("accounts:register"), registration_payload())

    assert response.status_code == 302
    assert response.url == reverse("accounts:verify_otp")

    user = User.objects.get(email="patient@example.com")
    assert user.is_active is False
    assert client.session[PENDING_SESSION_KEY] == user.pk
    mock_send_otp.assert_called_once_with(user.email)


@pytest.mark.django_db
def test_invalid_registration_renders_errors_without_creating_user():
    response = Client().post(
        reverse("accounts:register"),
        registration_payload(confirm_password="DifferentPass987!"),
    )

    assert response.status_code == 200
    assert User.objects.count() == 0
    assert "رمزهای عبور با هم مطابقت ندارند." in response.content.decode("utf-8")


@pytest.mark.django_db
@patch("apps.accounts.views.generate_and_send_otp", return_value=(False, "خطا در ارسال ایمیل."))
def test_registration_email_failure_keeps_pending_inactive_user(mock_send_otp):
    client = Client()

    response = client.post(reverse("accounts:register"), registration_payload(), follow=True)

    user = User.objects.get(email="patient@example.com")
    assert user.is_active is False
    assert client.session[PENDING_SESSION_KEY] == user.pk
    assert response.redirect_chain[-1][0] == reverse("accounts:verify_otp")
    assert "خطا در ارسال ایمیل." in response.content.decode("utf-8")
    mock_send_otp.assert_called_once_with(user.email)


@pytest.mark.django_db
def test_verify_requires_pending_registration_session():
    response = Client().get(reverse("accounts:verify_otp"))

    assert response.status_code == 302
    assert response.url == reverse("accounts:register")


@pytest.mark.django_db
@patch("apps.accounts.views.verify_otp")
def test_invalid_otp_form_does_not_call_service(mock_verify_otp):
    user = User.objects.create_user(
        username="pending_user",
        email="pending@example.com",
        password="StrongPass987!",
        is_active=False,
    )
    client = Client()
    session = client.session
    session[PENDING_SESSION_KEY] = user.pk
    session.save()

    response = client.post(reverse("accounts:verify_otp"), {"code": "abc"})

    assert response.status_code == 200
    mock_verify_otp.assert_not_called()


@pytest.mark.django_db
@patch("apps.accounts.views.verify_otp", return_value=(False, "کد وارد شده نامعتبر است."))
def test_wrong_otp_keeps_user_inactive_and_unauthenticated(mock_verify_otp):
    user = User.objects.create_user(
        username="pending_user",
        email="pending@example.com",
        password="StrongPass987!",
        is_active=False,
    )
    client = Client()
    session = client.session
    session[PENDING_SESSION_KEY] = user.pk
    session.save()

    response = client.post(reverse("accounts:verify_otp"), {"code": "123456"})

    user.refresh_from_db()
    assert response.status_code == 200
    assert user.is_active is False
    assert "_auth_user_id" not in client.session
    assert client.session[PENDING_SESSION_KEY] == user.pk
    assert "کد وارد شده نامعتبر است." in response.content.decode("utf-8")
    mock_verify_otp.assert_called_once_with(user.email, "123456")


@pytest.mark.django_db
@patch("apps.accounts.views.verify_otp", return_value=(True, "تأیید شد."))
def test_valid_otp_activates_logs_in_and_clears_pending_state(mock_verify_otp):
    user = User.objects.create_user(
        username="pending_user",
        email="pending@example.com",
        password="StrongPass987!",
        is_active=False,
    )
    client = Client()
    session = client.session
    session[PENDING_SESSION_KEY] = user.pk
    session.save()

    response = client.post(reverse("accounts:verify_otp"), {"code": "001234"})

    user.refresh_from_db()
    assert response.status_code == 302
    assert response.url == reverse("home")
    assert user.is_active is True
    assert client.session["_auth_user_id"] == str(user.pk)
    assert PENDING_SESSION_KEY not in client.session
    mock_verify_otp.assert_called_once_with(user.email, "001234")


@pytest.mark.django_db
def test_stale_pending_user_is_cleared_and_redirected_to_register():
    client = Client()
    session = client.session
    session[PENDING_SESSION_KEY] = 999999
    session.save()

    response = client.get(reverse("accounts:verify_otp"))

    assert response.status_code == 302
    assert response.url == reverse("accounts:register")
    assert PENDING_SESSION_KEY not in client.session


@pytest.mark.django_db
def test_resend_is_post_only():
    response = Client().get(reverse("accounts:resend_otp"))

    assert response.status_code == 405


@pytest.mark.django_db
@patch("apps.accounts.views.generate_and_send_otp", return_value=(True, "کد جدید ارسال شد."))
def test_resend_calls_existing_otp_service_and_returns_to_verify(mock_send_otp):
    user = User.objects.create_user(
        username="pending_user",
        email="pending@example.com",
        password="StrongPass987!",
        is_active=False,
    )
    client = Client()
    session = client.session
    session[PENDING_SESSION_KEY] = user.pk
    session.save()

    response = client.post(reverse("accounts:resend_otp"), follow=True)

    assert response.redirect_chain[-1][0] == reverse("accounts:verify_otp")
    assert "کد جدید ارسال شد." in response.content.decode("utf-8")
    mock_send_otp.assert_called_once_with(user.email)


@pytest.mark.django_db
@patch(
    "apps.accounts.views.generate_and_send_otp",
    return_value=(False, "لطفاً پیش از درخواست مجدد، چند لحظه صبر کنید."),
)
def test_resend_surfaces_service_rejection_without_duplicating_policy(mock_send_otp):
    user = User.objects.create_user(
        username="pending_user",
        email="pending@example.com",
        password="StrongPass987!",
        is_active=False,
    )
    client = Client()
    session = client.session
    session[PENDING_SESSION_KEY] = user.pk
    session.save()

    response = client.post(reverse("accounts:resend_otp"), follow=True)

    assert "لطفاً پیش از درخواست مجدد، چند لحظه صبر کنید." in response.content.decode("utf-8")
    mock_send_otp.assert_called_once_with(user.email)


@pytest.mark.django_db
def test_login_with_valid_email_and_password_authenticates_user():
    user = User.objects.create_user(
        username="active_user",
        email="active@example.com",
        password="StrongPass987!",
        is_active=True,
    )
    client = Client()

    response = client.post(
        reverse("accounts:login"),
        {"email": "ACTIVE@example.com", "password": "StrongPass987!"},
    )

    assert response.status_code == 302
    assert response.url == reverse("home")
    assert client.session["_auth_user_id"] == str(user.pk)


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("email", "password", "is_active"),
    [
        ("active@example.com", "WrongPass987!", True),
        ("missing@example.com", "StrongPass987!", True),
        ("inactive@example.com", "StrongPass987!", False),
    ],
)
def test_login_failures_use_same_generic_error(email, password, is_active):
    User.objects.create_user(
        username="login_user",
        email="inactive@example.com" if not is_active else "active@example.com",
        password="StrongPass987!",
        is_active=is_active,
    )

    response = Client().post(
        reverse("accounts:login"),
        {"email": email, "password": password},
    )

    assert response.status_code == 200
    assert "ایمیل یا رمز عبور صحیح نیست." in response.content.decode("utf-8")


@pytest.mark.django_db
def test_login_honors_safe_next_redirect():
    User.objects.create_user(
        username="active_user",
        email="active@example.com",
        password="StrongPass987!",
        is_active=True,
    )

    response = Client().post(
        reverse("accounts:login"),
        {
            "email": "active@example.com",
            "password": "StrongPass987!",
            "next": "/admin/",
        },
    )

    assert response.status_code == 302
    assert response.url == "/admin/"


@pytest.mark.django_db
def test_login_rejects_external_next_redirect():
    User.objects.create_user(
        username="active_user",
        email="active@example.com",
        password="StrongPass987!",
        is_active=True,
    )

    response = Client().post(
        reverse("accounts:login"),
        {
            "email": "active@example.com",
            "password": "StrongPass987!",
            "next": "https://evil.example/steal-session",
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("home")


@pytest.mark.django_db
def test_authenticated_user_is_redirected_away_from_login_and_register():
    user = User.objects.create_user(
        username="active_user",
        email="active@example.com",
        password="StrongPass987!",
        is_active=True,
    )
    client = Client()
    client.force_login(user, backend="apps.accounts.backends.EmailAuthBackend")

    login_response = client.get(reverse("accounts:login"))
    register_response = client.get(reverse("accounts:register"))

    assert login_response.url == reverse("home")
    assert register_response.url == reverse("home")


@pytest.mark.django_db
def test_logout_is_post_only_and_clears_authenticated_session():
    user = User.objects.create_user(
        username="active_user",
        email="active@example.com",
        password="StrongPass987!",
        is_active=True,
    )
    client = Client()
    client.force_login(user, backend="apps.accounts.backends.EmailAuthBackend")

    get_response = client.get(reverse("accounts:logout"))
    assert get_response.status_code == 405

    post_response = client.post(reverse("accounts:logout"))
    assert post_response.status_code == 302
    assert post_response.url == reverse("home")
    assert "_auth_user_id" not in client.session


@pytest.mark.django_db
def test_logout_requires_csrf_token_when_csrf_checks_are_enforced():
    user = User.objects.create_user(
        username="active_user",
        email="active@example.com",
        password="StrongPass987!",
        is_active=True,
    )
    client = Client(enforce_csrf_checks=True)
    client.force_login(user, backend="apps.accounts.backends.EmailAuthBackend")

    response = client.post(reverse("accounts:logout"))

    assert response.status_code == 403


def test_register_and_login_render_shared_auth_ui_contract():
    client = Client()

    register_response = client.get(reverse("accounts:register"))
    login_response = client.get(reverse("accounts:login"))

    register_html = register_response.content.decode("utf-8")
    login_html = login_response.content.decode("utf-8")

    assert "auth-shell" in register_html
    assert "auth-shell" in login_html
    assert "data-password-toggle" in register_html
    assert "data-password-toggle" in login_html


def test_anonymous_navbar_links_to_login_and_register():
    response = Client().get(reverse("home"))
    html = response.content.decode("utf-8")

    assert f'href="{reverse("accounts:login")}"' in html
    assert f'href="{reverse("accounts:register")}"' in html
