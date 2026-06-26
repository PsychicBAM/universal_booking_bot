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
    from app.models import Client
    from app.repositories import BookingRepository
    from app.services.language_service import resolve_client_lang_for_client
    from app.services.reminder_diagnostics import (
        REMINDER_SENT_AT_FIELDS,
        evaluate_admin_reminder,
        evaluate_client_reminder_1,
        evaluate_client_reminder_2,
        format_booking_reminder_state_lines,
    )
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
        clients: dict[int, Client | None] = {}
        for booking in bookings:
            if booking.client_id not in clients:
                clients[booking.client_id] = await session.get(Client, booking.client_id)

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
        client = clients.get(booking.client_id)
        telegram_id = client.telegram_id if client else None
        client_lang = await resolve_client_lang_for_client(client) if client else "n/a"
        print(
            f"#{booking.id}  start={start.strftime('%Y-%m-%d %H:%M')}  "
            f"in {delta:.1f} min  status={status}"
        )
        print(f"    client_telegram_id={telegram_id if telegram_id else 'MISSING'}")
        print(f"    client_language={client_lang}")
        print(f"    attendance_status={booking.attendance_status or 'none'}")
        for line in format_booking_reminder_state_lines(booking):
            print(line)

        c1 = evaluate_client_reminder_1(delta, config, booking)
        c2 = evaluate_client_reminder_2(delta, config, booking)
        adm = evaluate_admin_reminder(delta, config, booking)
        print(f"    client_reminder_1 due now: {c1.due}  reason: {c1.reason}")
        print(f"    client_reminder_2 due now: {c2.due}  reason: {c2.reason}")
        print(f"    admin_reminder due now: {adm.due}  reason: {adm.reason}")
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
