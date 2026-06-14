#!/usr/bin/env python3
"""Validate Google Calendar configuration without starting the bot."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _check_datetime_normalization() -> None:
    from datetime import datetime
    from zoneinfo import ZoneInfo

    from app.utils.datetime_utils import now_local, to_local_naive

    aware = datetime(2026, 6, 15, 12, 0, tzinfo=ZoneInfo("UTC"))
    naive = to_local_naive(aware)
    if naive.tzinfo is not None:
        raise AssertionError("to_local_naive must strip tzinfo")
    day_end = datetime.combine(naive.date(), datetime.max.time()).replace(microsecond=0)
    assert naive < day_end
    assert now_local() < day_end or now_local() >= datetime.combine(naive.date(), datetime.min.time())
    print("OK: Google busy datetime normalization regression passed")


async def main() -> int:
    from app.config import get_settings
    from app.database.session import async_session_factory, init_db
    from app.services.calendar_service import CalendarService

    settings = get_settings()
    print("=== Google Calendar check ===")
    print(f"GOOGLE_CALENDAR_ENABLED: {settings.google_calendar_enabled}")
    print(f"GOOGLE_CALENDAR_ID: {settings.google_calendar_id or 'primary'}")
    print(f"TIMEZONE: {settings.timezone}")

    # Import safety — should not crash when disabled
    try:
        from googleapiclient.discovery import build  # noqa: F401
        from google.oauth2.credentials import Credentials  # noqa: F401

        print("Google packages: installed")
    except ImportError as exc:
        print(f"Google packages: NOT installed ({exc})")
        if settings.google_calendar_enabled:
            print("WARNING: Calendar enabled but google-api-python-client is missing.")
            return 1

    await init_db()

    async with async_session_factory() as session:
        cal = CalendarService(session)
        await cal.log_startup_status()
        missing = await cal.get_missing_credentials()
        enabled = await cal.is_enabled()

        print(f"Effective sync enabled: {enabled}")
        if missing:
            print(f"Missing credentials: {', '.join(missing)}")
        else:
            print("Required credentials: present")

        if not settings.google_calendar_enabled:
            print("OK — disabled mode is safe.")
            _check_datetime_normalization()
            return 0

        if missing:
            print("WARNING — enabled but credentials incomplete. Booking works locally; sync skipped.")
            return 0

        if not enabled:
            print("INFO — credentials OK but admin sync toggle is off.")
            return 0

        result = await cal.test_connection()
        if result.ok:
            detail = result.detail or "OK"
            print(f"Connection test: SUCCESS ({detail})")
            _check_datetime_normalization()
            return 0

        if result.missing:
            print(f"Connection test: FAILED — missing {', '.join(result.missing)}")
        elif result.detail:
            print(f"Connection test: FAILED — {result.detail}")
        else:
            print(f"Connection test: FAILED — {result.message_key}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
