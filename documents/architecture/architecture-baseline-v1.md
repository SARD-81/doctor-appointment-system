# Architecture Baseline v1.0 — Doctor Appointment System

**Decision date:** 2026-09-04  
**Repository versioning date:** 2026-09-06  
**Status:** Proposed baseline for team/mentor review; not fully frozen  
**Decision participants:** Amir (Team Lead), Mahsa  
**OTP final review:** pending Amirreza/team confirmation

This document is the version-controlled Source of Truth for the project's initial architecture. It preserves the agreed boundaries and contracts and does not treat temporary feature-branch structure as final architecture.

## Navigation

- [Architecture index](README.md)
- [ERD](erd.md)
- [Use Case UML](uml-use-case.md)
- [Domain Class UML](uml-domain-class.md)
- [Booking Sequence UML](uml-booking-sequence.md)
- [ADR index](../adr/README.md)

## Formal project scope

The mandatory project brief requires Admin management of doctors/specialties/slots/fees, doctor search by name or specialty, booking from available slots, wallet payment, booking confirmation by email, review/rating by visited users, Django authentication with OTP, and an ERD under `documents/`.

Optional OAuth remains bonus scope and is not required by the baseline.

## Repository reconciliation

- On `develop`, `User` derives from Django `AbstractUser` and has unique email; this matches the baseline.
- Issue #2 requires the Doctor catalog boundary to contain only `Specialty` and `Doctor`. The current `feature/doctor-domain` branch still contains later-domain models, so that branch is treated as work in progress rather than final architecture.
- The current authentication branch provides implementation evidence for an Email + Django Cache OTP direction with expiry, cooldown, attempt limiting, rate limiting, hashed storage, one-time consumption, registration/OTP/login forms, and a custom email authentication backend. ADR-012 remains pending final review/merge confirmation rather than being silently frozen from branch code.

## Decision summary

| ADR | Decision |
|---|---|
| ADR-001 | Doctor is independent from User |
| ADR-002 | No separate Admin entity; use Django staff/permissions |
| ADR-003 | Specialty 1:N Doctor |
| ADR-004 | AppointmentSlot is separate from Appointment; availability is derived |
| ADR-005 | Store current doctor fee and appointment payment snapshot |
| ADR-006 | Wallet includes a transaction ledger |
| ADR-007 | WalletTransaction may reference Appointment; top-up has no appointment; max one appointment-payment trace per Appointment |
| ADR-008 | Maximum one Review per completed Appointment |
| ADR-009 | Admin marks Appointment completed and completion is auditable |
| ADR-010 | Cancellation/refund are outside baseline scope |
| ADR-011 | Wallet top-up is simulated; no real payment gateway required |
| ADR-012 | OTP contract pending final confirmation; current direction is Email + Cache |

Detailed rationale is preserved in [the ADR index](../adr/README.md).

## ERD baseline

Core entities are `User`, `Specialty`, `Doctor`, `AppointmentSlot`, `Appointment`, `Wallet`, `WalletTransaction`, and `Review`. OTP persistence is intentionally excluded until ADR-012 is finalized.

Key constraints include unique user email, unique specialty name, non-negative visit fee, unique `(doctor, starts_at)` slot, unique appointment slot, non-negative payment snapshot, one wallet per user with non-negative balance, positive ledger amounts, one optional payment trace per Appointment, transaction/reference consistency for `TOP_UP` vs `APPOINTMENT_PAYMENT`, and one review per appointment with rating 1..5.

See [ERD](erd.md).

## Service/application rules

- Booking executes in one database transaction.
- Slot and wallet rows are locked during booking.
- Review is allowed only for `COMPLETED` appointments.
- `completed_by` must represent an authorized staff/admin user.
- Booking confirmation email is scheduled only after successful database commit.
- Notification/email failure after commit is operationally separate from booking success: it must not convert an already committed booking/payment into a failed booking response or encourage a duplicate retry. The notification failure must be isolated and handled separately (log/retry/report).

## Appointment lifecycle

```text
CONFIRMED
   |
   | Admin marks visit completed
   v
COMPLETED
   |
   | Review becomes eligible
   v
REVIEW ALLOWED (max one per appointment)
```

Cancellation and refund are intentionally outside Architecture Baseline v1.0.

## Booking Transaction Contract

1. User selects an `AppointmentSlot`.
2. `BookingService` opens `transaction.atomic()`.
3. Lock the selected slot row and validate active/unbooked state.
4. Lock the user's wallet row and validate balance against `Doctor.visit_fee`.
5. Create `Appointment(status=CONFIRMED)` with `amount_paid` as the fee snapshot.
6. Debit Wallet balance.
7. Create `WalletTransaction(type=APPOINTMENT_PAYMENT, appointment=<created>)`.
8. Register the booking-confirmation notification for post-commit execution.
9. Commit the database transaction.
10. Run the booking-confirmation notification only after commit.
11. Return the committed Appointment result to the view regardless of notification delivery success; notification failure is isolated and handled separately.

Failure contract:

- unavailable/already-booked slot -> no wallet change;
- insufficient balance -> no Appointment or payment ledger row;
- database error -> rollback all database writes;
- post-commit notification failure -> booking/payment remain committed and are still treated as success; notification handling is logged/retried/reported separately.

No partial booking or wallet debit may remain after a database failure.

See [Booking Sequence UML](uml-booking-sequence.md).

## Open decisions

- Final OTP channel/storage/lifecycle contract: Amirreza + team.
- Extra Doctor fields such as license: only if requirement/mentor requires them.
- Wallet subsystem reuse details: review before implementation.
- Final app ownership/naming for later domains: settle before final migrations.

## Architecture Freeze v1.0

Full freeze requires all three team members to review the baseline, ADR-012 to be finalized or explicitly deferred, ERD/UML to remain consistent with this baseline, final domain migrations to match the agreed boundaries, Booking implementation to match the transaction/failure contract, and later changes to be recorded through ADR review.

Versioning this documentation does **not** by itself declare the full architecture frozen.
