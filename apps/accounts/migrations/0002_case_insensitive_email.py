from django.db import migrations, models
from django.db.models import Count
from django.db.models.functions import Lower


def normalize_existing_emails(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    duplicates = list(
        User.objects.annotate(normalized_email=Lower("email"))
        .values("normalized_email")
        .annotate(total=Count("id"))
        .filter(total__gt=1)
        .values_list("normalized_email", flat=True)
    )
    if duplicates:
        raise RuntimeError(
            "Cannot enforce case-insensitive email uniqueness; resolve duplicate emails first: "
            + ", ".join(duplicates)
        )

    for user in User.objects.only("pk", "email").iterator():
        normalized_email = user.email.lower()
        if normalized_email != user.email:
            User.objects.filter(pk=user.pk).update(email=normalized_email)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(normalize_existing_emails, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.UniqueConstraint(
                Lower("email"),
                name="accounts_user_email_ci_unique",
            ),
        ),
    ]
