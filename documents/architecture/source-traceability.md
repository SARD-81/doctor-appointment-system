# Architecture Source Traceability

This file records which project artifacts informed Architecture Baseline v1.0 without changing their approved meaning.

## Primary sources

- Official Doctor Appointment System project brief: mandatory doctor management, search, booking, wallet payment, email confirmation, visited-user review/rating, Django authentication/OTP, production/docker/environment requirements, and ERD under `documents/`.
- Team Architecture Baseline decision session dated 2026-09-04.
- Agreed ERD with eight core entities: User, Specialty, Doctor, AppointmentSlot, Appointment, Wallet, WalletTransaction, Review.
- Agreed UML set: Use Case, Domain Class, Atomic Booking Sequence.
- Existing team Git workflow, Team Contract, and Definition of Done.

## Repository reconciliation evidence

- `develop`: custom `User(AbstractUser)` with unique email.
- `feature/doctor-domain`: current branch still contains later-domain models even though Issue #2 requires the final Doctor boundary to contain only Specialty/Doctor.
- `feature/account-authentication`: current OTP service provides Email + Django Cache implementation evidence while Issue #15 remains the gate for final authentication-flow review and tests.

## Rule

Repository implementation evidence may confirm or challenge a decision, but temporary feature-branch structure does not silently replace the approved baseline. Conflicts are resolved through the owning issue and, when architecture changes, through ADR review.
