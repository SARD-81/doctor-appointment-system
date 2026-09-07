# Architecture Implementation Status Snapshot

**Snapshot date:** 2026-09-07

This file is intentionally a status/reconciliation note, not an architecture decision.

## `develop`

- Shared UI foundation from Issue #5 is merged.
- Custom `User` derives from Django `AbstractUser` and uses unique email.
- Architecture Baseline v1.0 is being versioned through Issue #9 / PR #17; it is not yet the same thing as a fully frozen architecture.

## `feature/doctor-domain`

- Issue #2 remains the active cleanup gate.
- Final intended boundary: `Specialty` + `Doctor` only inside the Doctor catalog domain.
- The branch is still one commit ahead of and one commit behind current `develop`, and its current model file still contains AppointmentSlot/Appointment/Review/Wallet/WalletTransaction.
- That transient branch structure must not be treated as final domain ownership.

## `feature/account-authentication`

- Issue #15 remains the authentication backend/forms contract gate.
- The branch currently contains the OTP service plus registration/OTP/login forms, a custom email authentication backend, and expanded OTP lifecycle tests.
- The branch is still behind current `develop` and must integrate latest `develop` before its PR as required by Issue #15.
- View/URL/template ownership has intentionally moved to Team Lead Issue #22; those presentation concerns are not part of the authentication backend branch.
- Current Email + Django Cache OTP implementation evidence is recorded under ADR-012 without declaring the ADR fully frozen.

## Booking dependency rule

Atomic Booking implementation should not be normalized against transient branch layouts. Before implementation, final domain ownership/migrations and the authentication/backend dependencies must be reconciled with this architecture baseline and the relevant merged feature work.

The booking contract also treats notification delivery as a post-commit side effect: a notification failure must not reverse or misreport a database booking/payment that already committed successfully.
