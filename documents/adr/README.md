# Architecture Decision Records — Baseline v1.0

This index preserves traceability for ADR-001 through ADR-012. Statuses describe the agreed architecture baseline, not temporary feature-branch structure.

| ADR | Title | Status |
|---|---|---|
| ADR-001 | Doctor is independent from User | Accepted baseline |
| ADR-002 | No separate Admin entity | Accepted baseline |
| ADR-003 | Specialty 1:N Doctor | Accepted baseline |
| ADR-004 | AppointmentSlot is separate from Appointment | Accepted baseline |
| ADR-005 | Store current fee and appointment payment snapshot | Accepted baseline |
| ADR-006 | Wallet has a transaction ledger | Accepted baseline |
| ADR-007 | WalletTransaction has nullable Appointment FK | Accepted baseline |
| ADR-008 | Max one Review per completed Appointment | Accepted baseline |
| ADR-009 | Admin marks Appointment completed | Accepted baseline |
| ADR-010 | Cancellation/refund out of baseline scope | Accepted baseline |
| ADR-011 | Simulated wallet top-up | Accepted baseline |
| ADR-012 | OTP channel/storage/lifecycle | Pending final confirmation |

## ADR-001 — Doctor is independent from User

**Decision:** `Doctor` is an independent model and does not have a user account or doctor panel by default.

**Rationale:** The formal requirement assigns doctor management to Admin and defines no doctor login/panel use case. Coupling Doctor to User would add dependency without a requirement.

**Consequences:** no `User.is_doctor`; a future doctor panel would require an explicit reviewed relationship/migration.

## ADR-002 — No separate Admin entity

**Decision:** Admin uses Django user capabilities (`is_staff`, `is_superuser`, permissions/groups).

**Rationale:** A separate Admin table would duplicate authentication and permission concepts.

**Consequence:** Admin is a UML actor, not a separate ERD entity.

## ADR-003 — Specialty 1:N Doctor

**Decision:** One Specialty has many Doctors; each Doctor belongs to one Specialty.

**Rationale:** The current requirements do not require multiple specialties per doctor. The simpler model reduces query/form/constraint complexity.

**Consequence:** `Doctor.specialty` is a ForeignKey.

## ADR-004 — AppointmentSlot is separate from Appointment

**Decision:** Available slots and booked appointments are separate entities with independent lifecycles.

**Rationale:** Admin defines availability before a patient books it.

**Consequence:** availability is derived from slot activity plus the existence/absence of an appointment; baseline does not persist duplicate `is_booked` state.

## ADR-005 — Current fee + historical payment snapshot

**Decision:** `Doctor.visit_fee` stores the current fee and `Appointment.amount_paid` stores the booking-time snapshot.

**Rationale:** Future fee changes must not rewrite historical financial records.

## ADR-006 — Wallet includes a ledger

**Decision:** Wallet is not only a balance; `WalletTransaction` records each balance mutation.

**Minimum transaction types:** `TOP_UP`, `APPOINTMENT_PAYMENT`.

**Rationale:** Without a ledger, changes are not sufficiently auditable, testable, or debuggable.

## ADR-007 — WalletTransaction can reference Appointment

**Decision:** `WalletTransaction.appointment` is a nullable FK.

**Rationale:** `TOP_UP` has no appointment, while appointment payments must remain traceable to the booked appointment.

**Contract:** `APPOINTMENT_PAYMENT` requires an Appointment; `TOP_UP` requires Appointment = NULL; baseline scope allows at most one appointment-payment transaction for an Appointment.

## ADR-008 — Max one Review per completed Appointment

**Decision:** `Review.appointment` is OneToOne.

**Rationale:** The appointment is direct evidence that the user was visited and avoids duplicating user/doctor references.

**Business rule:** Review is allowed only when `Appointment.status == COMPLETED`.

## ADR-009 — Admin marks Appointment completed

**Decision:** Admin transitions an appointment from `CONFIRMED` to `COMPLETED`.

**Rationale:** There is no doctor panel in baseline, and elapsed time alone does not prove a visit occurred.

**Audit recommendation:** store `completed_at` and `completed_by`.

## ADR-010 — Cancellation/refund out of baseline scope

**Decision:** Baseline lifecycle contains only `CONFIRMED` and `COMPLETED`.

**Rationale:** Cancellation/refund is not a formal requirement and would add substantial financial and slot-release rules.

## ADR-011 — Simulated wallet top-up

**Decision:** A user enters a top-up amount and the system records `TOP_UP` without a real payment gateway.

**Rationale:** This makes the mandatory wallet-payment flow usable and testable without expanding scope to external payment integration.

## ADR-012 — OTP channel/storage/lifecycle

**Status:** **Pending final confirmation / not fully frozen**

### Original open questions

- Channel: Email or Phone?
- Storage: Database or Cache/Redis?
- Is OTP issued before User creation?
- Expiration time?
- Max attempts?
- Resend policy?
- One-time consumption?

### Current implementation evidence

The current `feature/account-authentication` branch uses:

- Email delivery through Django's email backend.
- Django Cache API for OTP, cooldown, attempt, and rate-limit state.
- Secure 6-digit generation.
- Hashed OTP storage and constant-time verification.
- 5-minute OTP TTL.
- 60-second resend cooldown.
- Maximum 5 verification attempts.
- Maximum 5 requests per 15-minute window.
- One-time consumption by deleting OTP state after successful verification.
- A new OTP replaces the previous cached OTP value for the same email.

### Evidence still requiring review before Accepted/Frozen

Issue #15 still requires additional/fixed tests and flow behavior, including:

- a real 5-requests-per-15-minutes rate-limit test rather than only immediate cooldown behavior;
- an explicit one-time-use test;
- a resend test proving the previous OTP becomes invalid;
- deterministic invalid-code testing;
- safe handling of email-send failure so stale OTP/cooldown state does not block the user;
- end-to-end registration, verification, resend, login, and logout integration tests.

Therefore the implementation direction is documented, but ADR-012 is not silently promoted to Accepted/Frozen until Issue #15 review/merge or explicit team confirmation.

### ERD consequence

No `OTPRequest` entity is part of the baseline ERD while cache-backed persistence remains the implementation direction. If the final decision changes to DB-backed persistence, the ERD and related UML must be updated through an explicit ADR change.

## Change rule

Any future change to these decisions must be recorded as a new ADR or explicit amendment with rationale and impact. Feature-branch code by itself does not supersede an accepted architecture decision.
