import pytest
from django.conf import settings
from django.contrib.auth import get_user_model


def test_project_uses_custom_user_model():
    assert settings.AUTH_USER_MODEL == "accounts.User"


def test_project_uses_postgresql():
    assert settings.DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql"


@pytest.mark.django_db
def test_custom_user_can_be_created():
    user_model = get_user_model()

    user = user_model.objects.create_user(
        username="smoke_user",
        email="smoke@example.com",
        password="StrongTestPassword123!",
    )

    assert user.pk is not None
    assert user.email == "smoke@example.com"
    assert user.check_password("StrongTestPassword123!")
