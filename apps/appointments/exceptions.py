class BookingError(Exception):
    """Base exception for booking domain failures."""


class SlotUnavailableError(BookingError):
    """Raised when a slot cannot be booked (missing, inactive, past, or taken)."""


class InsufficientBalanceError(BookingError):
    """Raised when the patient's wallet cannot cover the visit fee."""

    def __init__(self, *, balance, required):
        self.balance = balance
        self.required = required
        super().__init__(
            f"Insufficient wallet balance: {balance} < {required}"
        )
