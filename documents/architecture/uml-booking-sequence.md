# UML 3 — Booking Sequence Diagram

This is the critical atomic booking flow.

```mermaid
sequenceDiagram
    actor Patient
    participant View as BookingView
    participant Service as BookingService
    participant Slot as AppointmentSlot
    participant Wallet
    participant Appointment
    participant Ledger as WalletTransaction
    participant Email as EmailService

    Patient->>View: POST selected slot
    View->>Service: book(patient, slot_id)

    rect rgb(238, 248, 247)
        Note over Service,Ledger: DB transaction.atomic()
        Service->>Slot: SELECT ... FOR UPDATE
        Slot-->>Service: slot state

        alt slot inactive or already booked
            Service-->>View: reject slot unavailable
            Note over Service,Wallet: rollback / no wallet change
        else slot available
            Service->>Wallet: SELECT ... FOR UPDATE
            Wallet-->>Service: balance

            alt insufficient balance
                Service-->>View: reject insufficient balance
                Note over Service,Ledger: rollback / no appointment or payment row
            else sufficient balance
                Service->>Appointment: CREATE CONFIRMED + amount_paid snapshot
                Service->>Wallet: UPDATE balance = balance - fee
                Service->>Ledger: CREATE APPOINTMENT_PAYMENT + FK Appointment
                Note over Service,Ledger: COMMIT
                Service->>Email: transaction.on_commit(send confirmation)
                Service-->>View: Appointment
                View-->>Patient: HTTP success / confirmation page
            end
        end
    end

    Note over Service,Ledger: Any DB error rolls back all writes; no partial booking or debit
```

## Contract summary

- Slot row lock before availability validation.
- Wallet row lock before balance validation/debit.
- Appointment stores the fee snapshot.
- Wallet and ledger mutations are in the same transaction.
- Email is a post-commit side effect.
- Failure paths must leave no partial booking/payment state.
