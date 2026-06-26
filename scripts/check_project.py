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
            "list_upcoming_unavailable(",
            "list_upcoming_unavailable",
            "app.services.unavailable_service",
            {"unavailable_service.py"},
        ),
        (
            "resolve_client_lang_for_client(",
            "resolve_client_lang_for_client",
            "app.services.language_service",
            {"language_service.py"},
        ),
        (
            "resolve_client_lang(",
            "resolve_client_lang",
            "app.services.language_service",
            {"language_service.py"},
        ),
        (
            "get_settings(",
            "get_settings",
            "app.config",
            {"config.py"},
        ),
        (
            "SERVICE_TYPE_ORDER",
            "SERVICE_TYPE_ORDER",
            "app.models",
            set(),
        ),
        (
            "SERVICE_TYPE_BOOKING",
            "SERVICE_TYPE_BOOKING",
            "app.models",
            set(),
        ),
    ]
    for path in app_dir.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for call, symbol, module_path, skip_def_files in rules:
            if call not in text:
                continue
            if path.name in skip_def_files:
                continue
            if f"{symbol} =" in text:
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

        from app.bot.handlers.admin_clients import (
            _parse_list_callback,
            _parse_section_callback,
            _parse_view_callback,
        )
        from app.bot.keyboards.admin_clients_kb import (
            _list_cb,
            _section_cb,
            _view_cb,
            admin_clients_list_kb,
        )

        # Test A — legacy adm_cli:all and list callbacks do not raise
        legacy_all = _parse_list_callback("adm_cli:all")
        if legacy_all is None or legacy_all != ("all", 0):
            print("FAIL: test A — adm_cli:all must parse as filter=all page=0")
            return 1
        if _parse_section_callback("adm_cli:all") is not None:
            print("FAIL: test A — adm_cli:all is not a section callback")
            return 1

        # Test B — filter token "all" must not be parsed as client_id
        section_parsed = _parse_section_callback("adm_cli:hist:123:all:0:0")
        if section_parsed is None:
            print("FAIL: test B — hist section with filter all must parse")
            return 1
        _section, client_id_b, filter_b, _page_b, _sp_b = section_parsed
        if client_id_b != 123 or filter_b != "all":
            print("FAIL: test B — section parser must keep all as filter_key, not client_id")
            return 1

        # Test C — view callback returns client_id
        client_id_c, filter_c, page_c = _parse_view_callback("adm_cli:view:123:all:0")
        if client_id_c != 123 or filter_c != "all" or page_c != 0:
            print("FAIL: test C — adm_cli:view:123 must return client_id=123")
            return 1

        # Test D — malformed view with non-numeric id does not crash
        bad_view = _parse_view_callback("adm_cli:view:all:all:0")
        if bad_view[0] is not None:
            print("FAIL: test D — adm_cli:view:all must return client_id=None")
            return 1
        bad_section = _parse_section_callback("adm_cli:hist:all:all:0:0")
        if bad_section is None or bad_section[1] is not None:
            print("FAIL: test D — adm_cli:hist:all must return client_id=None without crash")
            return 1

        # Test E — hub buttons parse successfully
        hub_callbacks = {btn.callback_data for row in main_kb.inline_keyboard for btn in row}
        for cb in hub_callbacks:
            if cb.startswith("adm_cli:list:") or cb == "adm_cli:all":
                if _parse_list_callback(cb) is None:
                    print(f"FAIL: test E — hub list callback must parse: {cb!r}")
                    return 1
            elif cb in ("adm_cli:search", "adm_cli:admin_back", "adm_cli:menu"):
                continue
            else:
                print(f"FAIL: test E — unexpected hub callback: {cb!r}")
                return 1

        # Test F — list row and section callbacks parse successfully
        list_cb = _list_cb("all", 0)
        if _parse_list_callback(list_cb) != ("all", 0):
            print("FAIL: test F — list page callback must parse")
            return 1
        view_cb = _view_cb(42, "all", 0)
        if _parse_view_callback(view_cb)[0] != 42:
            print("FAIL: test F — client row view callback must parse")
            return 1
        future_cb = _section_cb("future", 42, "all", 0, 0)
        future_parsed = _parse_section_callback(future_cb)
        if future_parsed is None or future_parsed[1] != 42:
            print("FAIL: test F — future section callback must parse client_id")
            return 1
        hist_cb = _section_cb("hist", 42, "upcoming", 1, 2)
        hist_parsed = _parse_section_callback(hist_cb)
        if hist_parsed is None or hist_parsed != ("hist", 42, "upcoming", 1, 2):
            print("FAIL: test F — hist section callback must parse all tokens")
            return 1
        empty_list_kb = admin_clients_list_kb([], "all", 0, 1, lang="en")
        for row in empty_list_kb.inline_keyboard:
            for btn in row:
                cb = btn.callback_data or ""
                if cb.startswith("adm_cli:list:"):
                    if _parse_list_callback(cb) is None:
                        print(f"FAIL: test F — list nav callback must parse: {cb!r}")
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
        if "show_admin_panel" not in sch_back_src:
            print("FAIL: test E — schedule back should return mode-aware admin panel")
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
        from unittest.mock import AsyncMock, patch

        from app.bot.keyboards.admin_bookings_kb import (
            admin_bookings_folder_kb,
            admin_bookings_hub_kb,
        )
        from app.bot.i18n import t
        from app.bot.utils.booking_labels import format_admin_booking_button, truncate_display_name
        from app.models import BookingStatus
        from app.services.admin_bookings_service import (
            build_bookings_hub_body,
            compute_bookings_hub_counts,
            filter_bookings_for_section,
            normalize_bookings_section,
            parse_bookings_list_callback,
            search_bookings,
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
                label_ru = format_admin_booking_button(booking, "ru", service_name="Урок")
                label_en = format_admin_booking_button(booking, "en", service_name="Lesson")
                label_confirmed = format_admin_booking_button(
                    booking_tomorrow, "ru", service_name="Тренировка"
                )
                label_waiting = format_admin_booking_button(
                    booking_confirmed_no_response,
                    "ru",
                    service_name="Урок",
                )
                label_needs_change = format_admin_booking_button(
                    booking_needs_change,
                    "ru",
                    service_name="Урок",
                )
                counts = compute_bookings_hub_counts(all_bookings, fixed_now)
                pending_admin = filter_bookings_for_section(all_bookings, "pending_admin", fixed_now)
                active = filter_bookings_for_section(all_bookings, "active", fixed_now)
                upcoming = filter_bookings_for_section(all_bookings, "upcoming", fixed_now)
                confirmed_bookings = filter_bookings_for_section(
                    all_bookings, "confirmed_bookings", fixed_now
                )
                waiting_client = filter_bookings_for_section(
                    all_bookings, "waiting_client_response", fixed_now
                )
                needs_change = filter_bookings_for_section(all_bookings, "needs_change", fixed_now)
                hub_kb = admin_bookings_hub_kb("ru")
                hub_body = build_bookings_hub_body(counts, "ru")
                folder_kb = admin_bookings_folder_kb(
                    pending_admin,
                    "pending_admin",
                    0,
                    1,
                    "ru",
                    service_names={1: "Урок"},
                )
                active_kb = admin_bookings_folder_kb(
                    active,
                    "active",
                    0,
                    1,
                    "ru",
                    service_names={1: "Урок"},
                )

        hub_callbacks = [btn.callback_data for row in hub_kb.inline_keyboard for btn in row]
        hub_buttons = [btn.text for row in hub_kb.inline_keyboard for btn in row]
        if any(cb.startswith("adm_book:view:") or cb.startswith("adm_booking:") for cb in hub_callbacks):
            print("FAIL: test A — hub must not list individual bookings")
            return 1
        for required_cb in (
            "adm_book:list:active:0",
            "adm_book:list:pending_admin:0",
            "adm_book:list:history:0",
            "adm_book:list:cancelled:0",
            "adm_book:search",
            "adm_book:admin_back",
        ):
            if required_cb not in hub_callbacks:
                print(f"FAIL: test E — hub missing callback {required_cb}")
                return 1
        for forbidden_cb in (
            "adm_book:list:upcoming:0",
            "adm_book:list:confirmed_bookings:0",
            "adm_book:list:waiting_client_response:0",
            "adm_book:list:needs_change:0",
        ):
            if forbidden_cb in hub_callbacks:
                print(f"FAIL: test F — hub must not expose old folder {forbidden_cb}")
                return 1
        if len(hub_callbacks) != 6:
            print("FAIL: test E — hub should have 5 actions plus back")
            return 1
        for label in (
            t("ru", "bookings_all_active_button"),
            t("ru", "bookings_pending_admin_button"),
            t("ru", "bookings_folder_history"),
            t("ru", "bookings_folder_cancelled"),
            t("ru", "bookings_search_button"),
            t("ru", "back_to_admin_panel"),
        ):
            if label not in hub_buttons:
                print(f"FAIL: test E — hub missing button {label}")
                return 1
        for forbidden_label in (
            t("ru", "bookings_folder_upcoming"),
            t("ru", "bookings_folder_confirmed_bookings"),
            t("ru", "bookings_folder_waiting_client_response"),
            t("ru", "bookings_folder_needs_change"),
            "Требуют внимания",
            "Need attention",
        ):
            if forbidden_label in hub_buttons:
                print(f"FAIL: test F — hub must not show {forbidden_label}")
                return 1
        if t("ru", "bookings_active_summary", count=str(counts.active_count)) not in hub_body:
            print("FAIL: test E — hub body missing active summary")
            return 1
        if t("ru", "bookings_choose_action") not in hub_body:
            print("FAIL: test E — hub body missing choose action")
            return 1

        for legacy in (
            "upcoming",
            "confirmed_bookings",
            "waiting_client_response",
            "needs_change",
        ):
            mapped_section, _ = parse_bookings_list_callback(f"adm_book:list:{legacy}:0")
            if mapped_section != "active":
                print(f"FAIL: test G — legacy section {legacy} must map to active")
                return 1
        from app.services.admin_bookings_service import resolve_bookings_list_section

        if resolve_bookings_list_section("pending_admin") != "pending_admin":
            print("FAIL: test G — pending_admin section must stay pending_admin")
            return 1

        if label_ru != "🕓 Сегодня 21:30 · Abdallah Bahi · Урок":
            print(f"FAIL: admin booking button RU label mismatch: {label_ru!r}")
            return 1
        if label_en != "🕓 Today 21:30 · Abdallah Bahi · Lesson":
            print(f"FAIL: admin booking button EN label mismatch: {label_en!r}")
            return 1
        if "#26" in label_ru:
            print("FAIL: booking id visible in list button")
            return 1
        if label_confirmed != "✅ Завтра 13:00 · Maria · Тренировка":
            print(f"FAIL: confirmed tomorrow label mismatch: {label_confirmed!r}")
            return 1
        if label_waiting != "❔ Сегодня 20:00 · Maria · Урок":
            print(f"FAIL: waiting client response label mismatch: {label_waiting!r}")
            return 1
        if label_needs_change != "⚠️ 19.06 12:00 · Maria · Урок":
            print(f"FAIL: needs change label mismatch: {label_needs_change!r}")
            return 1
        truncated = truncate_display_name(long_name)
        if len(truncated) > 28 or not truncated.endswith("…"):
            print("FAIL: name truncation length or suffix")
            return 1

        if counts.active_count != 4 or counts.upcoming_count != 4:
            print("FAIL: test C — active/upcoming count")
            return 1
        if len(active) != 4 or active != upcoming:
            print("FAIL: test C — active folder must match upcoming filter")
            return 1
        if counts.pending_admin_count != 1:
            print("FAIL: test A/B — pending admin count")
            return 1
        if len(pending_admin) != 1 or pending_admin[0].id != 26:
            print("FAIL: test A/B — pending admin folder filter")
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

        search_hits = search_bookings(all_bookings, "Abdallah", {1: "Урок"})
        if not search_hits or search_hits[0].id != 26:
            print("FAIL: booking search by client name")
            return 1
        search_id = search_bookings(all_bookings, "31", {1: "Урок"})
        if not search_id or search_id[0].id != 31:
            print("FAIL: booking search by id")
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
        pending_labels = [btn.text for row in folder_kb.inline_keyboard for btn in row if btn.callback_data.startswith("adm_book:view:")]
        if not pending_labels or not pending_labels[0].startswith("🕓"):
            print("FAIL: test I — pending admin row must use pending icon")
            return 1
        if " · Урок" not in pending_labels[0]:
            print("FAIL: test I — pending admin row must include service name")
            return 1
        active_labels = [btn.text for row in active_kb.inline_keyboard for btn in row if btn.callback_data.startswith("adm_book:view:")]
        if len(active_labels) < 4:
            print("FAIL: test I — active folder should list active bookings")
            return 1
        if not any(text.startswith("❔") for text in active_labels):
            print("FAIL: test I — active folder must show waiting-client icon rows")
            return 1
        if not any(text.startswith("⚠️") for text in active_labels):
            print("FAIL: test I — active folder must show needs-change icon rows")
            return 1

        from app.bot.keyboards.admin_bookings_kb import admin_booking_detail_kb
        from app.bot.keyboards.booking_edit_kb import client_booking_detail_kb
        from app.bot.keyboards.orders_kb import admin_order_detail_kb
        from app.models import ServiceOrderStatus
        from app.services.admin_bookings_service import (
            BookingDetailSource,
            booking_detail_back_callback,
            build_booking_view_callback,
            parse_booking_detail_source,
        )
        from app.services.calendar_service import CalendarService

        bookings_source = BookingDetailSource(section="pending_admin", page=0)
        bookings_view_cb = build_booking_view_callback(26, bookings_source)
        if booking_detail_back_callback(bookings_source) != "adm_book:list:pending_admin:0":
            print("FAIL: test A — bookings source back must return same section")
            return 1
        parsed_id, parsed_source = parse_booking_detail_source(bookings_view_cb)
        if parsed_id != 26 or parsed_source.section != "pending_admin":
            print("FAIL: test A — bookings view callback must preserve section")
            return 1

        client_source = BookingDetailSource(
            origin="client",
            client_id=5,
            client_tab="hist",
            client_filter="all",
            page=0,
            client_section_page=1,
        )
        client_view_cb = build_booking_view_callback(42, client_source)
        if booking_detail_back_callback(client_source) != "adm_cli:hist:5:all:0:1":
            print("FAIL: test B — client history back must return client history section")
            return 1
        if "adm_book:list:active" in booking_detail_back_callback(client_source):
            print("FAIL: test B — client history back must not route to active bookings")
            return 1
        _, client_parsed = parse_booking_detail_source(client_view_cb)
        if client_parsed.origin != "client" or client_parsed.client_tab != "hist":
            print("FAIL: test B — client history view callback parse")
            return 1

        future_source = BookingDetailSource(
            origin="client",
            client_id=5,
            client_tab="future",
            client_filter="all",
            page=0,
            client_section_page=0,
        )
        if booking_detail_back_callback(future_source) != "adm_cli:future:5:all:0:0":
            print("FAIL: test C — client future back must return future section")
            return 1

        with patch("app.services.admin_bookings_service.now_local", return_value=fixed_now):
            cancelled_kb = admin_booking_detail_kb(booking_cancelled, bookings_source, lang="ru")
            past_kb = admin_booking_detail_kb(booking_past, bookings_source, lang="ru")
            pending_kb = admin_booking_detail_kb(booking, bookings_source, lang="ru")
            confirmed_kb = admin_booking_detail_kb(
                booking_confirmed,
                bookings_source,
                lang="ru",
                show_send_confirmation=True,
            )
        cancelled_callbacks = [btn.callback_data for row in cancelled_kb.inline_keyboard for btn in row]
        for forbidden in ("adm_confirm:", "adm_cancel:", "adm_att:send:"):
            if any(cb and cb.startswith(forbidden) for cb in cancelled_callbacks):
                print(f"FAIL: test D — cancelled booking must not include {forbidden}")
                return 1

        past_callbacks = [btn.callback_data for row in past_kb.inline_keyboard for btn in row]
        if any(cb and cb.startswith("adm_confirm:") for cb in past_callbacks):
            print("FAIL: test E — past booking must not include confirm")
            return 1
        if any(cb and cb.startswith("adm_cancel:") for cb in past_callbacks):
            print("FAIL: test E — past booking must not include cancel")
            return 1

        pending_callbacks = [btn.callback_data for row in pending_kb.inline_keyboard for btn in row]
        if not any(cb and cb.startswith("adm_confirm:") for cb in pending_callbacks):
            print("FAIL: test F — pending future booking must include confirm")
            return 1
        if not any(cb and cb.startswith("adm_cancel:") for cb in pending_callbacks):
            print("FAIL: test F — pending future booking must include cancel")
            return 1

        confirmed_callbacks = [btn.callback_data for row in confirmed_kb.inline_keyboard for btn in row]
        if not any(cb and cb.startswith("adm_cancel:") for cb in confirmed_callbacks):
            print("FAIL: test G — confirmed future booking must include cancel")
            return 1
        if not any(cb and cb.startswith("adm_att:send:") for cb in confirmed_callbacks):
            print("FAIL: test G — confirmed future booking must include send question")
            return 1

        client_past_kb = client_booking_detail_kb(
            booking_past.id,
            lang="ru",
            can_reschedule=False,
            can_cancel=False,
            can_change_location=False,
            can_change_address=False,
            can_change_comment=False,
        )
        client_past_callbacks = [btn.callback_data for row in client_past_kb.inline_keyboard for btn in row]
        for forbidden in ("my:res:", "my:cancel:", "my:loc:", "my:addr:", "my:comment:"):
            if any(cb and cb.startswith(forbidden) for cb in client_past_callbacks):
                print(f"FAIL: test H — past/cancelled client booking must not include {forbidden}")
                return 1

        closed_order_kb = admin_order_detail_kb(
            1,
            ServiceOrderStatus.CANCELLED.value,
            "cancelled",
            0,
            "ru",
        )
        closed_callbacks = [btn.callback_data for row in closed_order_kb.inline_keyboard for btn in row]
        for forbidden in ("ord:accept:", "ord:decline:", "ord:status:in_progress:", "ord:status:completed:", "ord:status:cancelled:"):
            if any(cb and cb.startswith(forbidden) for cb in closed_callbacks):
                print(f"FAIL: test I — closed order must not include {forbidden}")
                return 1

        class _FakeRefreshError(Exception):
            pass

        import logging

        import app.services.calendar_service as calendar_service_module
        from app.services.calendar_service import (
            CalendarService,
            log_calendar_failure,
            mark_calendar_auth_failed,
        )

        calendar_service_module._calendar_auth_failed = False
        calendar_service_module._calendar_auth_warned = False
        calendar_service_module._calendar_auth_admin_notify_pending = False
        with patch.dict("sys.modules", {"google.auth.exceptions": SimpleNamespace(RefreshError=_FakeRefreshError)}):
            exc = _FakeRefreshError("invalid_grant: Token has been expired or revoked.")
            if not CalendarService._is_refresh_token_error(exc):
                print("FAIL: test J — RefreshError invalid_grant must be detected")
                return 1
            mark_calendar_auth_failed("event create")
            if not CalendarService.is_auth_failed():
                print("FAIL: test J — calendar auth failed flag must be set")
                return 1
            test_logger = logging.getLogger("check_project.calendar_test")
            with patch.object(test_logger, "exception") as mock_exception:
                log_calendar_failure(test_logger, "sync", exc, booking_id=45)
                if mock_exception.called:
                    print("FAIL: test J — RefreshError must not log traceback")
                    return 1
            service = CalendarService(AsyncMock())
            service._log_api_error("event create", exc)
            if not CalendarService.is_auth_failed():
                print("FAIL: test J — _log_api_error must mark auth failed on RefreshError")
                return 1

        from app.bot.keyboards.orders_kb import admin_orders_hub_kb

        orders_hub_callbacks = [
            btn.callback_data
            for row in admin_orders_hub_kb(
                {"new": 1, "in_progress": 0, "completed": 0, "cancelled": 0, "declined": 0},
                "ru",
            ).inline_keyboard
            for btn in row
        ]
        for required_order_cb in (
            "ord:folder:new:0",
            "ord:folder:in_progress:0",
            "ord:folder:completed:0",
            "ord:folder:cancelled:0",
            "ord:folder:declined:0",
        ):
            if required_order_cb not in orders_hub_callbacks:
                print(f"FAIL: test H — orders hub callback missing {required_order_cb}")
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
            service_type="booking",
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

        if t("ru", "admin_services") != "🛠 Услуги":
            raise AssertionError("test B — RU admin services button must be short")
        if t("en", "admin_services") != "🛠 Services":
            raise AssertionError("test B — EN admin services button must be short")
        if "Управление" in t("ru", "admin_services"):
            raise AssertionError("test B — admin services button must not use long manage label")
        if t("ru", "main_menu_services") != "📋 Выбрать услугу":
            raise AssertionError("test A — RU client services button must be choose-service label")
        if t("en", "main_menu_services") != "📋 Choose service":
            raise AssertionError("test A — EN client services button must be choose-service label")

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
        if not t("ru", "order_services_button").startswith("🛒"):
            raise AssertionError("test A — order service button must use cart icon")
        if not t("ru", "my_orders_button").startswith("🗂"):
            raise AssertionError("test A — my orders button must use folder icon")
        if t("ru", "order_services_button")[0] == t("ru", "my_orders_button")[0]:
            raise AssertionError("test A — order service and my orders icons must differ")

        order_only_admin = {
            btn.text for row in admin_menu("ru", booking_enabled=False, order_enabled=True).keyboard for btn in row
        }
        if t("ru", "orders_admin_button") not in order_only_admin:
            raise AssertionError("test C — order-only admin menu must show orders")
        if t("ru", "admin_bookings") in order_only_admin or t("ru", "schedule_button") in order_only_admin:
            raise AssertionError("test C — order-only admin menu must hide bookings/schedule")
        clients_back_menu = {
            btn.text
            for row in admin_menu("ru", booking_enabled=False, order_enabled=True).keyboard
            for btn in row
        }
        if t("ru", "admin_bookings") in clients_back_menu:
            raise AssertionError("test D — clients back admin menu must be mode-aware (no bookings in order-only)")

        import inspect

        clients_back_src = inspect.getsource(
            __import__(
                "app.bot.handlers.admin_clients",
                fromlist=["clients_back_admin"],
            ).clients_back_admin
        )
        if "show_admin_panel" not in clients_back_src:
            raise AssertionError("test D — clients back must use show_admin_panel helper")

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
        from types import SimpleNamespace

        from app.bot.i18n import t
        from app.bot.keyboards.orders_kb import (
            admin_new_order_kb,
            admin_order_detail_kb,
            client_order_detail_kb,
        )
        from app.bot.states import AdminOrderStates
        from app.models import OrderMessage, ServiceOrderStatus
        from app.utils.formatting import (
            format_order_accepted_client_notification,
            format_order_declined_client_notification,
        )

        if OrderMessage.__tablename__ != "order_messages":
            raise AssertionError("test D — order_messages model missing")
        if ServiceOrderStatus.ACCEPTED.value != "accepted":
            raise AssertionError("test B — accepted status missing")
        if ServiceOrderStatus.DECLINED.value != "declined":
            raise AssertionError("test C — declined status missing")
        if not hasattr(AdminOrderStates, "entering_decline_reason"):
            raise AssertionError("test C — decline reason FSM missing")

        new_kb_callbacks = [
            btn.callback_data for row in admin_new_order_kb(7, "ru").inline_keyboard for btn in row
        ]
        new_kb_texts = [btn.text for row in admin_new_order_kb(7, "ru").inline_keyboard for btn in row]
        if "ord:accept:7" not in new_kb_callbacks:
            raise AssertionError("test A — admin new order notification missing accept callback")
        if "ord:decline:7" not in new_kb_callbacks:
            raise AssertionError("test A — admin new order notification missing decline callback")
        if t("ru", "order_accept_button") not in new_kb_texts:
            raise AssertionError("test A — admin new order notification missing accept button")
        if t("ru", "order_decline_button") not in new_kb_texts:
            raise AssertionError("test A — admin new order notification missing decline button")

        new_detail = {
            btn.callback_data
            for row in admin_order_detail_kb(7, ServiceOrderStatus.NEW.value, "new", 0, "ru").inline_keyboard
            for btn in row
        }
        accepted_detail = {
            btn.callback_data
            for row in admin_order_detail_kb(
                7, ServiceOrderStatus.ACCEPTED.value, "in_progress", 0, "ru"
            ).inline_keyboard
            for btn in row
        }
        if "ord:accept:7" not in new_detail or "ord:decline:7" not in new_detail:
            raise AssertionError("test G — new order detail must offer accept/decline")
        if "ord:status:in_progress:7" not in accepted_detail:
            raise AssertionError("test G — accepted order detail must offer mark in progress")
        if "ord:status:in_progress:7" in new_detail:
            raise AssertionError("test G — new order detail must not skip approval")

        client_active = {
            btn.callback_data
            for row in client_order_detail_kb(
                7, ServiceOrderStatus.ACCEPTED.value, "ru", section="active"
            ).inline_keyboard
            for btn in row
        }
        client_declined = {
            btn.callback_data
            for row in client_order_detail_kb(
                7, ServiceOrderStatus.DECLINED.value, "ru", section="history"
            ).inline_keyboard
            for btn in row
        }
        if "myord:msg:7" not in client_active:
            raise AssertionError("test G — active client order must allow writing to order")
        if "myord:cancel:7:active" not in client_active:
            raise AssertionError("test G — active client order must allow cancel")
        if "myord:cancel:7:active" in client_declined or "myord:cancel:7:history" in client_declined:
            raise AssertionError("test G — declined client order must not allow cancel")
        if "myord:active" not in client_active:
            raise AssertionError("test E — detail back must return to active section")

        service = SimpleNamespace(name="Telegram bot", service_type="order")
        order = SimpleNamespace(
            id=7,
            service_id=1,
            decline_reason="Сейчас не смогу выполнить эту услугу.",
            status=ServiceOrderStatus.DECLINED.value,
        )
        accepted_text = format_order_accepted_client_notification(order, service, "ru")
        declined_text = format_order_declined_client_notification(order, service, "ru")
        if not isinstance(accepted_text, str) or t("ru", "order_accepted_client") not in accepted_text:
            raise AssertionError("test B — accepted client notification missing")
        if "Сейчас не смогу выполнить эту услугу." not in declined_text:
            raise AssertionError("test C — declined client notification must include reason")

        from app.services.order_service import ORDER_MESSAGE_SENDER_ADMIN, ORDER_MESSAGE_SENDER_CLIENT

        if ORDER_MESSAGE_SENDER_ADMIN != "admin" or ORDER_MESSAGE_SENDER_CLIENT != "client":
            raise AssertionError("test E/F — order message sender constants missing")

        print("OK: order approval workflow")
    except Exception as exc:
        print(f"FAIL: order approval workflow — {exc}")
        return 1

    try:
        from datetime import datetime
        from types import SimpleNamespace

        from app.bot.i18n import t
        from app.bot.keyboards.orders_kb import (
            client_orders_active_kb,
            client_orders_history_kb,
            client_orders_hub_kb,
        )
        from app.bot.utils.order_labels import format_client_order_button
        from app.models import ServiceOrderStatus
        from app.services.client_orders_service import (
            compute_client_orders_hub_counts,
            sort_active_client_orders,
            sort_history_client_orders,
            split_client_orders,
        )

        def _order(oid, status, created_at, details=None, service_id=1):
            return SimpleNamespace(
                id=oid,
                status=status,
                created_at=created_at,
                details=details,
                service_id=service_id,
            )

        now = datetime(2026, 6, 20, 12, 0, 0)
        orders = [
            _order(1, ServiceOrderStatus.NEW.value, now, "запись клиентов"),
            _order(2, ServiceOrderStatus.ACCEPTED.value, now.replace(day=21), "лендинг для курса"),
            _order(3, ServiceOrderStatus.IN_PROGRESS.value, now.replace(day=22)),
            _order(4, ServiceOrderStatus.COMPLETED.value, now.replace(day=19)),
            _order(5, ServiceOrderStatus.CANCELLED.value, now.replace(day=18)),
            _order(6, ServiceOrderStatus.DECLINED.value, now.replace(day=17)),
        ]
        active, history = split_client_orders(orders)
        counts = compute_client_orders_hub_counts(orders)
        if len(active) != 3 or len(history) != 3:
            raise AssertionError("test B/C — active/history split mismatch")
        if {o.status for o in active} != {
            ServiceOrderStatus.NEW.value,
            ServiceOrderStatus.ACCEPTED.value,
            ServiceOrderStatus.IN_PROGRESS.value,
        }:
            raise AssertionError("test B — active statuses mismatch")
        if {o.status for o in history} != {
            ServiceOrderStatus.COMPLETED.value,
            ServiceOrderStatus.CANCELLED.value,
            ServiceOrderStatus.DECLINED.value,
        }:
            raise AssertionError("test C — history statuses mismatch")

        hub_callbacks = [
            btn.callback_data for row in client_orders_hub_kb(counts, "ru").inline_keyboard for btn in row
        ]
        hub_texts = [btn.text for row in client_orders_hub_kb(counts, "ru").inline_keyboard for btn in row]
        if "myord:active" not in hub_callbacks or "myord:history" not in hub_callbacks:
            raise AssertionError("test A — my orders hub missing section buttons")
        if any(cb.startswith("myord:view:") for cb in hub_callbacks):
            raise AssertionError("test A — hub must not list individual orders")
        if t("ru", "my_orders_active_button", count="3") not in hub_texts:
            raise AssertionError("test A — hub missing active button")
        if t("ru", "my_orders_history_button", count="3") not in hub_texts:
            raise AssertionError("test A — hub missing history button")

        sorted_active = sort_active_client_orders(active)
        if [o.id for o in sorted_active] != [1, 2, 3]:
            raise AssertionError(f"test B — active sort order mismatch: {[o.id for o in sorted_active]}")
        sorted_history = sort_history_client_orders(history)
        if [o.id for o in sorted_history] != [4, 5, 6]:
            raise AssertionError("test C — history sort order mismatch")

        names = {1: "Order a bot", 2: "Сайт"}
        active_label = format_client_order_button(orders[0], "ru", service_name=names[1])
        if active_label != "🆕 20.06 · Order a bot · запись клиентов":
            raise AssertionError(f"test D — active row label mismatch: {active_label!r}")
        if "#1" in active_label:
            raise AssertionError("test D — row label must not show order id")

        active_kb = client_orders_active_kb(sorted_active, "ru", service_names=names)
        history_kb = client_orders_history_kb(sorted_history, "ru", service_names=names)
        active_view = [
            btn.callback_data for row in active_kb.inline_keyboard for btn in row if btn.callback_data.startswith("myord:view:")
        ]
        history_view = [
            btn.callback_data for row in history_kb.inline_keyboard for btn in row if btn.callback_data.startswith("myord:view:")
        ]
        if active_view != ["myord:view:1:active", "myord:view:2:active", "myord:view:3:active"]:
            raise AssertionError(f"test E — active view callbacks mismatch: {active_view}")
        if history_view[0] != "myord:view:4:history":
            raise AssertionError("test E — history view callbacks must include section")

        print("OK: client my orders hub and sections")
    except Exception as exc:
        print(f"FAIL: client my orders hub — {exc}")
        return 1

    try:
        from types import SimpleNamespace

        from app.bot.i18n import t
        from app.bot.keyboards import admin_service_detail_kb
        from app.models import SERVICE_TYPE_BOOKING, SERVICE_TYPE_ORDER
        from app.utils.formatting import format_service, format_service_admin

        def _service(svc_type: str) -> SimpleNamespace:
            return SimpleNamespace(
                name="Telegram bot" if svc_type == SERVICE_TYPE_ORDER else "Lesson",
                description="Build a bot",
                price=5000,
                duration_minutes=60,
                buffer_after_minutes=0,
                is_active=True,
                requires_location=False,
                ask_client_comment=False,
                show_media_to_clients=True,
                service_type=svc_type,
            )

        booking = _service(SERVICE_TYPE_BOOKING)
        order = _service(SERVICE_TYPE_ORDER)
        booking_admin = format_service_admin(booking, "ru", photos_count=0, videos_count=0, locations_count=0)
        order_admin = format_service_admin(order, "ru", photos_count=0, videos_count=0, locations_count=0)
        for label in ("Длительность", "Буфер", "Адрес клиента", "Комментарий клиента", "Места проведения"):
            if label not in booking_admin:
                raise AssertionError(f"test A — booking admin detail missing {label}")
            if label in order_admin:
                raise AssertionError(f"test B — order admin detail must not include {label}")
        for label in ("Duration", "Buffer", "Client address", "Client comment", "Locations"):
            order_en = format_service_admin(order, "en", photos_count=0, videos_count=0, locations_count=0)
            if label in order_en:
                raise AssertionError(f"test B — order EN admin detail must not include {label}")
        if "Заявка без даты и времени" not in order_admin:
            raise AssertionError("test B — order admin detail missing no-time type label")

        booking_kb = {
            btn.callback_data
            for row in admin_service_detail_kb(1, True, "ru", is_order_type=False).inline_keyboard
            for btn in row
        }
        order_kb = {
            btn.callback_data
            for row in admin_service_detail_kb(2, True, "ru", is_order_type=True).inline_keyboard
            for btn in row
        }
        if "adm_svc_edit:dur:1" not in booking_kb:
            raise AssertionError("test D — booking detail must include duration button")
        if "adm_svc_edit:buf:1" not in booking_kb:
            raise AssertionError("test D — booking detail must include buffer button")
        if "adm_svc_loc:1" not in booking_kb:
            raise AssertionError("test D — booking detail must include location button")
        for forbidden in ("adm_svc_edit:dur:2", "adm_svc_edit:buf:2", "adm_svc_loc:2", "adm_svc_comment:2"):
            if forbidden in order_kb:
                raise AssertionError(f"test C — order detail must not include {forbidden}")

        booking_client = format_service(booking, "ru")
        order_client = format_service(order, "ru")
        if "Длительность" not in booking_client:
            raise AssertionError("test F — booking client card must show duration")
        if "Длительность" in order_client:
            raise AssertionError("test E — order client card must not show duration")
        if "📝 Telegram bot" not in order_client:
            raise AssertionError("test E — order client card must use order icon")

        print("OK: order service hides booking-only fields")
    except Exception as exc:
        print(f"FAIL: order service field visibility — {exc}")
        return 1

    try:
        from types import SimpleNamespace

        from app.bot.i18n import t
        from app.bot.keyboards.service_price_kb import admin_service_price_kb
        from app.models import PRICE_MODE_EXACT, PRICE_MODE_FROM, SERVICE_TYPE_BOOKING, SERVICE_TYPE_ORDER
        from app.utils.formatting import (
            format_service,
            format_service_admin,
            format_service_price,
            normalize_price_mode,
        )

        def _priced_service(**kwargs) -> SimpleNamespace:
            base = dict(
                name="Telegram bot",
                description="Build a bot",
                price=5000,
                duration_minutes=60,
                buffer_after_minutes=0,
                is_active=True,
                requires_location=False,
                ask_client_comment=False,
                show_media_to_clients=True,
                service_type=SERVICE_TYPE_ORDER,
            )
            base.update(kwargs)
            return SimpleNamespace(**base)

        # Test A — missing price_mode defaults to exact
        legacy = _priced_service()
        if format_service_price(legacy, "ru") != "Цена: 5000 ₽":
            print(f"FAIL: test A — legacy exact price: {format_service_price(legacy, 'ru')!r}")
            return 1

        exact_svc = _priced_service(price_mode=PRICE_MODE_EXACT)
        if format_service_price(exact_svc, "ru") != "Цена: 5000 ₽":
            print("FAIL: test B — exact price RU")
            return 1

        from_svc = _priced_service(price_mode=PRICE_MODE_FROM)
        if format_service_price(from_svc, "ru") != "Цена: от 5000 ₽":
            print(f"FAIL: test C — from price RU: {format_service_price(from_svc, 'ru')!r}")
            return 1

        if format_service_price(exact_svc, "en") != "Price: 5000 ₽":
            print("FAIL: test D — exact price EN")
            return 1

        if format_service_price(from_svc, "en") != "Price: from 5000 ₽":
            print("FAIL: test E — from price EN")
            return 1

        bad_mode = _priced_service(price_mode="unknown")
        if normalize_price_mode(bad_mode) != PRICE_MODE_EXACT:
            print("FAIL: test F — unknown price_mode must fall back to exact")
            return 1
        if format_service_price(bad_mode, "ru") != "Цена: 5000 ₽":
            print("FAIL: test F — unknown price_mode formats as exact")
            return 1

        price_kb = {
            btn.callback_data
            for row in admin_service_price_kb(1, exact_svc, "ru").inline_keyboard
            for btn in row
        }
        for required in (
            "adm_svc:price:amt:1",
            "adm_svc:price:mode:exact:1",
            "adm_svc:price:mode:from:1",
            "adm_svc:price:back:1",
        ):
            if required not in price_kb:
                print(f"FAIL: test G — price keyboard missing {required}")
                return 1

        booking_svc = _priced_service(
            name="Lesson",
            service_type=SERVICE_TYPE_BOOKING,
            price_mode=PRICE_MODE_EXACT,
        )
        booking_text = format_service(booking_svc, "ru")
        if "Цена: 5000 ₽" not in booking_text or "Длительность" not in booking_text:
            print("FAIL: test H — booking service formatting")
            return 1

        order_from_admin = format_service_admin(from_svc, "ru", photos_count=0, videos_count=0, locations_count=0)
        if "Цена: от 5000 ₽" not in order_from_admin:
            print(f"FAIL: test I — order from price admin detail: {order_from_admin!r}")
            return 1
        order_from_client = format_service(from_svc, "ru")
        if "Цена: от 5000 ₽" not in order_from_client:
            print("FAIL: test I — order from price client card")
            return 1

        print("OK: service price display modes")
    except Exception as exc:
        print(f"FAIL: service price display modes — {exc}")
        return 1

    try:
        import inspect
        from unittest.mock import AsyncMock, MagicMock, patch

        from app.models import SERVICE_TYPE_BOOKING, SERVICE_TYPE_ORDER

        import app.bot.handlers.client as client_handlers

        if getattr(client_handlers, "SERVICE_TYPE_ORDER", None) != SERVICE_TYPE_ORDER:
            print("FAIL: test A — client.py must import SERVICE_TYPE_ORDER")
            return 1
        if getattr(client_handlers, "SERVICE_TYPE_BOOKING", None) != SERVICE_TYPE_BOOKING:
            print("FAIL: test A — client.py must import SERVICE_TYPE_BOOKING")
            return 1

        back_src = inspect.getsource(client_handlers._services_for_back)
        if "SERVICE_TYPE_ORDER" not in back_src or "SERVICE_TYPE_BOOKING" not in back_src:
            print("FAIL: test B — _services_for_back must use service type constants")
            return 1

        async def _run_back_tests() -> None:
            state = AsyncMock()
            session = MagicMock()
            repo = AsyncMock()
            repo.list_client_services = AsyncMock(return_value=[])

            with patch.object(client_handlers, "ServiceRepository", return_value=repo):
                state.get_data.return_value = {"flow_kind": "order"}
                services, show_icons = await client_handlers._services_for_back(state, session)
                repo.list_client_services.assert_awaited_with(service_type=SERVICE_TYPE_ORDER)
                if show_icons:
                    raise AssertionError("test C — order back must not show type icons")
                if services != []:
                    raise AssertionError("test C — order back services list")

                repo.list_client_services.reset_mock()
                state.get_data.return_value = {"flow_kind": "booking"}
                services, show_icons = await client_handlers._services_for_back(state, session)
                repo.list_client_services.assert_awaited_with(service_type=SERVICE_TYPE_BOOKING)
                if show_icons:
                    raise AssertionError("test D — booking back must not show type icons")

                repo.list_client_services.reset_mock()
                state.get_data.return_value = {"flow_kind": "unified"}
                services, show_icons = await client_handlers._services_for_back(state, session)
                repo.list_client_services.assert_awaited_with()
                if not show_icons:
                    raise AssertionError("test D — unified back must show type icons")

        import asyncio

        asyncio.run(_run_back_tests())

        handlers_src = inspect.getsource(client_handlers.back_to_services)
        if "_services_for_back" not in handlers_src or "cb:svc_back" not in inspect.getsource(client_handlers):
            print("FAIL: test C/D — back_to_services must use _services_for_back")
            return 1

        print("OK: client service type constants and back navigation")
    except Exception as exc:
        print(f"FAIL: client service type constants — {exc}")
        return 1

    try:
        import asyncio
        import inspect
        from datetime import timedelta
        from types import SimpleNamespace
        from unittest.mock import AsyncMock, MagicMock, patch

        from app.bot.handlers import orders as orders_handlers
        from app.bot.handlers.booking_edit import _detail_options
        from app.bot.handlers.client import show_my_bookings
        from app.bot.i18n import t
        from app.models import BookingStatus
        from app.services.confirmation_text_service import (
            ConfirmationTextConfig,
            should_send_attendance_buttons,
        )
        from app.services.language_service import resolve_client_lang
        from app.services.reminder_service import ReminderService
        from app.services.reminder_settings import ReminderConfig
        from app.utils.datetime_utils import now_local

        show_src = inspect.getsource(show_my_bookings)
        if "event.from_user.id" not in show_src:
            raise AssertionError("test A — show_my_bookings must use event.from_user.id")
        orders_src = inspect.getsource(orders_handlers.my_activity_bookings)
        if "show_my_bookings(callback" not in orders_src:
            raise AssertionError("test B — my_activity_bookings must call show_my_bookings(callback, ...)")

        repo_src = (ROOT / "app" / "repositories" / "__init__.py").read_text(encoding="utf-8")
        list_start = repo_src.find("async def list_for_client(self, client_id: int) -> list[Booking]:")
        list_block = repo_src[list_start : list_start + 400]
        if "attendance_status" in list_block:
            raise AssertionError("test C — list_for_client must not filter by attendance_status")

        service = SimpleNamespace(requires_location=True, ask_client_comment=True)
        future_booking = SimpleNamespace(
            status=BookingStatus.CONFIRMED,
            start_at=now_local() + timedelta(hours=3),
        )
        past_booking = SimpleNamespace(
            status=BookingStatus.CONFIRMED,
            start_at=now_local() - timedelta(hours=1),
        )
        cancelled_booking = SimpleNamespace(
            status=BookingStatus.CANCELLED,
            start_at=now_local() + timedelta(hours=3),
        )
        close_future = SimpleNamespace(
            status=BookingStatus.CONFIRMED,
            start_at=now_local() + timedelta(minutes=51),
        )
        future_opts = _detail_options(future_booking, service, 2)
        if not future_opts["can_cancel"] or not future_opts["can_reschedule"]:
            raise AssertionError("test D — future active booking must show action buttons")
        close_opts = _detail_options(close_future, service, 2)
        if not close_opts["can_cancel"] or not close_opts["can_reschedule"]:
            raise AssertionError("test D — near-future booking must still show action buttons")
        past_opts = _detail_options(past_booking, service, 2)
        if past_opts["can_cancel"] or past_opts["can_reschedule"]:
            raise AssertionError("test E — past booking must hide action buttons")
        cancelled_opts = _detail_options(cancelled_booking, service, 2)
        if cancelled_opts["can_cancel"] or cancelled_opts["can_reschedule"]:
            raise AssertionError("test F — cancelled booking must hide action buttons")

        client_ru = SimpleNamespace(language=None)
        client_en = SimpleNamespace(language="en")
        if resolve_client_lang(client_ru, enabled_languages=["ru"], default_language="ru") != "ru":
            raise AssertionError("test K — default language must be used when client language unset")
        if resolve_client_lang(client_en, enabled_languages=["ru"], default_language="ru") != "ru":
            raise AssertionError("test K — must not use unsupported client language when default is ru")
        ru_text = t("ru", "attendance_reminder_title")
        if "Подтверждение" not in ru_text:
            raise AssertionError("test L — Russian reminder title missing")

        enabled_cfg = ReminderConfig(
            enabled=True,
            test_mode=False,
            client_reminder_1_minutes=1440,
            client_reminder_2_minutes=60,
            admin_reminder_minutes=60,
            test_client_reminder_minutes=5,
            test_admin_reminder_minutes=3,
            attendance_confirmation_enabled=True,
            attendance_confirmation_reminder="client_1",
        )
        disabled_cfg = ReminderConfig(
            enabled=True,
            test_mode=False,
            client_reminder_1_minutes=1440,
            client_reminder_2_minutes=60,
            admin_reminder_minutes=60,
            test_client_reminder_minutes=5,
            test_admin_reminder_minutes=3,
            attendance_confirmation_enabled=False,
            attendance_confirmation_reminder="client_1",
        )
        if not should_send_attendance_buttons(enabled_cfg, "client_2"):
            raise AssertionError("test I — attendance enabled reminders must include buttons")
        if should_send_attendance_buttons(disabled_cfg, "client_1"):
            raise AssertionError("test J — attendance disabled reminders must not include buttons")

        async def _run_reminder_tests() -> None:
            bot = AsyncMock()
            bot.send_message = AsyncMock()
            service_obj = ReminderService(bot)
            booking = SimpleNamespace(
                id=99,
                client_id=1,
                service_id=1,
                start_at=now_local() + timedelta(minutes=59),
                client_name="Test",
                client_phone=None,
                location_text=None,
                service_location_title=None,
                service_location_address=None,
                client_comment=None,
                attendance_status=None,
                client_reminder_1_sent_at=None,
                client_reminder_2_sent_at=None,
                admin_reminder_sent_at=None,
            )
            client = SimpleNamespace(id=1, telegram_id=12345, language=None)
            text_config = ConfirmationTextConfig(values={})
            with patch.object(
                service_obj,
                "resolve_client_lang_for_client",
                new=AsyncMock(return_value="ru"),
                create=True,
            ):
                with patch(
                    "app.services.reminder_service.resolve_client_lang_for_client",
                    new=AsyncMock(return_value="ru"),
                ):
                    client_ok = await service_obj._send_client_reminder(
                        booking,
                        client,
                        "ru",
                        "Урок",
                        "01.01.2026 18:00",
                        now_local(),
                        enabled_cfg,
                        text_config,
                        "client_2",
                    )
            if not client_ok:
                raise AssertionError("test G — client reminder send failed")
            if bot.send_message.await_count != 1:
                raise AssertionError("test G — client reminder must call send_message once")
            sent_kwargs = bot.send_message.await_args.kwargs
            if sent_kwargs.get("reply_markup") is None:
                raise AssertionError("test I — attendance enabled client reminder must include keyboard")

            bot.send_message.reset_mock()
            simple_ok = await service_obj._send_client_reminder(
                booking,
                client,
                "ru",
                "Урок",
                "01.01.2026 18:00",
                now_local(),
                disabled_cfg,
                text_config,
                "client_2",
            )
            if not simple_ok:
                raise AssertionError("test J — simple client reminder send failed")
            if bot.send_message.await_args.kwargs.get("reply_markup") is not None:
                raise AssertionError("test J — attendance disabled client reminder must not include keyboard")

            bot.send_message.reset_mock()
            with patch(
                "app.services.reminder_service.get_user_language",
                new=AsyncMock(return_value="ru"),
            ):
                admin_ok = await service_obj._send_admin_reminder_messages(
                    booking,
                    "Урок",
                    "01.01.2026 18:00",
                    mark_sent=False,
                )
            if not admin_ok:
                raise AssertionError("test M — admin reminder send failed")
            if bot.send_message.await_count < 1:
                raise AssertionError("test H/M — admin reminder must send independently")

        asyncio.run(_run_reminder_tests())
        print("OK: client bookings visibility, reminders, and language (tests A–M)")
    except Exception as exc:
        print(f"FAIL: client bookings/reminders — {exc}")
        return 1

    try:
        import asyncio
        import inspect
        from datetime import timedelta
        from types import SimpleNamespace
        from unittest.mock import AsyncMock, MagicMock, patch

        from app.bot.handlers.schedule import build_schedule_main_text
        from app.bot.keyboards import bookings_kb, my_bookings_back_kb
        from app.bot.keyboards.admin_bookings_kb import admin_booking_detail_kb, admin_bookings_folder_kb
        from app.models import BookingStatus
        from app.services.admin_bookings_service import BookingDetailSource, is_manual_attendance_send_eligible
        from app.services.language_service import resolve_client_lang_for_client
        from app.utils.datetime_utils import now_local

        schedule_src = (ROOT / "app" / "bot" / "handlers" / "schedule.py").read_text(encoding="utf-8")
        if "list_upcoming_unavailable" not in schedule_src:
            raise AssertionError("test A — schedule.py must use list_upcoming_unavailable")
        if "from app.services.unavailable_service import list_upcoming_unavailable" not in schedule_src:
            raise AssertionError("test A — schedule.py must import list_upcoming_unavailable")

        async def _build_schedule_text() -> str:
            with patch(
                "app.bot.handlers.schedule.get_weekly_schedule",
                new=AsyncMock(return_value={}),
            ), patch(
                "app.bot.handlers.schedule.breaks_by_weekday",
                new=AsyncMock(return_value={}),
            ), patch(
                "app.bot.handlers.schedule.list_upcoming_unavailable",
                new=AsyncMock(return_value=[]),
            ):
                return await build_schedule_main_text("ru")

        text = asyncio.run(_build_schedule_text())
        if not isinstance(text, str) or "Расписание" not in text and "Schedule" not in text:
            raise AssertionError("test B — build_schedule_main_text must return schedule text")

        fixed_now = now_local()
        booking_confirmed = SimpleNamespace(
            id=10,
            status=BookingStatus.CONFIRMED,
            start_at=fixed_now + timedelta(hours=2),
            service_id=1,
            client_id=1,
        )
        booking_pending = SimpleNamespace(
            id=11,
            status=BookingStatus.PENDING,
            start_at=fixed_now + timedelta(hours=2),
            service_id=1,
            client_id=1,
        )
        booking_cancelled = SimpleNamespace(
            id=12,
            status=BookingStatus.CANCELLED,
            start_at=fixed_now + timedelta(hours=2),
            service_id=1,
            client_id=1,
        )
        booking_past = SimpleNamespace(
            id=13,
            status=BookingStatus.CONFIRMED,
            start_at=fixed_now - timedelta(hours=1),
            service_id=1,
            client_id=1,
        )
        source = BookingDetailSource(section="active", page=0)
        confirmed_kb = admin_booking_detail_kb(booking_confirmed, source, lang="ru")
        pending_kb = admin_booking_detail_kb(booking_pending, source, lang="ru")
        cancelled_kb = admin_booking_detail_kb(booking_cancelled, source, lang="ru")
        past_kb = admin_booking_detail_kb(booking_past, source, lang="ru")
        confirmed_callbacks = [btn.callback_data for row in confirmed_kb.inline_keyboard for btn in row]
        pending_callbacks = [btn.callback_data for row in pending_kb.inline_keyboard for btn in row]
        cancelled_callbacks = [btn.callback_data for row in cancelled_kb.inline_keyboard for btn in row]
        past_callbacks = [btn.callback_data for row in past_kb.inline_keyboard for btn in row]
        if not any(cb and cb.startswith("adm_att:send:") for cb in confirmed_callbacks):
            raise AssertionError("test C — confirmed future booking must include manual attendance button")
        if any(cb and cb.startswith("adm_att:send:") for cb in pending_callbacks):
            raise AssertionError("test D — pending booking must not include manual attendance button")
        if any(cb and cb.startswith("adm_att:send:") for cb in cancelled_callbacks + past_callbacks):
            raise AssertionError("test E — cancelled/past booking must not include manual attendance button")

        attendance_src = inspect.getsource(
            __import__("app.services.admin_attendance_service", fromlist=["send_attendance_question_to_client"])
        )
        if "resolve_client_lang_for_client" not in attendance_src:
            raise AssertionError("test F — manual attendance send must use resolve_client_lang_for_client")

        mark_src = inspect.getsource(
            __import__("app.services.admin_attendance_service", fromlist=["mark_manual_attendance_sent"])
        )
        for forbidden in ("client_reminder_1_sent_at", "client_reminder_2_sent_at", "admin_reminder_sent_at"):
            if forbidden in mark_src:
                raise AssertionError(f"test G — manual attendance must not set {forbidden}")

        bookings_keyboard = bookings_kb([], "ru")
        back_callbacks = [btn.callback_data for row in bookings_keyboard.inline_keyboard for btn in row]
        if "my:back:main" not in back_callbacks:
            raise AssertionError("test H — client My bookings list must include back button")
        hub_back = my_bookings_back_kb("ru", from_activity_hub=True)
        hub_back_callbacks = [btn.callback_data for row in hub_back.inline_keyboard for btn in row]
        if "myact:hub" not in hub_back_callbacks:
            raise AssertionError("test H — hub My bookings back must return to activity hub")

        folder_kb = admin_bookings_folder_kb([], "active", 0, 1, "ru")
        folder_callbacks = [btn.callback_data for row in folder_kb.inline_keyboard for btn in row]
        if "adm_book:hub" not in folder_callbacks:
            raise AssertionError("test I — admin bookings folder must include back to bookings hub")

        repo_src = (ROOT / "app" / "repositories" / "__init__.py").read_text(encoding="utf-8")
        list_start = repo_src.find("async def list_for_client(self, client_id: int) -> list[Booking]:")
        list_block = repo_src[list_start : list_start + 400]
        if "attendance_status" in list_block:
            raise AssertionError("test J — My bookings must not filter by attendance_status")

        if not is_manual_attendance_send_eligible(booking_confirmed, now=fixed_now):
            raise AssertionError("test C helper — confirmed future booking must be manual-send eligible")
        if is_manual_attendance_send_eligible(booking_pending, now=fixed_now):
            raise AssertionError("test D helper — pending booking must not be manual-send eligible")

        if resolve_client_lang_for_client is None:
            raise AssertionError("test F — resolve_client_lang_for_client must be importable")

        print("OK: manual attendance, schedule import, and back buttons (tests A–J)")
    except Exception as exc:
        print(f"FAIL: manual attendance / schedule / back buttons — {exc}")
        return 1

    try:
        import asyncio
        import inspect
        from datetime import timedelta
        from types import SimpleNamespace
        from unittest.mock import AsyncMock, MagicMock, patch

        from app.bot.handlers import booking_edit as booking_edit_handlers
        from app.bot.handlers import start as start_handlers
        from app.bot.i18n import t
        from app.bot.keyboards import main_menu
        from app.bot.keyboards.admin_bookings_kb import admin_booking_detail_kb
        from app.bot.utils.menu_helpers import mode_aware_main_menu, show_main_menu
        from app.models import BookingStatus
        from app.services.admin_bookings_service import (
            BookingDetailSource,
            parse_admin_confirm_callback,
        )
        from app.utils.datetime_utils import now_local

        client_both = {
            btn.text for row in main_menu("ru", booking_enabled=True, order_enabled=True).keyboard for btn in row
        }
        for label in (
            t("ru", "main_menu_services"),
            t("ru", "main_menu_my_activity"),
            t("ru", "contact_admin"),
        ):
            if label not in client_both:
                raise AssertionError("test A — both modes menu missing compact button")
        for forbidden in (
            t("ru", "book_appointment"),
            t("ru", "my_bookings"),
            t("ru", "order_services_button"),
            t("ru", "my_orders_button"),
        ):
            if forbidden in client_both:
                raise AssertionError(f"test A — both modes menu must not show {forbidden}")

        client_booking = {
            btn.text for row in main_menu("ru", booking_enabled=True, order_enabled=False).keyboard for btn in row
        }
        if t("ru", "book_appointment") not in client_booking or t("ru", "my_bookings") not in client_booking:
            raise AssertionError("test B — booking-only menu missing booking buttons")
        if t("ru", "order_services_button") in client_booking or t("ru", "my_orders_button") in client_booking:
            raise AssertionError("test B — booking-only menu must not show order buttons")

        client_order = {
            btn.text for row in main_menu("ru", booking_enabled=False, order_enabled=True).keyboard for btn in row
        }
        if t("ru", "order_services_button") not in client_order or t("ru", "my_orders_button") not in client_order:
            raise AssertionError("test C — order-only menu missing order buttons")
        if t("ru", "book_appointment") in client_order or t("ru", "my_bookings") in client_order:
            raise AssertionError("test C — order-only menu must not show booking buttons")

        cancel_src = inspect.getsource(booking_edit_handlers.my_cancel_booking)
        if "show_main_menu" not in cancel_src:
            raise AssertionError("test D — booking cancel must use show_main_menu")

        back_main_src = inspect.getsource(start_handlers.back_main)
        if "show_main_menu" not in back_main_src:
            raise AssertionError("test E — back_main must use show_main_menu")
        orders_src = (ROOT / "app" / "bot" / "handlers" / "orders.py").read_text(encoding="utf-8")
        if "myact:back" in orders_src and "show_main_menu(callback" not in orders_src:
            raise AssertionError("test E — myact:back must use show_main_menu")

        fixed_now = now_local()
        source = BookingDetailSource(section="active", page=0)
        pending = SimpleNamespace(
            id=20,
            status=BookingStatus.PENDING,
            start_at=fixed_now + timedelta(hours=2),
            service_id=1,
            client_id=1,
        )
        confirmed = SimpleNamespace(
            id=21,
            status=BookingStatus.CONFIRMED,
            start_at=fixed_now + timedelta(hours=2),
            service_id=1,
            client_id=1,
        )
        pending_kb = admin_booking_detail_kb(pending, source, lang="ru")
        confirmed_kb = admin_booking_detail_kb(confirmed, source, lang="ru")
        pending_cbs = [btn.callback_data for row in pending_kb.inline_keyboard for btn in row]
        confirmed_cbs = [btn.callback_data for row in confirmed_kb.inline_keyboard for btn in row]
        if any(cb and cb.startswith("adm_att:send:") for cb in pending_cbs):
            raise AssertionError("test F — pending booking must not show manual attendance button")
        if not any(cb and cb.startswith("adm_att:send:") for cb in confirmed_cbs):
            raise AssertionError("test G — confirmed future booking must show manual attendance button")

        confirm_cb = next(cb for cb in pending_cbs if cb and cb.startswith("adm_confirm:"))
        parsed_id, parsed_source = parse_admin_confirm_callback(confirm_cb)
        if parsed_id != 20 or parsed_source.section != "active":
            raise AssertionError("test H — confirm callback must preserve back context")

        admin_src = (ROOT / "app" / "bot" / "handlers" / "admin.py").read_text(encoding="utf-8")
        if "show_booking_detail" not in admin_src or "parse_admin_confirm_callback" not in admin_src:
            raise AssertionError("test H — admin confirm must refresh booking detail with context")

        cancelled = SimpleNamespace(
            id=22,
            status=BookingStatus.CANCELLED,
            start_at=fixed_now + timedelta(hours=2),
            service_id=1,
            client_id=1,
        )
        past = SimpleNamespace(
            id=23,
            status=BookingStatus.CONFIRMED,
            start_at=fixed_now - timedelta(hours=1),
            service_id=1,
            client_id=1,
        )
        for booking in (cancelled, past):
            cbs = [
                btn.callback_data
                for row in admin_booking_detail_kb(booking, source, lang="ru").inline_keyboard
                for btn in row
            ]
            if any(cb and cb.startswith("adm_att:send:") for cb in cbs):
                raise AssertionError("test I — cancelled/past booking must not show manual attendance button")

        async def _mode_aware_menu_smoke() -> None:
            session = MagicMock()
            with patch(
                "app.bot.utils.menu_helpers.menu_mode_kwargs",
                new=AsyncMock(return_value={"booking_enabled": True, "order_enabled": True}),
            ):
                kb = await mode_aware_main_menu("ru", False, session)
            labels = {btn.text for row in kb.keyboard for btn in row}
            if t("ru", "main_menu_my_activity") not in labels:
                raise AssertionError("mode_aware_main_menu must load both modes")

        asyncio.run(_mode_aware_menu_smoke())
        if show_main_menu is None or mode_aware_main_menu is None:
            raise AssertionError("mode-aware menu helpers must be importable")

        print("OK: mode-aware client main menu and admin confirm refresh (tests A–I)")
    except Exception as exc:
        print(f"FAIL: mode-aware client menu — {exc}")
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
