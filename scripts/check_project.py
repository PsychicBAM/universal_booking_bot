#!/usr/bin/env python3
"""Compile-check the app and verify core imports."""

from __future__ import annotations

import compileall
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    print("=== Project check ===")

    ok = compileall.compile_dir(ROOT / "app", quiet=1)
    if not ok:
        print("FAIL: compileall reported errors in app/")
        return 1
    print("OK: app/ compiles")

    scripts_ok = compileall.compile_dir(ROOT / "scripts", quiet=1)
    if not scripts_ok:
        print("FAIL: compileall reported errors in scripts/")
        return 1
    print("OK: scripts/ compiles")

    try:
        from app.config import get_settings, parse_admin_ids  # noqa: F401
        from app.services.booking_service import BookingService  # noqa: F401
        from app.utils.datetime_utils import normalize_slot, now_local, to_local_naive  # noqa: F401

        print("OK: core imports load")
    except Exception as exc:
        print(f"FAIL: import error — {exc}")
        return 1

    admin_id_cases = {
        "123": [123],
        "123,456": [123, 456],
        "[123,456]": [123, 456],
        '"123,456"': [123, 456],
        "'[123,456]'": [123, 456],
        "": [],
    }
    for raw, expected in admin_id_cases.items():
        parsed = parse_admin_ids(raw)
        if parsed != expected:
            print(f"FAIL: parse_admin_ids({raw!r}) = {parsed}, expected {expected}")
            return 1
    print("OK: ADMIN_IDS parsing (comma-separated and JSON)")

    try:
        from types import SimpleNamespace

        from app.bot.utils.attendance_helpers import has_attendance_response
        from app.services.attendance_service import format_attendance_reminder_text
        from app.services.confirmation_text_service import (
            ConfirmationTextConfig,
            build_booking_confirmation_keyboard,
            resolve_confirmation_text,
        )

        booking = SimpleNamespace(
            attendance_status=None,
            attendance_reason=None,
            service_location_title="Office",
            service_location_address="Main St 1",
            location_text="Client addr",
        )
        empty_config = ConfirmationTextConfig(values={})
        text = format_attendance_reminder_text(
            booking, "Lesson", "01.01.2026 10:00", "ru", empty_config
        )
        if "Подтвердите, пожалуйста, актуальность вашей записи." not in text:
            print("FAIL: default RU confirmation question missing")
            return 1
        if "🔔 Подтверждение записи" not in text:
            print("FAIL: default RU confirmation title missing")
            return 1
        kb = build_booking_confirmation_keyboard(1, "ru", empty_config)
        if kb.inline_keyboard[0][0].text != "✅ Подтверждаю":
            print("FAIL: default RU yes button label")
            return 1
        custom_config = ConfirmationTextConfig(values={"confirm_yes_button_ru": "✅ Да, буду"})
        kb_custom = build_booking_confirmation_keyboard(1, "ru", custom_config)
        if kb_custom.inline_keyboard[0][0].text != "✅ Да, буду":
            print("FAIL: custom RU yes button label")
            return 1
        custom_en = ConfirmationTextConfig(
            values={"confirm_question_en": "Is your appointment still on?"}
        )
        if resolve_confirmation_text(custom_en, "en", "question") != "Is your appointment still on?":
            print("FAIL: custom EN question")
            return 1
        text_en = format_attendance_reminder_text(
            booking, "Lesson", "01.01.2026 10:00", "en", empty_config
        )
        if "Please confirm that your booking is still valid." not in text_en:
            print("FAIL: default EN confirmation question missing")
            return 1
        booking.attendance_status = "confirmed"
        if not has_attendance_response(booking):
            print("FAIL: attendance response detection")
            return 1
        print("OK: booking confirmation text formatting")

        from app.bot.keyboards.confirmation_settings_kb import (
            confirmation_language_select_kb,
            confirmation_main_text_kb,
            confirmation_responses_kb,
            confirmation_settings_main_kb,
        )
        from app.bot.settings_ui import shorten_text

        long = "x" * 100
        if len(shorten_text(long, 80)) != 80:
            print("FAIL: shorten_text length")
            return 1
        main_kb = confirmation_settings_main_kb("ru", "ru", multi_lang=False)
        if len(main_kb.inline_keyboard) != 5:
            print(f"FAIL: single-lang main kb has {len(main_kb.inline_keyboard)} rows, expected 5")
            return 1
        select_kb = confirmation_language_select_kb("ru")
        if len(select_kb.inline_keyboard) != 5:
            print(f"FAIL: language select kb has {len(select_kb.inline_keyboard)} rows, expected 5")
            return 1
        main_text_kb = confirmation_main_text_kb("ru", "ru")
        if len(main_text_kb.inline_keyboard) != 5:
            print(f"FAIL: main text group kb has {len(main_text_kb.inline_keyboard)} rows, expected 5")
            return 1
        responses_kb = confirmation_responses_kb("ru", "ru")
        if len(responses_kb.inline_keyboard) != 5:
            print(f"FAIL: responses group kb has {len(responses_kb.inline_keyboard)} rows, expected 5")
            return 1
        print("OK: confirmation settings UI keyboards")

        from app.bot.settings_ui import format_confirmation_language_menu_text

        menu_text = format_confirmation_language_menu_text(
            empty_config, "ru", "ru", multi_lang=True
        )
        if "—" not in menu_text:
            print("FAIL: multi-lang confirmation menu title missing language label")
            return 1
        print("OK: confirmation settings i18n placeholders")

        from app.services.reminder_matching import is_reminder_due

        if not is_reminder_due(4.8, 5):
            print("FAIL: test client reminder should be due at 4.8min with target 5")
            return 1
        if is_reminder_due(7.0, 5):
            print("FAIL: test client reminder should not be due at 7min with target 5")
            return 1
        if not is_reminder_due(1.2, 1):
            print("FAIL: test admin reminder should be due at 1.2min with target 1")
            return 1
        if is_reminder_due(2.5, 1):
            print("FAIL: test admin reminder should not be due at 2.5min with target 1")
            return 1
        print("OK: reminder due-window matching")

        from app.models import Booking
        from app.services.reminder_diagnostics import REMINDER_SENT_AT_FIELDS

        for field, _label in REMINDER_SENT_AT_FIELDS:
            if not hasattr(Booking, field):
                print(f"FAIL: Booking model missing reminder field {field}")
                return 1
        print("OK: reminder sent-at column names documented")

        from app.services.admin_attendance_service import (
            filter_upcoming_for_attendance,
            normalize_attendance_filter,
        )

        assert normalize_attendance_filter("invalid") == "7d"
        print("OK: admin attendance filters")
    except Exception as exc:
        print(f"FAIL: attendance check — {exc}")
        return 1

    # Regression: Google busy aware datetimes must compare safely with naive local datetimes
    try:
        from datetime import datetime
        from zoneinfo import ZoneInfo

        aware_utc = datetime(2026, 6, 15, 9, 0, tzinfo=ZoneInfo("UTC"))
        naive_local = to_local_naive(aware_utc)
        if naive_local.tzinfo is not None:
            raise AssertionError("to_local_naive must strip tzinfo")
        day_end = datetime.combine(naive_local.date(), datetime.max.time()).replace(microsecond=0)
        if not (naive_local < day_end):
            raise AssertionError("naive comparison failed")
        _ = now_local() < day_end
        print("OK: aware->naive datetime comparison safe")
    except Exception as exc:
        print(f"FAIL: datetime normalization regression — {exc}")
        return 1

    settings = get_settings()
    sample = normalize_slot.__name__
    print(f"TIMEZONE={settings.timezone}")
    print(f"normalize_slot={sample} (from app.utils.datetime_utils)")

    try:
        import app.main  # noqa: F401

        print("OK: app.main importable")
    except SystemExit:
        print("WARN: app.main exited during import (likely missing BOT_TOKEN in .env)")
    except Exception as exc:
        print(f"FAIL: app.main import — {exc}")
        return 1

    print("=== All checks passed ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
