#!/usr/bin/env python3
"""Audit inline keyboard callback_data length and basic Back-button presence."""

from __future__ import annotations

import inspect
import sys
from collections.abc import Callable
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MAX_CALLBACK_BYTES = 64

# Keyboards that must expose a Back / back navigation button (substring match on label or callback).
BACK_KEYBOARD_CHECKS: tuple[tuple[str, Callable[..., object], tuple, dict], ...] = (
    (
        "admin_bookings_hub_kb",
        lambda: __import__("app.bot.keyboards.admin_bookings_kb", fromlist=["admin_bookings_hub_kb"]).admin_bookings_hub_kb("ru"),
        (),
        {},
    ),
    (
        "client_booking_detail_kb",
        lambda: __import__("app.bot.keyboards.booking_edit_kb", fromlist=["client_booking_detail_kb"]).client_booking_detail_kb(
            1, lang="ru", can_reschedule=True, can_cancel=True, can_change_location=False, can_change_address=False, can_change_comment=False
        ),
        (),
        {},
    ),
    (
        "client_orders_hub_kb",
        lambda: __import__("app.bot.keyboards.orders_kb", fromlist=["client_orders_hub_kb"]).client_orders_hub_kb(
            SimpleNamespace(active_count=1, history_count=1), "ru"
        ),
        (),
        {},
    ),
)


def _sample_booking(bid: int = 1, status=None):
    from app.models import BookingStatus

    status = status or BookingStatus.PENDING
    now = datetime(2026, 6, 20, 10, 0)
    return SimpleNamespace(
        id=bid,
        status=status,
        start_at=now + timedelta(days=1),
        end_at=now + timedelta(days=1, hours=1),
        service_id=1,
        client_id=1,
        client_name="Test",
        attendance_status=None,
    )


def _collect_callbacks(markup) -> list[str]:
    if markup is None:
        return []
    keyboard = getattr(markup, "inline_keyboard", None) or getattr(markup, "keyboard", None)
    if not keyboard:
        return []
    out: list[str] = []
    for row in keyboard:
        for btn in row:
            data = getattr(btn, "callback_data", None)
            if data:
                out.append(data)
    return out


def _keyboard_builders() -> list[tuple[str, Callable[..., object], tuple, dict]]:
    from app.bot.keyboards import admin_bookings_kb as abk
    from app.bot.keyboards import orders_kb as okb
    from app.bot.keyboards.admin_bookings_kb import admin_booking_detail_kb, admin_bookings_folder_kb
    from app.bot.keyboards.booking_edit_kb import client_booking_detail_kb, reschedule_dates_kb
    from app.bot.keyboards.booking_time_kb import dates_kb, time_periods_kb
    from app.bot.keyboards.orders_kb import admin_order_detail_kb, admin_orders_folder_kb, client_order_detail_kb
    from app.models import BookingStatus, ServiceOrderStatus
    from app.services.admin_bookings_service import BookingDetailSource

    booking = _sample_booking(42, BookingStatus.PENDING)
    confirmed = _sample_booking(43, BookingStatus.CONFIRMED)
    source = BookingDetailSource(section="active", page=0)
    client_source = BookingDetailSource(
        origin="client",
        client_id=5,
        client_tab="hist",
        client_filter="all",
        page=0,
        client_section_page=1,
    )
    dates = [datetime(2026, 6, 21).date(), datetime(2026, 6, 22).date()]

    return [
        ("admin_bookings_hub_kb", abk.admin_bookings_hub_kb, ("ru",), {}),
        (
            "admin_bookings_folder_kb",
            abk.admin_bookings_folder_kb,
            ([booking], "pending_admin", 0, 1, "ru"),
            {"service_names": {1: "Lesson"}},
        ),
        (
            "admin_booking_detail_kb_pending",
            admin_booking_detail_kb,
            (booking, source, "ru"),
            {},
        ),
        (
            "admin_booking_detail_kb_confirmed",
            admin_booking_detail_kb,
            (confirmed, source, "ru"),
            {"show_send_confirmation": True},
        ),
        (
            "admin_booking_detail_kb_client_origin",
            admin_booking_detail_kb,
            (confirmed, client_source, "ru"),
            {},
        ),
        ("admin_new_booking_notification_kb", abk.admin_new_booking_notification_kb, (99, "ru"), {}),
        ("dates_kb", dates_kb, (dates, "ru"), {}),
        ("time_periods_kb", time_periods_kb, ("ru",), {}),
        (
            "client_booking_detail_kb",
            client_booking_detail_kb,
            (1,),
            {
                "lang": "ru",
                "can_reschedule": True,
                "can_cancel": True,
                "can_change_location": False,
                "can_change_address": False,
                "can_change_comment": False,
            },
        ),
        ("reschedule_dates_kb", reschedule_dates_kb, (1, dates, "ru"), {}),
        ("admin_orders_hub_kb", okb.admin_orders_hub_kb, ({"new": 0, "in_progress": 0, "completed": 0, "declined": 0, "cancelled": 0}, "ru"), {}),
        (
            "admin_orders_folder_kb",
            admin_orders_folder_kb,
            ([], "new", 0, 1, "ru"),
            {},
        ),
        (
            "admin_order_detail_kb_new",
            admin_order_detail_kb,
            (7, ServiceOrderStatus.NEW.value, "new", 0, "ru"),
            {},
        ),
        (
            "admin_order_detail_kb_completed",
            admin_order_detail_kb,
            (8, ServiceOrderStatus.COMPLETED.value, "completed", 0, "ru"),
            {},
        ),
        (
            "client_order_detail_kb",
            client_order_detail_kb,
            (3, ServiceOrderStatus.ACCEPTED.value, "ru"),
            {"section": "active"},
        ),
        ("client_orders_hub_kb", okb.client_orders_hub_kb, (SimpleNamespace(active_count=1, history_count=2), "ru"), {}),
    ]


