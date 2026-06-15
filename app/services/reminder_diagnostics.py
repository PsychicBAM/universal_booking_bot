"""Reminder sent-flag field names and formatting for diagnostics."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.utils.datetime_utils import to_local_naive

# Active columns used by ReminderService to prevent duplicate sends.
REMINDER_SENT_AT_FIELDS: tuple[tuple[str, str], ...] = (
    ("client_reminder_1_sent_at", "Client reminder 1"),
    ("client_reminder_2_sent_at", "Client reminder 2"),
    ("admin_reminder_sent_at", "Admin reminder"),
)

# Legacy boolean columns (SQLite compatibility only; not used by ReminderService).
LEGACY_REMINDER_BOOL_FIELDS: tuple[tuple[str, str], ...] = (
    ("reminder_24h_sent", "Legacy 24h flag"),
    ("reminder_2h_sent", "Legacy 2h flag"),
    ("admin_reminder_sent", "Legacy admin flag (boolean)"),
)


def format_sent_at(value: datetime | None) -> str:
    if value is None:
        return "NULL"
    return to_local_naive(value).strftime("%Y-%m-%d %H:%M")


def reminder_was_sent(booking: Any, field: str) -> bool:
    return getattr(booking, field, None) is not None


def format_booking_reminder_state_lines(booking: Any) -> list[str]:
    """Human-readable reminder flag lines using real Booking column names."""
    lines: list[str] = []
    for field, _label in REMINDER_SENT_AT_FIELDS:
        value = getattr(booking, field, None)
        lines.append(f"    {field}={format_sent_at(value)}")
    legacy_present = any(hasattr(booking, field) for field, _ in LEGACY_REMINDER_BOOL_FIELDS)
    if legacy_present:
        for field, _label in LEGACY_REMINDER_BOOL_FIELDS:
            if hasattr(booking, field):
                lines.append(f"    {field}={getattr(booking, field)!r}  (legacy, ignored by scheduler)")
    return lines


def reminder_flags_summary_for_log(booking: Any) -> str:
    parts: list[str] = []
    for field, _label in REMINDER_SENT_AT_FIELDS:
        sent = reminder_was_sent(booking, field)
        parts.append(f"{field}={'set' if sent else 'null'}")
    return " ".join(parts)
