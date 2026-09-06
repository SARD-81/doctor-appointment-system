# Architecture Implementation Status Snapshot

**Snapshot date:** 2026-09-06

This file is intentionally a status/reconciliation note, not an architecture decision.

## `develop`

- Shared UI foundation from Issue #5 is merged.
- Custom `User` derives from Django `AbstractUser` and uses unique email.
- Architecture baseline and critical diagrams are being versioned by Issue #9.

## `feature/doctor-domain`

- Issue #2 remains the active cleanup gate.
- Final intended boundary: `Specialty` + `Doctor` only inside the Doctor catalog domain.
- Current branch still contains AppointmentSlot/Appointment/Review/Wallet/WalletTransaction and therefore must not be treated as final domain ownership.

## `feature/account-authentication`

- OTP service foundation exists.
- Issue #15 remains the active gate for forms/views/URLs/templates and end-to-end auth behavior/tests.
- Current OTP implementation evidence is recorded under ADR-012 without declaring the ADR fully frozen.

## Booking dependency rule

Atomic Booking implementation should not be normalized against transient branch layouts. Before implementation, final domain ownership/migrations must be reconciled with this architecture baseline and the relevant merged feature work.
