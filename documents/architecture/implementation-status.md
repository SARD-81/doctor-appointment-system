# Architecture Implementation Status

**Snapshot date:** 2026-09-14

This document reconciles Architecture Baseline v1.0 with the integrated implementation.
It is a status record, not a replacement for an ADR.

## Integrated domains

| Domain | Current implementation |
|---|---|
| Accounts | Custom user, case-insensitive unique email, email/password login, cache-backed email OTP |
| Doctors | Specialty and Doctor catalog, admin management, search, detail, active/future slot discovery |
| Appointments | Slot and Appointment models, atomic BookingService, fee snapshot, post-commit email |
| Wallet | One wallet per user, simulated top-up, locked balance mutation, constrained transaction ledger |
| Reviews | One review per completed appointment, ownership/status checks, rating presentation |
| UI | Responsive RTL shared components, connected landing search/CTA, persistent light/dark themes |
| Runtime | PostgreSQL, shared Redis cache, Gunicorn, Nginx, development and production Compose |

## Contract reconciliation

- `Appointment.slot` is one-to-one, so database storage prevents double booking.
- Booking locks the slot and wallet within `transaction.atomic()`.
- A booking snapshots `Doctor.visit_fee` into `Appointment.amount_paid`.
- Paid bookings debit the wallet and create exactly one constrained
  `APPOINTMENT_PAYMENT` ledger row.
- Zero-fee appointments deliberately create no zero-valued ledger row (ADR-013).
- Booking email is registered with `transaction.on_commit`; delivery failure cannot roll
  back or misreport the committed booking.
- Review creation locks the appointment and requires both ownership and `COMPLETED`
  status.
- Admin completion records `completed_at` and `completed_by` through the dedicated admin
  action.
- Production OTP state uses shared Redis, avoiding per-worker LocMemCache divergence.

## Database invariants

The current migrations enforce:

- case-insensitive user email uniqueness;
- unique specialty names and non-negative doctor fees;
- unique `(doctor, starts_at)` slots and one appointment per slot;
- non-negative payment snapshots and wallet balances;
- positive ledger amounts and non-negative post-transaction balances;
- transaction type / appointment-reference consistency;
- at most one payment ledger row per appointment;
- one review per appointment and rating from 1 through 5.

## Deliberate scope boundaries

- Cancellation and refund remain outside Architecture Baseline v1.0.
- Wallet top-up remains simulated; no real payment gateway is included.
- Google OAuth remains optional bonus scope and is not implemented.
- The health endpoint is a process-level liveness probe and deliberately does not query
  PostgreSQL or expose application data.

## Release gates

A release still requires a green PostgreSQL CI run, successful Docker build/runtime smoke
test in an environment with Docker, real SMTP credentials, a shared Redis service, and an
external TLS termination path. The production HTTP listener must not be exposed directly
to the internet.
