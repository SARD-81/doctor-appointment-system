class ReviewError(Exception):
    """Base exception for review domain failures."""


class ReviewOwnershipError(ReviewError):
    """Raised when the appointment does not exist for this patient (no data disclosure)."""


class AppointmentNotCompletedError(ReviewError):
    """Raised when a review is attempted before the appointment is COMPLETED."""


class ReviewAlreadyExistsError(ReviewError):
    """Raised when the appointment already has a review (pre-check or race-condition)."""
