from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("appointments", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Wallet",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("balance", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="wallet", to=settings.AUTH_USER_MODEL)),
            ],
            options={"constraints": [models.CheckConstraint(condition=models.Q(balance__gte=0), name="wallet_balance_gte_zero")]},
        ),
        migrations.CreateModel(
            name="WalletTransaction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("transaction_type", models.CharField(choices=[("TOP_UP", "Top Up"), ("APPOINTMENT_PAYMENT", "Appointment Payment")], max_length=32)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("balance_after", models.DecimalField(decimal_places=2, max_digits=12)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("appointment", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to="appointments.appointment")),
                ("wallet", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="transactions", to="wallet.wallet")),
            ],
            options={"ordering": ["-created_at"], "constraints": [models.CheckConstraint(condition=models.Q(amount__gt=0), name="wallet_transaction_amount_gt_zero")]},
        ),
    ]
