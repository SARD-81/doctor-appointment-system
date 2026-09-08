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
                Service->>Service: register post-commit notification callback
                Note over Service,Ledger: COMMIT
            end
        end
    end

    opt booking transaction committed
        Service->>Email: run post-commit booking confirmation
        alt notification succeeds
            Email-->>Service: sent
        else notification fails
            Email-->>Service: failure
            Note over Service,View: isolate/log/retry notification failure; committed booking remains success
        end
        Service-->>View: Appointment
        View-->>Patient: HTTP success / confirmation page
    end

    Note over Service,Ledger: Any DB error rolls back all writes; no partial booking or debit
```

## Contract summary

- Slot row lock before availability validation.
- Wallet row lock before balance validation/debit.
- Appointment stores the fee snapshot.
- Wallet and ledger mutations are in the same transaction.
- The notification callback is registered for post-commit execution; email is never part of the database transaction.
- A post-commit email failure must not turn an already committed booking/payment into an HTTP booking failure. The implementation must isolate the callback exception and log/retry/report the notification separately (for example, Django `transaction.on_commit(..., robust=True)` or an equivalent guarded/durable mechanism).
- Database failure paths must leave no partial booking/payment state.
