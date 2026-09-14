# Architecture Baseline Review Checklist

Use this checklist for changes that touch Architecture Baseline v1.0.

- [ ] Baseline mandatory scope matches the official project brief.
- [ ] Doctor remains independent from User unless a new requirement explicitly changes it.
- [ ] Admin remains a Django permission/staff concern, not a separate entity.
- [ ] ERD contains the eight agreed core entities; cache-backed OTP does not introduce a database entity.
- [ ] Slot availability has one source of truth; no duplicate `is_booked` state is introduced.
- [ ] Appointment stores `amount_paid` as a booking-time fee snapshot.
- [ ] Wallet includes an auditable ledger.
- [ ] `APPOINTMENT_PAYMENT` requires an Appointment, `TOP_UP` requires no Appointment, and the baseline enforces at most one appointment-payment ledger trace per Appointment.
- [ ] Review is one-per-appointment and eligible only after `COMPLETED`.
- [ ] Lifecycle remains `CONFIRMED -> COMPLETED`; cancellation/refund are out of baseline scope.
- [ ] Booking sequence includes atomic transaction, slot/wallet row locks, rollback, ledger entry, and post-commit email.
- [ ] Post-commit notification failure is isolated from the committed booking result so a successful payment/booking cannot be surfaced as a failed booking solely because email delivery failed.
- [ ] ADR-012 remains Email + Django Cache, with a shared production cache for multi-worker consistency.
- [ ] Implementation status and README are updated when integrated behavior changes.
- [ ] Any intentional contract change includes an ADR amendment, migration impact, and regression tests.
