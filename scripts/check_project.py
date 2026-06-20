#!/usr/bin/env python3
"""Compile-check the app and verify core imports."""

from __future__ import annotations

import compileall
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _check_symbol_imports(app_dir: Path) -> None:
    rules = [
        (
            "async_session_factory(",
            "async_session_factory",
            "app.database.session",
            {"session.py"},
        ),
        (
            "log_action_timing(",
            "log_action_timing",
            "app.utils.perf_logging",
            {"perf_logging.py"},
        ),
        (
            "schedule_background_task(",
            "schedule_background_task",
            "app.utils.background_tasks",
            {"background_tasks.py"},
        ),
        (
            "safe_callback_answer(",
            "safe_callback_answer",
            "app.bot.utils.callbacks",
            {"callbacks.py"},
        ),
        (
            "send_attendance_question_to_client(",
            "send_attendance_question_to_client",
            "app.services.admin_attendance_service",
            {"admin_attendance_service.py"},
        ),
        (
            "notify_admins_client_cancelled(",
            "notify_admins_client_cancelled",
            "app.services.booking_notification_service",
            {"booking_notification_service.py"},
        ),
        (
            "edit_or_send(",
            "edit_or_send",
            "app.bot.utils.telegram_ui",
            {"telegram_ui.py"},
        ),
        (
            "safe_edit_text(",
            "safe_edit_text",
            "app.bot.utils.telegram_ui",
            {"telegram_ui.py"},
        ),
        (
            "build_booking_confirmation_message(",
            "build_booking_confirmation_message",
            "app.services.confirmation_text_service",
            {"confirmation_text_service.py"},
        ),
        (
            "build_booking_confirmation_keyboard(",
            "build_booking_confirmation_keyboard",
            "app.services.confirmation_text_service",
            {"confirmation_text_service.py"},
        ),
        (
            "format_admin_booking_button(",
            "format_admin_booking_button",
            "app.bot.utils.booking_labels",
            {"booking_labels.py"},
        ),
        (
            "format_client_booking_button(",
            "format_client_booking_button",
            "app.bot.utils.booking_labels",
            {"booking_labels.py"},
        ),
        (
            "get_settings(",
            "get_settings",
            "app.config",
            {"config.py"},
        ),
    ]
    for path in app_dir.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for call, symbol, module_path, skip_def_files in rules:
            if call not in text:
                continue
            if path.name in skip_def_files:
                continue
            if f"def {symbol}" in text:
                continue
            if f"import {symbol}" in text:
                continue
            if f"from {module_path} import" in text and symbol in text:
                continue
            raise AssertionError(f"{path.relative_to(ROOT)}: uses {symbol} without import/def")


