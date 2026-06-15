#!/usr/bin/env python3
"""Diagnose reminder configuration and upcoming booking eligibility."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


async def diagnose() -> int:
    from app.config import get_settings
    from app.database.session import async_session_factory
    from app.repositories import BookingRepository
    from app.services.reminder_diagnostics import (
        REMINDER_SENT_AT_FIELDS,
        format_booking_reminder_state_lines,
        reminder_was_sent,
    )
    from app.services.reminder_matching import is_reminder_due, reminder_window_label
    from app.services.reminder_settings import load_reminder_config
    from app.utils.datetime_utils import now_local, to_local_naive

    settings = get_settings()
    now = now_local()
    print(f"TIMEZONE={settings.timezone}")
    print(f"Now (local naive): {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("Reminder duplicate-prevention columns on bookings (datetime, NULL = not sent yet):")
    for field, label in REMINDER_SENT_AT_FIELDS:
        print(f"  - {field}  ({label})")
    print()
    print("Use this script instead of raw SQL with old names like client_reminder_1_sent.")
    print()

    async with async_session_factory() as session:
        config = await load_reminder_config(session)
        bookings = await BookingRepository(session).list_for_reminders(now)

    print(f"Reminders enabled: {config.enabled}")
    print(f"Test mode: {config.test_mode}")
    if config.test_mode:
        print(f"  Test client reminder: {config.test_client_reminder_minutes} min")
        print(f"  Test admin reminder: {config.test_admin_reminder_minutes} min")
    else:
        print(f"  Client reminder 1: {config.client_reminder_1_minutes} min")
        print(f"  Client reminder 2: {config.client_reminder_2_minutes} min")
        print(f"  Admin reminder: {config.admin_reminder_minutes} min")
    print(f"Attendance confirmation: {config.attendance_confirmation_enabled}")
    print(f"Bookings eligible for reminders: {len(bookings)}")
    print()

    if not bookings:
        print("No upcoming pending/confirmed bookings.")
        return 0

    print("Upcoming bookings (soonest first):")
    print("-" * 72)
    for booking in bookings[:25]:
        start = to_local_naive(booking.start_at)
        delta = (start - now).total_seconds() / 60
        status = booking.status.value if hasattr(booking.status, "value") else booking.status
        print(
            f"#{booking.id}  start={start.strftime('%Y-%m-%d %H:%M')}  "
            f"in {delta:.1f} min  status={status}"
        )
        for line in format_booking_reminder_state_lines(booking):
            print(line)
        print(f"    attendance_status={booking.attendance_status or 'none'}")

        if config.test_mode:
            ct = config.test_client_reminder_minutes
            at = config.test_admin_reminder_minutes
            client_due = (
                not reminder_was_sent(booking, "client_reminder_1_sent_at")
                and is_reminder_due(delta, ct)
            )
            admin_due = (
                not reminder_was_sent(booking, "admin_reminder_sent_at")
                and is_reminder_due(delta, at)
            )
            print(
                f"    client test due now: {client_due}  "
                f"(checks client_reminder_1_sent_at IS NULL)  "
                f"window={reminder_window_label(ct)}  target={ct}min"
            )
            print(
                f"    admin test due now: {admin_due}  "
                f"(checks admin_reminder_sent_at IS NULL)  "
                f"window={reminder_window_label(at)}  target={at}min"
            )
        else:
            c1_due = (
                not reminder_was_sent(booking, "client_reminder_1_sent_at")
                and delta > config.client_reminder_2_minutes
                and is_reminder_due(delta, config.client_reminder_1_minutes)
            )
            c2_due = (
                not reminder_was_sent(booking, "client_reminder_2_sent_at")
                and delta <= config.client_reminder_2_minutes
                and is_reminder_due(delta, config.client_reminder_2_minutes)
            )
            adm_due = (
                not reminder_was_sent(booking, "admin_reminder_sent_at")
                and is_reminder_due(delta, config.admin_reminder_minutes)
            )
            print(
                f"    client_reminder_1 due now: {c1_due}  "
                f"window={reminder_window_label(config.client_reminder_1_minutes)}"
            )
            print(
                f"    client_reminder_2 due now: {c2_due}  "
                f"window={reminder_window_label(config.client_reminder_2_minutes)}"
            )
            print(
                f"    admin_reminder due now: {adm_due}  "
                f"window={reminder_window_label(config.admin_reminder_minutes)}"
            )
        print()

    return 0


def main() -> int:
    try:
        return asyncio.run(diagnose())
    except Exception as exc:
        print(f"FAIL: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