def _has_back_navigation(markup) -> bool:
    callbacks = _collect_callbacks(markup)
    back_tokens = (
        "back",
        "hub",
        "admin_back",
        "my:back",
        "my_bookings",
        "myact:hub",
        "myord:back",
        "bk:back",
        "adm_book:hub",
        "adm_cli:menu",
        "ord:hub",
    )
    return any(any(token in (cb or "") for token in back_tokens) for cb in callbacks)


def main() -> int:
    print("=== Keyboard audit ===")
    failures = 0
    long_callbacks: list[tuple[str, str, int]] = []
    all_callbacks: list[tuple[str, str]] = []

    for name, builder, args, kwargs in _keyboard_builders():
        try:
            markup = builder(*args, **kwargs)
        except Exception as exc:
            print(f"FAIL: {name} — builder raised {exc!r}")
            failures += 1
            continue
        for cb in _collect_callbacks(markup):
            all_callbacks.append((name, cb))
            size = len(cb.encode("utf-8"))
            if size > MAX_CALLBACK_BYTES:
                long_callbacks.append((name, cb, size))

    for name, builder_fn, _args, _kwargs in BACK_KEYBOARD_CHECKS:
        try:
            markup = builder_fn()
        except Exception as exc:
            print(f"FAIL: back check {name} — {exc!r}")
            failures += 1
            continue
        if not _has_back_navigation(markup):
            print(f"FAIL: {name} — missing back navigation callback")
            failures += 1

    if long_callbacks:
        failures += len(long_callbacks)
        print(f"FAIL: {len(long_callbacks)} callback_data value(s) exceed {MAX_CALLBACK_BYTES} bytes:")
        for name, cb, size in long_callbacks[:20]:
            print(f"  [{name}] ({size}B) {cb!r}")
        if len(long_callbacks) > 20:
            print(f"  ... and {len(long_callbacks) - 20} more")
    else:
        print(f"OK: all {len(all_callbacks)} sampled callback_data <= {MAX_CALLBACK_BYTES} bytes")

    # Spot-check longest client-history booking view callback (compact encoding).
    from app.services.admin_bookings_service import BookingDetailSource, build_booking_view_callback

    worst = build_booking_view_callback(
        99999,
        BookingDetailSource(
            origin="client",
            client_id=123456789,
            client_tab="hist",
            client_filter="all",
            page=9,
            client_section_page=9,
        ),
    )
    worst_len = len(worst.encode("utf-8"))
    if worst_len > MAX_CALLBACK_BYTES:
        print(f"FAIL: worst-case client booking view callback is {worst_len}B: {worst!r}")
        failures += 1
    else:
        print(f"OK: worst-case client booking view callback {worst_len}B")

    if failures:
        print(f"=== Keyboard audit: {failures} issue(s) ===")
        return 1
    print("=== Keyboard audit passed ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
