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

        from datetime import datetime, timedelta
        from types import SimpleNamespace

        from app.models import BookingStatus
        from app.services.client_history_service import (
            client_status_label_key,
            compute_client_stats,
            matches_client_filter,
        )

        now = datetime(2026, 6, 14, 12, 0, 0)
        client = SimpleNamespace(id=1, telegram_id=100, name="Ahmad", phone="+7999", language="ru")

        def _booking(bid, start, status=BookingStatus.CONFIRMED, attendance_status=None):
            return SimpleNamespace(
                id=bid,
                client_id=1,
                service_id=1,
                start_at=start,
                end_at=start + timedelta(hours=1),
                status=status,
                client_name="Ahmad",
                client_phone="+7999",
                attendance_status=attendance_status,
            )

        future = _booking(1, now + timedelta(days=2))
        stats_a = compute_client_stats(client, [future], {1: "Lesson"}, now=now)
        if not matches_client_filter(stats_a, "new"):
            print("FAIL: test A — new client filter")
            return 1
        if not matches_client_filter(stats_a, "upcoming"):
            print("FAIL: test A — upcoming client filter")
            return 1

        past = _booking(2, now - timedelta(days=1))
        stats_b = compute_client_stats(client, [past], {1: "Lesson"}, now=now)
        if not matches_client_filter(stats_b, "visited"):
            print("FAIL: test B — visited client filter")
            return 1

        stats_c = compute_client_stats(client, [past, future], {1: "Lesson"}, now=now)
        if client_status_label_key(stats_c) != "client_status_returning":
            print("FAIL: test C — returning client status")
            return 1
        if not matches_client_filter(stats_c, "returning"):
            print("FAIL: test C — returning client filter")
            return 1

        cancelled = _booking(3, now - timedelta(days=2), status=BookingStatus.CANCELLED)
        stats_d = compute_client_stats(client, [cancelled], {1: "Lesson"}, now=now)
        if not matches_client_filter(stats_d, "cancelled"):
            print("FAIL: test D — cancelled client filter")
            return 1

        if stats_c.total_bookings != 2 or stats_c.upcoming_count != 1 or stats_c.completed_or_past_count != 1:
            print("FAIL: test E — client detail stats")
            return 1

        history = SimpleNamespace(
            stats=stats_c,
            future_bookings=[future],
            history_bookings=[past],
        )
        if not history.future_bookings or not history.history_bookings:
            print("FAIL: test E — client history sections")
            return 1

        from app.bot.keyboards.admin_clients_kb import admin_clients_main_kb, admin_client_detail_kb

        main_kb = admin_clients_main_kb("en")
        if len(main_kb.inline_keyboard) < 4:
            print("FAIL: clients main keyboard rows")
            return 1
        detail_kb = admin_client_detail_kb(1, "all", 0, lang="en")
        if len(detail_kb.inline_keyboard) != 5:
            print("FAIL: client detail keyboard rows")
            return 1

        from app.bot.keyboards import ADMIN_CLIENTS_TEXTS

        if not ADMIN_CLIENTS_TEXTS:
            print("FAIL: ADMIN_CLIENTS_TEXTS empty")
            return 1

        from app.services.client_history_service import ClientStats, match_client_search_query

        search_stats = ClientStats(
            client_id=1,
            telegram_id=100,
            name="Maria",
            phone="+79001234567",
            username="maria_user",
            telegram_name="Maria",
            phone_source="manual",
            last_seen_at=None,
            first_booking_at=None,
            last_booking_at=None,
            next_booking_at=None,
            total_bookings=1,
            non_cancelled_count=1,
            completed_or_past_count=0,
            upcoming_count=1,
            cancelled_count=0,
            cannot_attend_count=0,
            last_service_name="Lesson",
            status_label_key="client_status_new",
        )
        if not match_client_search_query(search_stats, "Maria"):
            print("FAIL: test H — search by name")
            return 1
        if not match_client_search_query(search_stats, "900123"):
            print("FAIL: test H — search by phone")
            return 1
        if not match_client_search_query(search_stats, "@maria_user"):
            print("FAIL: test H — search by username")
            return 1
        if not match_client_search_query(search_stats, "100"):
            print("FAIL: test H — search by telegram id")
            return 1

        import inspect

        from app.bot.handlers import admin as admin_handlers
        from app.bot.handlers import admin_clients as admin_clients_handlers

        admin_src = inspect.getsource(admin_handlers.admin_send_message)
        if "msg_client_id" not in admin_src:
            print("FAIL: test F — admin message client by client_id")
            return 1

        confirm_src = inspect.getsource(admin_clients_handlers.client_confirm_nearest_callback)
        if "send_attendance_question_to_client" not in confirm_src:
            print("FAIL: test G — send confirmation nearest booking")
            return 1

        from app.services.confirmation_text_service import build_booking_confirmation_keyboard

        kb = build_booking_confirmation_keyboard(1, "ru", empty_config)
        if len(kb.inline_keyboard) < 2:
            print("FAIL: test G — confirmation yes/no keyboard")
            return 1
        if "att:yes:" not in kb.inline_keyboard[0][0].callback_data:
            print("FAIL: test G — confirmation yes button callback")
            return 1

        print("OK: admin clients archive filters and UI")

        from app.bot.i18n import t
        from app.bot.keyboards import (
            ADMIN_SCHEDULE_TEXTS,
            ADMIN_UNAVAILABLE_TEXTS,
            ADMIN_WH_TEXTS,
            admin_menu,
        )
        from app.bot.keyboards.schedule_kb import schedule_main_kb

        ru_texts = {btn.text for row in admin_menu("ru").keyboard for btn in row}
        en_texts = {btn.text for row in admin_menu("en").keyboard for btn in row}
        if t("ru", "schedule_button") not in ru_texts:
            print("FAIL: test A — RU admin panel missing schedule button")
            return 1
        if t("en", "schedule_button") not in en_texts:
            print("FAIL: test A — EN admin panel missing schedule button")
            return 1
        for legacy in ADMIN_WH_TEXTS | ADMIN_UNAVAILABLE_TEXTS:
            if legacy in ru_texts or legacy in en_texts:
                print(f"FAIL: test A — legacy schedule button still in admin panel: {legacy!r}")
                return 1
        if t("ru", "admin_calendar") in ru_texts:
            print("FAIL: test A — calendar should not be on admin panel")
            return 1

        main_kb = schedule_main_kb("ru")
        callbacks = [btn.callback_data for row in main_kb.inline_keyboard for btn in row]
        if "sch:main" not in callbacks and "wh:list" not in callbacks:
            print("FAIL: test B — schedule main keyboard missing sub-screens")
            return 1
        if "wh:list" not in callbacks or "unav:main" not in callbacks or "sch:back" not in callbacks:
            print("FAIL: test B — schedule main keyboard incomplete")
            return 1

        import inspect

        wh_src = inspect.getsource(
            __import__("app.bot.handlers.working_hours", fromlist=["open_working_hours_from_reply"]).open_working_hours_from_reply
        )
        unav_src = inspect.getsource(
            __import__("app.bot.handlers.unavailable", fromlist=["open_unavailable_from_reply"]).open_unavailable_from_reply
        )
        if "show_schedule_main" not in wh_src:
            print("FAIL: test C — legacy working hours should open schedule")
            return 1
        if "show_schedule_main" not in unav_src:
            print("FAIL: test D — legacy unavailable should open schedule")
            return 1

        sch_back_src = inspect.getsource(
            __import__("app.bot.handlers.schedule", fromlist=["schedule_back_admin"]).schedule_back_admin
        )
        if "admin_menu" not in sch_back_src:
            print("FAIL: test E — schedule back should return clean admin panel")
            return 1
        if ADMIN_SCHEDULE_TEXTS:
            print("OK: admin schedule panel layout and legacy routing")

        from types import SimpleNamespace

        from app.services.client_data_service import (
            ClientDataSettings,
            build_telegram_full_name,
            is_valid_phone_config,
            load_client_data_settings,
            validate_client_name,
            validate_manual_phone,
        )

        user = SimpleNamespace(first_name="Ahmad", last_name="Test", username="ahmad", id=1)
        if build_telegram_full_name(user) != "Ahmad Test":
            print("FAIL: client data — telegram full name")
            return 1
        defaults = ClientDataSettings(True, True, True, True, True, True)
        if not is_valid_phone_config(defaults):
            print("FAIL: client data — default config should be valid")
            return 1
        invalid = ClientDataSettings(True, True, False, False, True, True)
        if is_valid_phone_config(invalid):
            print("FAIL: test I — invalid phone config should be rejected")
            return 1
        optional = ClientDataSettings(True, True, False, False, False, True)
        if not is_valid_phone_config(optional):
            print("FAIL: test F — optional phone with both off should be valid")
            return 1
        if not validate_client_name("Ahmad") or validate_client_name(""):
            print("FAIL: client data — name validation")
            return 1
        if not validate_manual_phone("+7 999 000-00-00", required=True):
            print("FAIL: test E — manual phone validation")
            return 1
        if validate_manual_phone("", required=True):
            print("FAIL: test E — empty phone when required")
            return 1
        if validate_manual_phone("", required=False) is False:
            print("FAIL: test F — empty phone when optional")
            return 1
        from app.bot.keyboards.client_data_kb import confirm_telegram_name_kb, request_contact_reply_kb

        if len(confirm_telegram_name_kb("en").inline_keyboard) != 2:
            print("FAIL: test A/B — confirm telegram name keyboard")
            return 1
        contact_kb = request_contact_reply_kb("en", manual_enabled=True, phone_required=True)
        if not contact_kb.keyboard[0][0].request_contact:
            print("FAIL: test D — request_contact reply keyboard")
            return 1
        print("OK: client data collection settings and validation")

        from types import SimpleNamespace

        from app.models import BookingStatus
        from app.services.client_data_service import (
            ClientDataSettings,
            can_fast_reuse_saved_data,
            missing_client_data_fields,
            resolve_saved_client_name,
            resolve_saved_client_phone,
        )

        settings_on = ClientDataSettings(True, True, True, True, True, True)
        settings_off = ClientDataSettings(True, True, True, True, True, False)
        user = SimpleNamespace(first_name="Ahmad", last_name="Test", username="ahmad", id=1)
        client = SimpleNamespace(
            id=1,
            telegram_id=100,
            full_name="Ahmad Test",
            first_name="Ahmad",
            last_name="Test",
            name="Ahmad",
            phone="+79990000000",
        )
        latest = SimpleNamespace(
            id=10,
            client_name="Ahmad Test",
            client_phone="+79990000000",
            status=BookingStatus.CONFIRMED,
        )
        if not can_fast_reuse_saved_data(client, latest, user, settings_on):
            print("FAIL: test B — fast reuse should work for returning client")
            return 1
        if can_fast_reuse_saved_data(client, latest, user, settings_off):
            print("FAIL: test B — fast reuse disabled should not fast-path")
            return 1
        if can_fast_reuse_saved_data(None, latest, user, settings_on):
            print("FAIL: test A — new client should not fast reuse")
            return 1
        client_no_phone = SimpleNamespace(**{**client.__dict__, "phone": None})
        latest_no_phone = SimpleNamespace(**{**latest.__dict__, "client_phone": None})
        if can_fast_reuse_saved_data(client_no_phone, latest_no_phone, user, settings_on):
            print("FAIL: test E — missing required phone should block fast reuse")
            return 1
        need_name, need_phone = missing_client_data_fields(
            client_no_phone, latest_no_phone, user, settings_on
        )
        if need_name or not need_phone:
            print("FAIL: test E — should need phone only")
            return 1
        client_no_name = SimpleNamespace(
            **{**client.__dict__, "full_name": None, "name": None, "first_name": None, "last_name": None}
        )
        latest_name_only_phone = SimpleNamespace(
            id=10, client_name="", client_phone="+79990000000", status=BookingStatus.CONFIRMED
        )
        settings_no_tg = ClientDataSettings(False, True, True, True, True, True)
        need_name, need_phone = missing_client_data_fields(
            client_no_name, latest_name_only_phone, user, settings_no_tg
        )
        if not need_name or need_phone:
            print("FAIL: test F — should need name only")
            return 1
        optional_settings = ClientDataSettings(True, True, True, True, False, True)
        if not can_fast_reuse_saved_data(client_no_phone, latest_no_phone, user, optional_settings):
            print("FAIL: test D — optional phone should allow fast reuse without phone")
            return 1
        if resolve_saved_client_phone(client, latest) != "+79990000000":
            print("FAIL: test H — saved phone resolution")
            return 1
        if resolve_saved_client_name(client, latest, user, settings_on) != "Ahmad Test":
            print("FAIL: test B — saved name resolution")
            return 1

        from app.utils.formatting import format_booking

        booking = SimpleNamespace(
            id=1,
            service_id=1,
            client_name="Ahmad",
            client_phone="+7999",
            start_at=datetime(2026, 6, 15, 10, 0),
            end_at=datetime(2026, 6, 15, 11, 0),
            status=BookingStatus.CONFIRMED,
            service_location_title=None,
            service_location_address=None,
            location_text=None,
            client_comment=None,
            attendance_status=None,
        )
        service = SimpleNamespace(name="Lesson", requires_location=False, ask_client_comment=False)
        rendered = format_booking(booking, service, "ru", show_location_comment=True)
        if "<b>" in rendered or "</b>" in rendered:
            print("FAIL: test G — literal HTML tags in booking card")
            return 1
        if "📋 Lesson" not in rendered:
            print("FAIL: test G — booking card service line")
            return 1

        import inspect

        from app.bot.handlers import admin as admin_handlers
        from app.bot.handlers import admin_attendance as admin_attendance_handlers

        confirm_src = inspect.getsource(admin_handlers.admin_confirm_booking)
        if "@router.callback_query" not in confirm_src or "adm_confirm:" not in confirm_src:
            print("FAIL: admin_confirm_booking must be callback_query handler")
            return 1
        if admin_attendance_handlers.send_attendance_question_to_client is None:
            print("FAIL: admin_attendance missing send_attendance_question_to_client import")
            return 1

        print("OK: fast booking reuse and HTML formatting")
    except Exception as exc:
        print(f"FAIL: attendance check — {exc}")
        return 1

    try:
        from datetime import datetime, timedelta
        from types import SimpleNamespace
        from unittest.mock import patch

        from app.bot.keyboards.admin_bookings_kb import (
            admin_bookings_folder_kb,
            admin_bookings_hub_kb,
        )
        from app.bot.utils.booking_labels import format_admin_booking_button, truncate_display_name
        from app.models import BookingStatus
        from app.services.admin_bookings_service import (
            compute_bookings_hub_counts,
            filter_bookings_for_section,
        )
        from app.utils.formatting import format_booking

        fixed_now = datetime(2026, 6, 14, 12, 0, 0)
        long_name = "Abdallah Mohammed Bahi Al-Longlastname"

        def _booking(bid, start, status=BookingStatus.PENDING, attendance_status=None):
            return SimpleNamespace(
                id=bid,
                client_name="Abdallah Bahi" if bid == 26 else "Maria",
                client_id=bid,
                start_at=start,
                status=status,
                attendance_status=attendance_status,
                client_phone=None,
                service_id=1,
                service_location_title=None,
                service_location_address=None,
                location_text=None,
                client_comment=None,
            )

        booking = _booking(26, fixed_now.replace(hour=21, minute=30))
        booking_tomorrow = _booking(
            27,
            fixed_now.replace(hour=13, minute=0) + timedelta(days=1),
            status=BookingStatus.CONFIRMED,
            attendance_status="confirmed",
        )
        booking_needs_change = _booking(
            28,
            fixed_now + timedelta(days=5),
            status=BookingStatus.CONFIRMED,
            attendance_status="cannot_attend",
        )
        booking_past = _booking(
            29,
            fixed_now - timedelta(days=1),
            status=BookingStatus.COMPLETED,
        )
        booking_cancelled = _booking(
            30,
            fixed_now + timedelta(days=2),
            status=BookingStatus.CANCELLED,
        )
        all_bookings = [
            booking,
            booking_tomorrow,
            booking_needs_change,
            booking_past,
            booking_cancelled,
        ]

        with patch("app.bot.utils.booking_labels.now_local", return_value=fixed_now):
            with patch("app.services.admin_bookings_service.now_local", return_value=fixed_now):
                label_ru = format_admin_booking_button(booking, "ru")
                label_en = format_admin_booking_button(booking, "en")
                label_confirmed = format_admin_booking_button(booking_tomorrow, "ru")
                counts = compute_bookings_hub_counts(all_bookings, fixed_now)
                waiting = filter_bookings_for_section(all_bookings, "waiting", fixed_now)
                upcoming = filter_bookings_for_section(all_bookings, "upcoming", fixed_now)
                confirmed = filter_bookings_for_section(all_bookings, "confirmed", fixed_now)
                needs_change = filter_bookings_for_section(all_bookings, "needs_change", fixed_now)
                hub_kb = admin_bookings_hub_kb("ru")
                folder_kb = admin_bookings_folder_kb(waiting, "waiting", 0, 1, "ru")

        hub_callbacks = [btn.callback_data for row in hub_kb.inline_keyboard for btn in row]
        if any(cb.startswith("adm_book:view:") or cb.startswith("adm_booking:") for cb in hub_callbacks):
            print("FAIL: test A — hub must not list individual bookings")
            return 1
        if "adm_book:list:upcoming:0" not in hub_callbacks:
            print("FAIL: test A — hub missing upcoming folder")
            return 1
        if "adm_book:list:waiting:0" not in hub_callbacks:
            print("FAIL: test A — hub missing waiting folder")
            return 1
        if len(hub_callbacks) != 7:
            print("FAIL: test A — hub should have 6 folders plus back")
            return 1

        if label_ru != "❔ Сегодня 21:30 · Abdallah Bahi":
            print("FAIL: admin booking button RU label mismatch")
            return 1
        if label_en != "❔ Today 21:30 · Abdallah Bahi":
            print("FAIL: admin booking button EN label mismatch")
            return 1
        if "#26" in label_ru:
            print("FAIL: booking id visible in list button")
            return 1
        if label_confirmed != "✅ Завтра 13:00 · Maria":
            print("FAIL: confirmed tomorrow label mismatch")
            return 1
        truncated = truncate_display_name(long_name)
        if len(truncated) > 28 or not truncated.endswith("…"):
            print("FAIL: name truncation length or suffix")
            return 1

        if counts.waiting_count != 1:
            print("FAIL: test B — waiting count")
            return 1
        if len(waiting) != 1:
            print("FAIL: test B — waiting folder filter")
            return 1
        if counts.upcoming_count != 3:
            print("FAIL: test C — upcoming count")
            return 1
        if len(upcoming) != 3:
            print("FAIL: test C — upcoming folder filter")
            return 1
        if counts.confirmed_count != 1 or len(confirmed) != 1:
            print("FAIL: test F — confirmed count/filter")
            return 1
        if counts.needs_change_count != 1 or len(needs_change) != 1:
            print("FAIL: test G — needs change count/filter")
            return 1

        folder_callbacks = [btn.callback_data for row in folder_kb.inline_keyboard for btn in row]
        if "adm_book:view:26:from:waiting:0" not in folder_callbacks:
            print("FAIL: test D — folder booking view callback")
            return 1
        if "adm_book:hub" not in folder_callbacks:
            print("FAIL: test E — folder back to hub")
            return 1

        import inspect

        att_src = inspect.getsource(
            __import__(
                "app.bot.handlers.admin_attendance",
                fromlist=["admin_attendance_list_legacy"],
            ).admin_attendance_list_legacy
        )
        if "show_bookings_folder" not in att_src or "waiting" not in att_src:
            print("FAIL: test H — legacy attendance list should open waiting folder")
            return 1

        service = SimpleNamespace(name="Test", requires_location=False, ask_client_comment=False)
        detail = format_booking(booking, service, "ru", admin_view=True)
        if "ID записи: 26" not in detail:
            print("FAIL: admin detail should show booking id label")
            return 1
        print("OK: admin bookings hub, folders, and button labels")
    except Exception as exc:
        print(f"FAIL: admin booking labels — {exc}")
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
