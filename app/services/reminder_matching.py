"""Reminder due-window matching (tolerant to 60s scheduler interval)."""

from __future__ import annotations

REMINDER_WINDOW_BELOW_MINUTES = 2.0
REMINDER_WINDOW_ABOVE_MINUTES = 1.0


def is_reminder_due(
    minutes_until_start: float,
    target_minutes: int,
    *,
    window_below: float = REMINDER_WINDOW_BELOW_MINUTES,
    window_above: float = REMINDER_WINDOW_ABOVE_MINUTES,
) -> bool:
    """
    True when the booking is within the reminder window before start.

    Example target=5, window_below=2, window_above=1 → due when 3 < minutes <= 6.
    Example target=1 → due when 0 < minutes <= 2.
    """
    if minutes_until_start <= 0:
        return False
    lower = max(0.0, float(target_minutes) - window_below)
    upper = float(target_minutes) + window_above
    return upper >= minutes_until_start > lower


def reminder_window_label(target_minutes: int) -> str:
    lower = max(0.0, float(target_minutes) - REMINDER_WINDOW_BELOW_MINUTES)
    upper = float(target_minutes) + REMINDER_WINDOW_ABOVE_MINUTES
    return f"({lower:.0f}–{upper:.0f} min before start)"
