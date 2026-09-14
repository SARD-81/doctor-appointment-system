import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("wallet", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="wallettransaction",
            name="appointment",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="appointments.appointment",
            ),
        ),
        migrations.AddConstraint(
            model_name="wallettransaction",
            constraint=models.CheckConstraint(
                condition=models.Q(balance_after__gte=0),
                name="wallet_transaction_balance_after_gte_zero",
            ),
        ),
        migrations.AddConstraint(
            model_name="wallettransaction",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(appointment__isnull=True, transaction_type="TOP_UP")
                    | models.Q(
                        appointment__isnull=False,
                        transaction_type="APPOINTMENT_PAYMENT",
                    )
                ),
                name="wallet_transaction_reference_matches_type",
            ),
        ),
        migrations.AddConstraint(
            model_name="wallettransaction",
            constraint=models.UniqueConstraint(
                condition=models.Q(transaction_type="APPOINTMENT_PAYMENT"),
                fields=("appointment",),
                name="unique_appointment_payment_transaction",
            ),
        ),
    ]
