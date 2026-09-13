import logging
from decimal import Decimal

from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.appointments.exceptions import InsufficientBalanceError, SlotUnavailableError
from apps.appointments.models import Appointment, AppointmentSlot, AppointmentStatus
from apps.wallet.models import Wallet, WalletTransaction

logger = logging.getLogger(__name__)


class BookingService:
    """Atomic appointment booking contract from Architecture Baseline v1.0.

    Guarantees (BookingTransactionContract):
      1. Slot row locked with SELECT FOR UPDATE, then revalidated.
      2. Wallet row locked with SELECT FOR UPDATE, then balance checked.
      3. Appointment created in CONFIRMED state with a visit_fee snapshot.
      4. Wallet debited and an APPOINTMENT_PAYMENT ledger entry written
         (skipped for zero-fee visits per ADR-013).
      5. Confirmation email is sent only after COMMIT (on_commit hook).

    FailureContract: any failure raises a domain error (or propagates the DB
    error), the whole transaction rolls back, and the slot remains bookable.
    """

    @staticmethod
    def book_appointment(*, patient, slot_id: int) -> Appointment:
        if patient is None:
            raise TypeError("Patient is required")
        if slot_id is None:
            raise TypeError("slot_id is required")

        with transaction.atomic():
            slot = (
                AppointmentSlot.objects.select_for_update()
                .select_related("doctor")
                .filter(pk=slot_id, doctor__is_active=True)
                .first()
            )
            if slot is None:
                raise SlotUnavailableError("Slot does not exist or its doctor is inactive.")
            BookingService._validate_slot_availability(slot)

            visit_fee = slot.doctor.visit_fee

            wallet = None
            if visit_fee > Decimal("0.00"):
                # ADR-013: zero-fee visits need no wallet, debit, or ledger row.
                wallet = Wallet.objects.select_for_update().filter(user=patient).first()
                if wallet is None:
                    raise InsufficientBalanceError(balance=Decimal("0.00"), required=visit_fee)
                if wallet.balance < visit_fee:
                    raise InsufficientBalanceError(balance=wallet.balance, required=visit_fee)

            try:
                appointment = Appointment.objects.create(
                    patient=patient,
                    slot=slot,
                    status=AppointmentStatus.CONFIRMED,
                    amount_paid=visit_fee,
                )
            except IntegrityError as exc:
                raise SlotUnavailableError(
                    "Slot could not be booked due to a database conflict."
                ) from exc

            if wallet is not None:
                wallet.balance = wallet.balance - visit_fee
                wallet.save(update_fields=["balance", "updated_at"])

                WalletTransaction.objects.create(
                    wallet=wallet,
                    appointment=appointment,
                    transaction_type=WalletTransaction.APPOINTMENT_PAYMENT,
                    amount=visit_fee,
                    balance_after=wallet.balance,
                )

            transaction.on_commit(
                lambda: BookingService._send_confirmation_email(appointment),
                robust=True,
            )

        return appointment

    @staticmethod
    def _validate_slot_availability(slot: AppointmentSlot) -> None:
        """Revalidate availability *after* acquiring the row lock.

        Validation must happen post-lock so concurrent transactions that race
        for the same slot observe the final committed state.
        """
        if not slot.is_active:
            raise SlotUnavailableError("Slot is not active.")
        if slot.starts_at <= timezone.now():
            raise SlotUnavailableError("Slot starts in the past.")
        if hasattr(slot, "appointment"):
            raise SlotUnavailableError("Slot is already booked.")

    @staticmethod
    def _send_confirmation_email(appointment: Appointment) -> None:
        """Send booking confirmation; email failure must never break the booking."""
        try:
            if not appointment.patient.email:
                return
            local_start = timezone.localtime(appointment.slot.starts_at)
            formatted_start = local_start.strftime("%Y/%m/%d %H:%M")
            send_mail(
                subject="تأیید رزرو نوبت",
                message=(
                    f"نوبت شماره {appointment.pk} برای شما ثبت شد.\n"
                    f"پزشک: {appointment.slot.doctor.full_name}\n"
                    f"زمان: {formatted_start}\n"
                    f"مبلغ پرداخت‌شده: {appointment.amount_paid}"
                ),
                from_email=None,
                recipient_list=[appointment.patient.email],
                fail_silently=False,
            )
        except Exception:
            logger.exception(
                "Failed to send booking confirmation email",
                extra={"appointment_id": appointment.pk},
            )
