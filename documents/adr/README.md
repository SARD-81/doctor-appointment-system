# Architecture Decision Records — Baseline v1.0

This index preserves traceability for ADR-001 through ADR-013. Statuses describe the agreed architecture baseline, not temporary feature-branch structure.

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
| ADR-013 | Payment snapshot range and zero-fee visits | Accepted amendment (PR #52 review feedback) |

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

**Contract:**

- `APPOINTMENT_PAYMENT` requires an Appointment.
- `TOP_UP` requires Appointment = NULL.
- Baseline scope allows at most one `APPOINTMENT_PAYMENT` transaction for an Appointment.
- The storage contract must enforce that stated maximum cardinality: a non-null `appointment_id` is unique for the baseline transaction types (or an equivalent conditional unique constraint is used for `APPOINTMENT_PAYMENT`). Multiple `TOP_UP` rows remain valid because their appointment reference is NULL.
- Transaction type and appointment nullability must be kept consistent with a database/application constraint rather than relying only on presentation logic.

This clarification makes the already-agreed “at most one appointment payment per Appointment” rule explicit in the ERD/storage contract; it does not add a new payment requirement.

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
- Registration/OTP/login forms and a custom email authentication backend are now present as additional implementation evidence, but Issue #15 remains the backend-contract review gate.

### Evidence still requiring review before Accepted/Frozen

Issue #15 remains open and still governs final backend/forms/authentication-contract acceptance, including correct email authentication behavior, inactive-user rejection, form validation/password handling, and the completed OTP lifecycle test suite.

Therefore the implementation direction is documented, but ADR-012 is not silently promoted to Accepted/Frozen until Issue #15 review/merge or explicit team confirmation.

### ERD consequence

No `OTPRequest` entity is part of the baseline ERD while cache-backed persistence remains the implementation direction. If the final decision changes to DB-backed persistence, the ERD and related UML must be updated through an explicit ADR change.

## ADR-013 — Payment snapshot decimal range and zero-fee visits

**Status:** Accepted amendment recorded from PR #52 review feedback; pending team re-review at merge.

**Decision:**

1. `Appointment.amount_paid` uses `max_digits=12` (`decimal_places=2`), aligned with `Doctor.visit_fee` and the Wallet money fields, so every storable doctor fee can be snapshotted without numeric overflow.
2. A `visit_fee` of `0` remains valid per the ERD (`visit_fee >= 0`). Zero-fee bookings create the `Appointment` without requiring a wallet, without a debit, and without an `APPOINTMENT_PAYMENT` ledger row, because the ledger contract (`WalletTransaction.amount > 0`) cannot store a zero payment.

**Rationale:** PR #52 review (Codex) flagged that the previous `max_digits=10` snapshot could overflow for valid fees and unhandled `IntegrityError` would surface as HTTP 500, and that a zero-fee insert would violate the ledger constraint. Skipping the wallet branch for free visits keeps the ledger contract honest instead of inventing zero-amount rows.

**Consequences:**

- Migration `appointments.0002_widen_amount_paid_digits` widens the snapshot field; no data rewrite is required.
- The fee snapshot remains auditable (`amount_paid` equals the doctor fee at booking time), including zero.
- The wallet lock/balance validation runs only when a payment is actually due.

## Change rule

Any future change to these decisions must be recorded as a new ADR or explicit amendment with rationale and impact. Feature-branch code by itself does not supersede an accepted architecture decision.