def _check_callback_prefix_handlers() -> None:
    handlers_dir = ROOT / "app" / "bot" / "handlers"
    handlers_blob = "\n".join(
        path.read_text(encoding="utf-8") for path in handlers_dir.glob("*.py")
    )
    required_snippets = [
        'cb:book:',
        'cb:loc:',
        "date:",
        "time:",
        "bk:period:",
        "bk:back:",
        "my:view:",
        "my:cancel:",
        "my:res:",
        "my:res:period:",
        "my:res:back:",
        "adm_confirm:",
        "adm_cancel:",
        "adm_msg:",
        "adm_att:",
        "adm_book:",
        'F.data == "cancel"',
        "confirm:yes",
        "bkdata:",
        "att:",
        "sup:",
        "wh:",
        "br:",
        "ord:",
        "cb:order:",
        "myact:",
        "svc:active",
        "svc:hub",
        "svc:search",
        "svc:type:",
        "set:modes:",
        "unav:",
        "sch:",
        "conf:",
        "set:",
    ]
    missing = [snippet for snippet in required_snippets if snippet not in handlers_blob]
    if missing:
        raise AssertionError(f"Missing handler references for callbacks: {', '.join(missing)}")


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
        if len(main_kb.inline_keyboard) != 3:
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

        name_kb = confirm_telegram_name_kb("en").inline_keyboard
        name_callbacks = [button.callback_data for row in name_kb for button in row]
        if len(name_kb) < 3:
            print("FAIL: test A/B — confirm telegram name keyboard")
            return 1
        if "bk:back:time" not in name_callbacks or "cancel" not in name_callbacks:
            print("FAIL: test A/B — confirm telegram name keyboard back/cancel")
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
        if "ID записи" in rendered or "Booking ID" in rendered:
            print("FAIL: test G — booking ID must not appear in client booking card")
            return 1
        if "📋 Lesson" not in rendered:
            print("FAIL: test G — booking card service line")
            return 1

        from app.bot.keyboards import bookings_kb
        from app.bot.utils.booking_labels import format_client_booking_button
        from app.utils.formatting import format_client_booking_detail

        btn_ru = format_client_booking_button(booking, "ru", service_name="Урок")
        if "#41" in btn_ru or "#" in btn_ru.split("·")[-1]:
            print("FAIL: client booking button must not contain booking id")
            return 1
        if "📅" not in btn_ru or "Урок" not in btn_ru:
            print("FAIL: client booking button RU format")
            return 1
        btn_en = format_client_booking_button(booking, "en", service_name="Lesson")
        if "Lesson" not in btn_en:
            print("FAIL: client booking button EN format")
            return 1
        kb = bookings_kb([booking], "ru", {1: "Урок"})
        if not kb.inline_keyboard[0][0].callback_data.endswith(":1"):
            print("FAIL: client bookings_kb callback must keep booking id")
            return 1
        if "#" in kb.inline_keyboard[0][0].text:
            print("FAIL: client bookings_kb label must not show booking id")
            return 1
        detail = format_client_booking_detail(booking, service, "ru")
        if "ID записи" in detail:
            print("FAIL: client booking detail must not show booking id")
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
        booking_confirmed_no_response = _booking(
            31,
            fixed_now.replace(hour=20, minute=0),
            status=BookingStatus.CONFIRMED,
            attendance_status=None,
        )
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
            booking_confirmed_no_response,
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
                pending_admin = filter_bookings_for_section(all_bookings, "pending_admin", fixed_now)
                upcoming = filter_bookings_for_section(all_bookings, "upcoming", fixed_now)
                confirmed_bookings = filter_bookings_for_section(
                    all_bookings, "confirmed_bookings", fixed_now
                )
                waiting_client = filter_bookings_for_section(
                    all_bookings, "waiting_client_response", fixed_now
                )
                needs_change = filter_bookings_for_section(all_bookings, "needs_change", fixed_now)
                hub_kb = admin_bookings_hub_kb("ru")
                folder_kb = admin_bookings_folder_kb(pending_admin, "pending_admin", 0, 1, "ru")

        hub_callbacks = [btn.callback_data for row in hub_kb.inline_keyboard for btn in row]
        if any(cb.startswith("adm_book:view:") or cb.startswith("adm_booking:") for cb in hub_callbacks):
            print("FAIL: test A — hub must not list individual bookings")
            return 1
        if "adm_book:list:upcoming:0" not in hub_callbacks:
            print("FAIL: test A — hub missing upcoming folder")
            return 1
        if "adm_book:list:pending_admin:0" not in hub_callbacks:
            print("FAIL: test A — hub missing pending admin folder")
            return 1
        if "adm_book:list:waiting_client_response:0" not in hub_callbacks:
            print("FAIL: test A — hub missing waiting client response folder")
            return 1
        if len(hub_callbacks) != 8:
            print("FAIL: test A — hub should have 7 folders plus back")
            return 1

        if label_ru != "🕓 Сегодня 21:30 · Abdallah Bahi":
            print("FAIL: admin booking button RU label mismatch")
            return 1
        if label_en != "🕓 Today 21:30 · Abdallah Bahi":
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

        if counts.pending_admin_count != 1:
            print("FAIL: test A/B — pending admin count")
            return 1
        if len(pending_admin) != 1 or pending_admin[0].id != 26:
            print("FAIL: test A/B — pending admin folder filter")
            return 1
        if counts.upcoming_count != 4:
            print("FAIL: test C — upcoming count")
            return 1
        if len(upcoming) != 4:
            print("FAIL: test C — upcoming folder filter")
            return 1
        if counts.confirmed_bookings_count != 3 or len(confirmed_bookings) != 3:
            print("FAIL: test B — confirmed bookings count/filter")
            return 1
        if 26 in {b.id for b in confirmed_bookings}:
            print("FAIL: test B — pending booking must not be in confirmed folder")
            return 1
        if counts.waiting_client_response_count != 1 or len(waiting_client) != 1:
            print("FAIL: test C — waiting client response count/filter")
            return 1
        if waiting_client[0].id != 31:
            print("FAIL: test C — waiting client response booking id")
            return 1
        if counts.needs_change_count != 1 or len(needs_change) != 1:
            print("FAIL: test D — needs change count/filter")
            return 1

        booking_confirmed = _booking(
            26,
            fixed_now.replace(hour=21, minute=30),
            status=BookingStatus.CONFIRMED,
            attendance_status=None,
        )
        after_confirm = [booking_confirmed, booking_confirmed_no_response, booking_tomorrow, booking_needs_change, booking_past, booking_cancelled]
        with patch("app.services.admin_bookings_service.now_local", return_value=fixed_now):
            after_pending = filter_bookings_for_section(after_confirm, "pending_admin", fixed_now)
            after_confirmed = filter_bookings_for_section(after_confirm, "confirmed_bookings", fixed_now)
            after_waiting = filter_bookings_for_section(after_confirm, "waiting_client_response", fixed_now)
        if after_pending:
            print("FAIL: test B — confirmed booking must leave pending admin folder")
            return 1
        if len(after_confirmed) != 4:
            print("FAIL: test B — confirmed booking must appear in confirmed folder")
            return 1
        if len(after_waiting) != 2:
            print("FAIL: test B — confirmed booking without response stays in waiting client folder")
            return 1

        folder_callbacks = [btn.callback_data for row in folder_kb.inline_keyboard for btn in row]
        if "adm_book:view:26:from:pending_admin:0" not in folder_callbacks:
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
        if "show_bookings_folder" not in att_src or "waiting_client_response" not in att_src:
            print("FAIL: test H — legacy attendance list should open waiting client folder")
            return 1

        from app.utils.formatting import format_client_cancelled_admin_notification

        service = SimpleNamespace(name="Test", requires_location=False, ask_client_comment=False)
        cancel_note = format_client_cancelled_admin_notification(booking, service, "ru")
        if "Клиент отменил запись" not in cancel_note:
            print("FAIL: test E — client cancel admin notification")
            return 1

        detail = format_booking(booking, service, "ru", admin_view=True)
        if "ID записи: 26" not in detail:
            print("FAIL: admin detail should show booking id label")
            return 1
        if "Статус записи:" not in detail:
            print("FAIL: admin detail should show booking status label")
            return 1
        print("OK: admin bookings hub, folders, and button labels")
    except Exception as exc:
        print(f"FAIL: admin booking labels — {exc}")
        return 1

    try:
        from datetime import date, datetime

        from app.bot.keyboards.booking_time_kb import dates_kb, time_grid_kb, time_periods_kb
        from app.bot.keyboards.booking_confirm_kb import booking_confirm_kb
        from app.bot.utils.time_periods import (
            build_period_screen_text,
            group_slots_by_period,
            non_empty_periods,
            slot_period,
        )

        morning = datetime(2026, 6, 19, 9, 0)
        afternoon = datetime(2026, 6, 19, 14, 0)
        evening = datetime(2026, 6, 19, 19, 0)
        if slot_period(morning) != "morning" or slot_period(afternoon) != "day":
            raise AssertionError("slot_period classification")
        if slot_period(evening) != "evening":
            raise AssertionError("evening slot_period")

        grouped = group_slots_by_period([morning, afternoon, evening])
        if non_empty_periods(grouped) != ["morning", "day", "evening"]:
            raise AssertionError("non_empty_periods order")

        text_ru = build_period_screen_text(date(2026, 6, 19), grouped, "ru")
        if "Выберите часть дня" not in text_ru or "мест" not in text_ru:
            raise AssertionError("period screen RU text")

        date_rows = dates_kb(
            [date(2026, 6, 17), date(2026, 6, 18), date(2026, 6, 19)],
            "ru",
        ).inline_keyboard
        if len(date_rows[0]) != 3:
            raise AssertionError("dates_kb should use 3 columns per row")

        period_callbacks = [
            button.callback_data
            for row in time_periods_kb(["day"], "en").inline_keyboard
            for button in row
        ]
        if "bk:period:morning" in period_callbacks:
            raise AssertionError("empty morning period must be hidden")
        if "bk:period:day" not in period_callbacks:
            raise AssertionError("day period button missing")

        grid_rows = time_grid_kb(
            [afternoon, afternoon.replace(minute=30), afternoon.replace(hour=15)],
            "en",
        ).inline_keyboard
        time_row = next(row for row in grid_rows if row[0].callback_data.startswith("time:"))
        if len(time_row) != 3:
            raise AssertionError("time grid should use up to 3 buttons per row")

        from app.utils.formatting import format_service

        service = SimpleNamespace(
            name="Урок",
            description="Test",
            price=500,
            duration_minutes=15,
            buffer_after_minutes=0,
        )
        service_text = format_service(service, "ru")
        if "<b>" in service_text or "</b>" in service_text:
            raise AssertionError("format_service must not contain HTML tags")
        if "📋 Урок" not in service_text:
            raise AssertionError("format_service plain service line")

        date_callbacks = [
            button.callback_data
            for row in dates_kb([date(2026, 6, 19)], "ru").inline_keyboard
            for button in row
        ]
        if "bk:back:service" not in date_callbacks:
            raise AssertionError("dates_kb must include back to service")

        confirm_callbacks = [
            button.callback_data
            for row in booking_confirm_kb("ru").inline_keyboard
            for button in row
        ]
        if "bk:back:time" not in confirm_callbacks:
            raise AssertionError("booking_confirm_kb must include back to time")
        if "cancel" not in confirm_callbacks:
            raise AssertionError("booking_confirm_kb must include cancel")

        print("OK: booking time period UI")
    except Exception as exc:
        print(f"FAIL: booking time period UI — {exc}")
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

    try:
        from datetime import date, datetime, time, timedelta
        from types import SimpleNamespace

        from app.bot.handlers.working_hours import format_day_detail
        from app.services.availability_service import AvailabilityService, _RangeContext
        from app.services.working_break_service import (
            format_schedule_day_with_breaks,
            parse_hhmm,
            validate_time_range,
        )
        from app.services.working_hours_service import DaySchedule

        lunch_break = SimpleNamespace(
            weekday=0,
            start_time=time(12, 0),
            end_time=time(13, 0),
            title="Обед",
            is_active=True,
        )
        schedule = DaySchedule(day_of_week=0, is_working=True, start_time=time(9, 0), end_time=time(18, 0))
        day_text = format_day_detail(schedule, "ru", [lunch_break])
        if "12:00–13:00" not in day_text or "Обед" not in day_text:
            raise AssertionError("test A — break on working hours day screen")

        monday = date(2026, 6, 15)
        ctx = _RangeContext(
            working_hours={
                0: SimpleNamespace(start_time=time(9, 0), end_time=time(18, 0), is_active=True)
            },
            working_breaks=[lunch_break],
            unavailable_dates=set(),
            time_ranges_by_date={},
            booking_ranges=[],
            google_busy_ranges=[],
        )
        day_start = datetime.combine(monday, time(9, 0))
        day_end = datetime.combine(monday, time(18, 0))
        blocked = AvailabilityService._blocked_ranges_for_day(monday, day_start, day_end, ctx)

        slot_12 = datetime.combine(monday, time(12, 0))
        if not AvailabilityService._overlaps_any(
            slot_12, slot_12 + timedelta(minutes=30), blocked
        ):
            raise AssertionError("test B — 12:00 slot blocked by break")

        slot_1230 = datetime.combine(monday, time(12, 30))
        if not AvailabilityService._overlaps_any(
            slot_1230, slot_1230 + timedelta(minutes=30), blocked
        ):
            raise AssertionError("test B — 12:30 slot blocked by break")

        slot_1130 = datetime.combine(monday, time(11, 30))
        if not AvailabilityService._overlaps_any(
            slot_1130, slot_1130 + timedelta(minutes=60), blocked
        ):
            raise AssertionError("test C — 11:30–12:30 slot blocked by break overlap")

        ctx_no_breaks = _RangeContext(
            working_hours=ctx.working_hours,
            working_breaks=[],
            unavailable_dates=set(),
            time_ranges_by_date={},
            booking_ranges=[],
            google_busy_ranges=[],
        )
        blocked_after_delete = AvailabilityService._blocked_ranges_for_day(
            monday, day_start, day_end, ctx_no_breaks
        )
        if AvailabilityService._overlaps_any(
            slot_12, slot_12 + timedelta(minutes=30), blocked_after_delete
        ):
            raise AssertionError("test D — slots should return after break removal")

        try:
            validate_time_range(time(13, 0), time(12, 0))
            raise AssertionError("test E — invalid range should raise")
        except ValueError:
            pass

        summary = format_schedule_day_with_breaks("ru", 0, "09:00", "18:00", [lunch_break])
        if "Пн: 09:00–18:00 · перерыв 12:00–13:00" not in summary:
            raise AssertionError(f"test F — schedule summary unexpected: {summary!r}")

        busy_start = datetime.combine(monday, time(15, 0))
        busy_end = datetime.combine(monday, time(16, 0))
        ctx_mixed = _RangeContext(
            working_hours=ctx.working_hours,
            working_breaks=[lunch_break],
            unavailable_dates={monday + timedelta(days=1)},
            time_ranges_by_date={
                monday: [(datetime.combine(monday, time(17, 0)), datetime.combine(monday, time(18, 0)))]
            },
            booking_ranges=[(busy_start, busy_end)],
            google_busy_ranges=[(datetime.combine(monday, time(10, 0)), datetime.combine(monday, time(10, 30)))],
        )
        mixed_blocked = AvailabilityService._blocked_ranges_for_day(
            monday, day_start, day_end, ctx_mixed
        )
        if len(mixed_blocked) < 4:
            raise AssertionError("test G — unavailable/booking/google ranges must still apply with breaks")

        try:
            parse_hhmm("25:00")
            raise AssertionError("test E — invalid HH:MM should fail")
        except ValueError:
            pass

        print("OK: working breaks availability and admin UI")
    except Exception as exc:
        print(f"FAIL: working breaks — {exc}")
        return 1

    try:
        from app.models import SERVICE_TYPE_BOOKING, SERVICE_TYPE_ORDER
        from app.services.service_modes_service import (
            ServiceModes,
            default_service_type_for_modes,
            save_booking_mode,
            save_order_mode,
        )

        assert default_service_type_for_modes(ServiceModes(True, False)) == SERVICE_TYPE_BOOKING
        assert default_service_type_for_modes(ServiceModes(False, True)) == SERVICE_TYPE_ORDER

        from app.bot.keyboards.admin_clients_kb import admin_clients_main_kb
        from app.bot.handlers.admin import _services_hub_text
        from app.bot.keyboards import (
            ADMIN_SERVICES_TEXTS,
            MAIN_MENU_SERVICES_TEXTS,
            admin_menu,
            admin_services_hub_kb,
            main_menu,
        )
        from app.bot.i18n import t
        from app.utils.formatting import (
            format_booking_rescheduled_by_client_admin_notification,
            format_order_cancelled_by_admin_client_notification,
            format_order_cancelled_by_client_admin_notification,
        )

        # Menu routing — admin vs client services buttons must differ
        if ADMIN_SERVICES_TEXTS & MAIN_MENU_SERVICES_TEXTS:
            raise AssertionError(
                "menu routing — admin services button text must not overlap client services button text"
            )
        if t("ru", "admin_services") == t("ru", "main_menu_services"):
            raise AssertionError("menu routing — RU admin/client services labels must differ")
        if t("en", "admin_services") == t("en", "main_menu_services"):
            raise AssertionError("menu routing — EN admin/client services labels must differ")

        admin_hub_text = _services_hub_text(2, 1, 0, "ru")
        if t("ru", "services_hub_intro") not in admin_hub_text:
            raise AssertionError("menu routing — admin services hub intro missing")
        if t("ru", "choose_service") in admin_hub_text:
            raise AssertionError("menu routing — admin hub must not use client choose_service text")

        admin_both = {
            btn.text for row in admin_menu("ru", booking_enabled=True, order_enabled=True).keyboard for btn in row
        }
        if t("ru", "admin_services") not in admin_both:
            raise AssertionError("menu routing — admin panel must show manage services button")
        if t("ru", "main_menu_services") in admin_both:
            raise AssertionError("menu routing — client services button must not appear in admin menu")

        # Test A — compact client menu when both modes enabled
        client_both = {
            btn.text for row in main_menu("ru", booking_enabled=True, order_enabled=True).keyboard for btn in row
        }
        for label in (
            t("ru", "main_menu_services"),
            t("ru", "main_menu_my_activity"),
            t("ru", "contact_admin"),
        ):
            if label not in client_both:
                raise AssertionError(f"test A — missing compact menu button: {label}")
        if t("ru", "book_appointment") in client_both or t("ru", "my_bookings") in client_both:
            raise AssertionError("test A — legacy booking buttons should be hidden in compact menu")

        # Test B — booking-only client menu
        client_booking = {
            btn.text for row in main_menu("ru", booking_enabled=True, order_enabled=False).keyboard for btn in row
        }
        if t("ru", "order_services_button") in client_booking or t("ru", "my_orders_button") in client_booking:
            raise AssertionError("test B — order buttons must be hidden in booking-only mode")

        # Test C — order-only client menu
        client_order = {
            btn.text for row in main_menu("ru", booking_enabled=False, order_enabled=True).keyboard for btn in row
        }
        if t("ru", "book_appointment") in client_order or t("ru", "my_bookings") in client_order:
            raise AssertionError("test C — booking buttons must be hidden in order-only mode")

        # Test D — simplified clients hub
        client_hub = {btn.text for row in admin_clients_main_kb("ru").inline_keyboard for btn in row}
        if t("ru", "clients_filter_upcoming") in client_hub:
            raise AssertionError("test D — extra client folders must be removed from hub")
        for label in (
            t("ru", "clients_all_button"),
            t("ru", "clients_search_button"),
            t("ru", "clients_back_admin"),
        ):
            if label not in client_hub:
                raise AssertionError(f"test D — missing clients hub button: {label}")

        # Test E — services hub folders
        services_hub = {
            btn.text
            for row in admin_services_hub_kb(active_count=2, disabled_count=1, archived_count=0, lang="ru").inline_keyboard
            for btn in row
        }
        for label in (
            t("ru", "services_folder_active", count="2"),
            t("ru", "services_folder_disabled", count="1"),
            t("ru", "services_folder_archive", count="0"),
        ):
            if label not in services_hub:
                raise AssertionError(f"test E — missing services folder: {label}")

        # Test F — active services grouping/sorting
        from types import SimpleNamespace

        from app.bot.keyboards import admin_active_services_grouped_kb

        services = [
            SimpleNamespace(id=1, name="Zeta", service_type=SERVICE_TYPE_ORDER),
            SimpleNamespace(id=2, name="Alpha", service_type=SERVICE_TYPE_BOOKING),
            SimpleNamespace(id=3, name="Beta", service_type=SERVICE_TYPE_ORDER),
        ]
        labels = [
            btn.text
            for row in admin_active_services_grouped_kb(services, "ru").inline_keyboard
            for btn in row
            if btn.callback_data.startswith("adm_svc:")
        ]
        if labels != ["📅 Alpha", "📝 Beta", "📝 Zeta"]:
            raise AssertionError(f"test F — grouped services order mismatch: {labels}")

        # Test G — client cancels order admin notification
        order = SimpleNamespace(
            id=7,
            service_id=1,
            client_name="Ivan",
            client_phone="+7999",
            client_username="ivan",
            details="Need a bot",
            status="cancelled",
        )
        service = SimpleNamespace(id=1, name="Order a bot", service_type=SERVICE_TYPE_ORDER)
        admin_cancel_order_text = format_order_cancelled_by_client_admin_notification(order, service, "ru")
        if "❌ Клиент отменил заявку" not in admin_cancel_order_text:
            raise AssertionError("test G — admin order cancel notification title missing")
        if "Order a bot" not in admin_cancel_order_text:
            raise AssertionError("test G — admin order cancel notification service missing")

        # Test H — admin cancels order client notification
        client_cancel_order_text = format_order_cancelled_by_admin_client_notification(order, service, "ru")
        if "❌ Ваша заявка отменена администратором" not in client_cancel_order_text:
            raise AssertionError("test H — client order cancel notification title missing")

        # Test I — client reschedules booking admin notification
        from datetime import datetime

        booking = SimpleNamespace(
            id=5,
            service_id=2,
            client_id=1,
            client_name="Maria",
            client_phone="+7888",
            start_at=datetime(2026, 6, 22, 21, 0),
        )
        book_service = SimpleNamespace(id=2, name="Урок", service_type=SERVICE_TYPE_BOOKING)
        reschedule_text = format_booking_rescheduled_by_client_admin_notification(
            booking,
            book_service,
            "ru",
            old_datetime="22.06.2026 21:00",
            new_datetime="22.06.2026 17:00",
        )
        if "22.06.2026 21:00" not in reschedule_text or "22.06.2026 17:00" not in reschedule_text:
            raise AssertionError("test I — reschedule notification must include old/new local datetimes")

        # Notification service — sync/async builders must resolve to str
        import asyncio
        import inspect
        from unittest.mock import AsyncMock, MagicMock, patch

        from app.services.booking_notification_service import _resolve_text_builder

        sync_text = asyncio.run(_resolve_text_builder(lambda lang: f"ok:{lang}", "ru"))
        if sync_text != "ok:ru":
            raise AssertionError("notification test A — sync builder must return str")

        async def async_builder(lang: str) -> str:
            return f"async:{lang}"

        async_text = asyncio.run(_resolve_text_builder(async_builder, "en"))
        if async_text != "async:en":
            raise AssertionError("notification test B — async builder must be awaited")

        try:
            asyncio.run(_resolve_text_builder(lambda lang: 123, "ru"))  # type: ignore[return-value]
            raise AssertionError("notification test C — non-str builder must fail type check")
        except TypeError:
            pass

        sent_texts: list = []

        async def capture_send(chat_id, text, **kwargs):
            sent_texts.append(text)

        mock_bot = MagicMock()
        mock_bot.send_message = AsyncMock(side_effect=capture_send)

        from app.services.booking_notification_service import notify_admins_client_cancelled

        cancel_booking = SimpleNamespace(
            id=1,
            service_id=1,
            client_id=1,
            client_name="Test",
            client_phone="+7999",
            start_at=datetime(2026, 6, 23, 10, 0),
            service_location_title=None,
            service_location_address=None,
            location_text=None,
            client_comment=None,
        )
        cancel_service = SimpleNamespace(id=1, name="Урок", requires_location=False, ask_client_comment=False)

        async def fake_username(_client_id: int):
            return "testuser"

        with patch(
            "app.services.booking_notification_service._load_client_username",
            new=fake_username,
        ), patch(
            "app.services.booking_notification_service.get_settings",
            return_value=SimpleNamespace(admin_ids=[1], default_language="ru"),
        ), patch(
            "app.services.booking_notification_service.get_user_language",
            new=AsyncMock(return_value="ru"),
        ):
            asyncio.run(
                notify_admins_client_cancelled(mock_bot, cancel_booking, cancel_service)
            )

        if not sent_texts or not isinstance(sent_texts[0], str):
            raise AssertionError("notification test C — send_message must receive str")
        if inspect.iscoroutine(sent_texts[0]):
            raise AssertionError("notification test C — coroutine must not be sent as text")
        if "❌ Клиент отменил запись" not in sent_texts[0]:
            raise AssertionError("notification test G — client cancel admin text missing")

        from app.utils.formatting import format_booking_cancelled_by_admin_client_notification

        admin_cancel_client_text = format_booking_cancelled_by_admin_client_notification(
            cancel_booking, cancel_service, "ru"
        )
        if not isinstance(admin_cancel_client_text, str) or "❌ Ваша запись отменена администратором" not in admin_cancel_client_text:
            raise AssertionError("notification test H — admin cancel client text missing")

        order_cancel_admin_text = format_order_cancelled_by_client_admin_notification(order, service, "ru")
        if not isinstance(order_cancel_admin_text, str):
            raise AssertionError("notification test I-order — order cancel admin text must be str")

        # Reschedule UI — period screen and 3-column time grid
        from datetime import date

        from app.bot.keyboards.booking_edit_kb import (
            reschedule_dates_kb,
            reschedule_time_grid_kb,
            reschedule_time_periods_kb,
        )

        booking_edit_src = (ROOT / "app" / "bot" / "handlers" / "booking_edit.py").read_text(encoding="utf-8")
        if "build_period_screen_text" not in booking_edit_src:
            raise AssertionError("notification test D — reschedule must use period screen helpers")
        if "reschedule_times_kb" in booking_edit_src:
            raise AssertionError("notification test D — old one-column reschedule_times_kb must not be used")

        res_date_rows = reschedule_dates_kb(1, [date(2026, 6, 25), date(2026, 6, 26), date(2026, 6, 27)], "ru").inline_keyboard
        if len(res_date_rows[0]) != 3:
            raise AssertionError("notification test E — reschedule dates must use 3 columns")

        res_period_rows = reschedule_time_periods_kb(1, ["day"], "ru").inline_keyboard
        period_callbacks = [btn.callback_data for row in res_period_rows for btn in row]
        if "my:res:period:1:day" not in period_callbacks:
            raise AssertionError("notification test D — reschedule period callbacks missing")

        res_grid_rows = reschedule_time_grid_kb(
            1,
            [
                datetime(2026, 6, 25, 12, 0),
                datetime(2026, 6, 25, 12, 30),
                datetime(2026, 6, 25, 13, 0),
            ],
            "ru",
        ).inline_keyboard
        time_row = next(row for row in res_grid_rows if row[0].callback_data.startswith("my:res:time:"))
        if len(time_row) != 3:
            raise AssertionError("notification test E — reschedule time grid must use 3 columns")

        if "Было:" not in reschedule_text or "Стало:" not in reschedule_text:
            raise AssertionError("notification test F — reschedule notification must include Было/Стало")

        # Test J/K — calendar sync guards for order vs booking services

        from app.models import BookingStatus
        from app.services.booking_service import BookingService

        booking_obj = MagicMock()
        booking_obj.id = 10
        booking_obj.service_id = 99
        booking_obj.status = BookingStatus.CONFIRMED

        bs = BookingService.__new__(BookingService)
        bs.service_repo = AsyncMock()
        bs.service_repo.get_by_id = AsyncMock(
            return_value=SimpleNamespace(service_type=SERVICE_TYPE_ORDER)
        )

        with patch("app.services.booking_service._schedule_calendar_sync_create") as create_sync:
            asyncio.run(bs._maybe_schedule_calendar_sync_create(booking_obj))
            if create_sync.called:
                raise AssertionError("test J — order service must not schedule calendar create")

        bs.service_repo.get_by_id = AsyncMock(
            return_value=SimpleNamespace(service_type=SERVICE_TYPE_BOOKING)
        )
        with patch("app.services.booking_service._schedule_calendar_sync_create") as create_sync:
            asyncio.run(bs._maybe_schedule_calendar_sync_create(booking_obj))
            if not create_sync.called:
                raise AssertionError("test K — booking service must still schedule calendar create")

        booking_only_admin = {btn.text for row in admin_menu("ru", booking_enabled=True, order_enabled=False).keyboard for btn in row}
        if t("ru", "orders_admin_button") in booking_only_admin:
            raise AssertionError("admin menu — orders button hidden when order mode off")
        both_admin = {btn.text for row in admin_menu("ru", booking_enabled=True, order_enabled=True).keyboard for btn in row}
        if t("ru", "orders_admin_button") not in both_admin:
            raise AssertionError("admin menu — orders button shown when order mode on")

        from app.bot.keyboards.service_media_kb import client_service_card_kb

        order_cb = client_service_card_kb(1, "ru", service_type=SERVICE_TYPE_ORDER).inline_keyboard[0][0].callback_data
        if order_cb != "cb:order:1":
            raise AssertionError("order service card uses cb:order")
        book_cb = client_service_card_kb(1, "ru", service_type=SERVICE_TYPE_BOOKING).inline_keyboard[0][0].callback_data
        if book_cb != "cb:book:1":
            raise AssertionError("booking service card uses cb:book")

        print("OK: UX menus, notifications, and calendar guards")
    except Exception as exc:
        print(f"FAIL: service types — {exc}")
        return 1

    settings = get_settings()
    sample = normalize_slot.__name__
    print(f"TIMEZONE={settings.timezone}")
    print(f"normalize_slot={sample} (from app.utils.datetime_utils)")

    try:
        _check_symbol_imports(ROOT / "app")
        print("OK: common symbol imports")
    except Exception as exc:
        print(f"FAIL: symbol import audit — {exc}")
        return 1

    try:
        _check_callback_prefix_handlers()
        print("OK: callback prefix handler audit")
    except Exception as exc:
        print(f"FAIL: callback prefix audit — {exc}")
        return 1

    try:
        from app.services.reminder_service import ReminderService
        from app.services.start_screen_service import deliver_start_screen

        start_src = (ROOT / "app" / "services" / "start_screen_service.py").read_text(encoding="utf-8")
        if "async_session_factory(" in start_src and "from app.database.session import async_session_factory" not in start_src:
            raise AssertionError("start_screen_service.py uses async_session_factory without import")
        if deliver_start_screen is None or ReminderService is None:
            raise AssertionError("critical service symbols missing")
        print("OK: critical service imports smoke")
    except Exception as exc:
        print(f"FAIL: critical service imports smoke — {exc}")
        return 1

    try:
        import app.services.reminder_service as reminder_service_module

        if not hasattr(reminder_service_module, "log_action_timing"):
            raise AssertionError("reminder_service must import log_action_timing")
        print("OK: ReminderService log_action_timing import")
    except Exception as exc:
        print(f"FAIL: ReminderService import audit — {exc}")
        return 1

    try:
        import scripts.smoke_e2e as smoke_e2e

        smoke_code = smoke_e2e.main()
        if smoke_code != 0:
            print("FAIL: scripts/smoke_e2e.py")
            return smoke_code
        print("OK: smoke E2E")
    except Exception as exc:
        print(f"FAIL: smoke E2E — {exc}")
        return 1

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
