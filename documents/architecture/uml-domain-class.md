# UML 2 — Domain Class Diagram

The domain-class view captures responsibilities in addition to persistence.

```mermaid
classDiagram
    class User {
        +email: string
        +is_staff: bool
    }

    class Specialty {
        +name: string
    }

    class Doctor {
        +full_name: string
        +visit_fee: decimal
        +is_active: bool
    }

    class AppointmentSlot {
        +starts_at: datetime
        +is_active: bool
        +is_available(): bool
    }

    class Appointment {
        +status: CONFIRMED|COMPLETED
        +amount_paid: decimal
        +booked_at: datetime
        +completed_at: datetime?
    }

    class Wallet {
        +balance: decimal
    }

    class WalletTransaction {
        +type: TOP_UP|APPOINTMENT_PAYMENT
        +amount: decimal
        +balance_after: decimal
    }

    class Review {
        +rating: int
        +comment: string?
    }

    class OTPService {
        <<service / persistence pending final ADR>>
        +request(identifier)
        +verify(identifier, code)
    }

    class BookingService {
        <<service>>
        +book(patient, slot): Appointment
        -lock_slot()
        -lock_wallet()
        -validate_balance()
    }

    class WalletService {
        <<service>>
        +top_up(user, amount)
        +debit_for_appointment()
    }

    class ReviewService {
        <<service>>
        +create_review(user, appointment, rating, comment)
    }

    class NotificationService {
        <<service>>
        +send_booking_confirmation(appointment)
    }

    Specialty "1" --> "*" Doctor
    Doctor "1" --> "*" AppointmentSlot
    User "1" --> "*" Appointment : patient
    User "0..1" --> "*" Appointment : completed_by
    AppointmentSlot "1" --> "0..1" Appointment
    User "1" --> "1" Wallet
    Wallet "1" --> "*" WalletTransaction
    Appointment "0..1" --> "*" WalletTransaction : payment trace
    Appointment "1" --> "0..1" Review

    BookingService ..> AppointmentSlot
    BookingService ..> Wallet
    BookingService ..> Appointment
    BookingService ..> WalletTransaction
    BookingService ..> NotificationService : after commit

    WalletService ..> Wallet
    WalletService ..> WalletTransaction
    ReviewService ..> Appointment
    ReviewService ..> Review
    OTPService ..> User : auth context
```

## Responsibility rules

- `BookingService` owns the atomic booking orchestration and race-condition-sensitive locks.
- `WalletService` owns wallet mutations and ledger creation.
- `ReviewService` enforces the completed-appointment eligibility rule.
- `NotificationService` is invoked only after successful booking commit.
- OTP behavior is represented as a service boundary; persistence remains governed by ADR-012.
