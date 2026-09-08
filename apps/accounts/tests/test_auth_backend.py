import pytest
from django.contrib.auth import authenticate, get_user_model

from apps.accounts.forms import UserRegisterForm, VerifyOTPForm

User = get_user_model()


@pytest.mark.django_db
def test_email_auth_backend_success():
    email = "active_user@example.com"
    password = "SecurePassword123!"
    User.objects.create_user(
        username="active_user",
        email=email,
        password=password,
        is_active=True,
    )

    user = authenticate(email=email, password=password)
    assert user is not None
    assert user.email == email


@pytest.mark.django_db
def test_email_auth_backend_inactive_user():
    email = "inactive_user@example.com"
    password = "SecurePassword123!"
    User.objects.create_user(
        username="inactive_user",
        email=email,
        password=password,
        is_active=False,
    )

    user = authenticate(email=email, password=password)
    assert user is None


@pytest.mark.django_db
def test_email_auth_backend_wrong_password():
    email = "user@example.com"
    User.objects.create_user(
        username="user",
        email=email,
        password="CorrectPassword123!",
        is_active=True,
    )

    user = authenticate(email=email, password="WrongPassword123!")
    assert user is None


@pytest.mark.django_db
def test_email_auth_backend_unknown_email():
    user = authenticate(email="nonexistent@example.com", password="SomePassword123!")
    assert user is None


@pytest.mark.django_db
def test_user_register_form_creates_inactive_user():
    data = {
        "username": "new_patient",
        "email": "patient@example.com",
        "password": "StrongPassword123!",
        "confirm_password": "StrongPassword123!",
    }
    form = UserRegisterForm(data=data)
    assert form.is_valid()
    user = form.save()

    assert user.pk is not None
    assert user.is_active is False
    assert user.check_password("StrongPassword123!")


def test_verify_otp_form_validation():
    assert VerifyOTPForm(data={"code": "123456"}).is_valid()
    assert not VerifyOTPForm(data={"code": "12345"}).is_valid()
    assert not VerifyOTPForm(data={"code": "1234567"}).is_valid()
    assert not VerifyOTPForm(data={"code": "abcdef"}).is_valid()
