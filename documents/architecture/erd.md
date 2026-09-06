# ERD — Architecture Baseline v1.0

This diagram represents the agreed storage baseline. OTP persistence is intentionally excluded until ADR-012 is finalized.

```mermaid
erDiagram
    USER ||--|| WALLET : owns
    USER ||--o{ APPOINTMENT : books
    USER o|--o{ APPOINTMENT : completes_as_admin
    SPECIALTY ||--o{ DOCTOR : categorizes
    DOCTOR ||--o{ APPOINTMENT_SLOT : offers
    APPOINTMENT_SLOT ||--o| APPOINTMENT : becomes
    WALLET ||--o{ WALLET_TRANSACTION : records
    APPOINTMENT o|--o{ WALLET_TRANSACTION : payment_trace
    APPOINTMENT ||--o| REVIEW : receives

    USER {
        bigint id PK
        string username UK
        string email UK
        string first_name
        string last_name
        boolean is_active
        boolean is_staff
        datetime date_joined
    }

    SPECIALTY {
        bigint id PK
        string name UK
        datetime created_at
    }

    DOCTOR {
        bigint id PK
        bigint specialty_id FK
        string full_name
        decimal visit_fee
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    APPOINTMENT_SLOT {
        bigint id PK
        bigint doctor_id FK
        datetime starts_at
        boolean is_active
        datetime created_at
    }

    APPOINTMENT {
        bigint id PK
        bigint patient_id FK
        bigint slot_id FK
        string status
        decimal amount_paid
        datetime booked_at
        datetime completed_at
        bigint completed_by_id FK
    }

    WALLET {
        bigint id PK
        bigint user_id FK
        decimal balance
        datetime updated_at
    }

    WALLET_TRANSACTION {
        bigint id PK
        bigint wallet_id FK
        bigint appointment_id FK
        string type
        decimal amount
        decimal balance_after
        datetime created_at
    }

    REVIEW {
        bigint id PK
        bigint appointment_id FK
        int rating
        text comment
        datetime created_at
        datetime updated_at
    }
```

## Required constraints

- `User.email` unique.
- `Specialty.name` unique.
- `Doctor.visit_fee >= 0`.
- `(doctor_id, starts_at)` unique for slots.
- `Appointment.slot_id` unique.
- `Appointment.amount_paid >= 0`.
- `Wallet.user_id` unique.
- `Wallet.balance >= 0`.
- `WalletTransaction.amount > 0`.
- `WalletTransaction.balance_after >= 0`.
- `Review.appointment_id` unique.
- `Review.rating` between 1 and 5.

## Notes

- Slot availability is derived from the existence/absence of an Appointment plus slot activity; no independent `is_booked` field is part of the baseline.
- `Appointment.amount_paid` is a historical fee snapshot.
- `WalletTransaction.appointment_id` is nullable because `TOP_UP` has no appointment.
- For `APPOINTMENT_PAYMENT`, an appointment reference is required by the application contract.
- OTP persistence remains outside the ERD until ADR-012 is finalized.
