#!/usr/bin/env python3
"""Lightweight E2E smoke checks without Telegram API."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def check_handler_modules_importable() -> None:
    handler_modules = [
        "app.bot.handlers.admin",
        "app.bot.handlers.admin_attendance",
        "app.bot.handlers.admin_bookings",
        "app.bot.handlers.admin_clients",
        "app.bot.handlers.attendance",
        "app.bot.handlers.booking_edit",
        "app.bot.handlers.cancel",
        "app.bot.handlers.client",
        "app.bot.handlers.common",
        "app.bot.handlers.confirmation_settings",
        "app.bot.handlers.schedule",
        "app.bot.handlers.settings",
        "app.bot.handlers.support",
        "app.bot.handlers.working_hours",
    ]
    for module_name in handler_modules:
        __import__(module_name)


def check_label_builders() -> None:
    from datetime import datetime

    from app.bot.keyboards import bookings_kb
    from app.bot.utils.booking_labels import format_admin_booking_button, format_client_booking_button
    from app.models import BookingStatus
    from app.utils.formatting import format_service

    booking = SimpleNamespace(
        id=41,
        service_id=1,
        client_id=1,
        client_name="Test",
        start_at=datetime(2026, 6, 19, 9, 30),
        status=BookingStatus.CONFIRMED,
        attendance_status=None,
    )
    service = SimpleNamespace(
        name="Lesson",
        description="",
        duration_minutes=30,
        buffer_after_minutes=0,
        price=0,
    )

    client_label = format_client_booking_button(booking, "en", service_name="Lesson")
    if "#41" in client_label:
        raise AssertionError("client booking label must not include booking id")
    admin_label = format_admin_booking_button(booking, "ru")
    if "·" not in admin_label:
        raise AssertionError("admin booking label format")

    kb = bookings_kb([booking], "ru", {1: "Урок"})
    if kb.inline_keyboard[0][0].callback_data != "my:view:41":
        raise AssertionError("bookings_kb callback must preserve booking id")

    service_text = format_service(service, "ru")
    if "<b>" in service_text or "</b>" in service_text:
        raise AssertionError("format_service must be plain text")


async def smoke_reminder_service() -> None:
    from app.services.reminder_service import ReminderService

    bot = MagicMock()
    service = ReminderService(bot)

    disabled_config = SimpleNamespace(enabled=False)
    session = AsyncMock()
    session_cm = AsyncMock()
    session_cm.__aenter__.return_value = session
    session_cm.__aexit__.return_value = None

    with patch("app.services.reminder_service.async_session_factory", return_value=session_cm):
        with patch(
            "app.services.reminder_service.load_reminder_config",
            AsyncMock(return_value=disabled_config),
        ):
            await service.process_reminders()

    enabled_config = SimpleNamespace(
        enabled=True,
        test_mode=False,
        client_reminder_1_minutes=1440,
        client_reminder_2_minutes=120,
        admin_reminder_minutes=60,
        attendance_confirmation_enabled=True,
        test_client_reminder_minutes=5,
        test_admin_reminder_minutes=3,
    )
    with patch("app.services.reminder_service.async_session_factory", return_value=session_cm):
        with patch(
            "app.services.reminder_service.load_reminder_config",
            AsyncMock(return_value=enabled_config),
        ):
            with patch(
                "app.services.reminder_service.load_confirmation_text_config",
                AsyncMock(return_value=SimpleNamespace()),
            ):
                with patch(
                    "app.services.reminder_service.BookingRepository"
                ) as repo_cls:
                    repo = repo_cls.return_value
                    repo.list_for_reminders = AsyncMock(return_value=[])
                    session.commit = AsyncMock()
                    await service.process_reminders()


def main() -> int:
    print("=== Smoke E2E ===")
    try:
        check_handler_modules_importable()
        print("OK: handler modules import")
    except Exception as exc:
        print(f"FAIL: handler imports — {exc}")
        return 1

    try:
        check_label_builders()
        print("OK: booking label builders")
    except Exception as exc:
        print(f"FAIL: booking label builders — {exc}")
        return 1

    try:
        asyncio.run(smoke_reminder_service())
        print("OK: ReminderService.process_reminders smoke")
    except Exception as exc:
        print(f"FAIL: ReminderService smoke — {exc}")
        return 1

    try:
        import app.main  # noqa: F401

        print("OK: app.main import")
    except SystemExit:
        print("WARN: app.main exited during import (likely missing BOT_TOKEN)")
    except Exception as exc:
        print(f"FAIL: app.main import — {exc}")
        return 1

    print("=== Smoke E2E passed ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
