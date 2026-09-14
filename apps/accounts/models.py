from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.functions import Lower


class User(AbstractUser):
    """Custom user model used across the project."""

    email = models.EmailField(unique=True)

    class Meta(AbstractUser.Meta):
        constraints = [
            models.UniqueConstraint(
                Lower("email"),
                name="accounts_user_email_ci_unique",
            )
        ]

    def __str__(self):
        return self.get_full_name() or self.username
