class SlotUnavailableError(Exception):
    """Raised when a slot cannot be booked (race, overlap, or stale selection)."""

    def __init__(self, reason: str = "slot_unavailable", *, conflict_booking_id: int | None = None) -> None:
        self.reason = reason
        self.conflict_booking_id = conflict_booking_id
        super().__init__(reason)
