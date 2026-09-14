# Architecture Source Traceability

This file records which project artifacts informed Architecture Baseline v1.0 without changing their approved meaning.

## Primary sources

- Official Doctor Appointment System project brief: mandatory doctor management, search, booking, wallet payment, email confirmation, visited-user review/rating, Django authentication/OTP, production/docker/environment requirements, and ERD under `documents/`.
- Team Architecture Baseline decision session dated 2026-09-04.
- Agreed ERD with eight core entities: User, Specialty, Doctor, AppointmentSlot, Appointment, Wallet, WalletTransaction, Review.
- Agreed UML set: Use Case, Domain Class, Atomic Booking Sequence.
- Existing team Git workflow, Team Contract, and Definition of Done.

## Repository reconciliation evidence

- `develop`: integrated Accounts, Doctors, Appointments, Wallet, and Reviews domains.
- Migrations: database invariants for email identity, slot uniqueness, financial values, ledger references, payment cardinality, and rating bounds.
- Services: cache-backed email OTP, atomic booking, locked wallet top-up, and completed-appointment review eligibility.
- Runtime: PostgreSQL plus shared Redis in production, with Gunicorn and Nginx Compose wiring.

## Rule

Repository implementation evidence may confirm or challenge a decision, but temporary feature-branch structure does not silently replace the approved baseline. Conflicts are resolved through the owning issue and, when architecture changes, through ADR review.
