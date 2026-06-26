#!/usr/bin/env python3
"""Full E2E audit against a temporary SQLite database (no production DB)."""

from __future__ import annotations

import asyncio
import inspect
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

# Bootstrap temp DB before app imports that bind the engine.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.e2e_test_env import bootstrap_temp_database, init_test_database  # noqa: E402

_TEMP_DB = bootstrap_temp_database(prefix="full_e2e")


@dataclass
class Scenario:
    name: str
    passed: bool
    detail: str = ""


RESULTS: list[Scenario] = []


def record(name: str, fn) -> None:
    try:
        fn()
        RESULTS.append(Scenario(name, True))
        print(f"PASS: {name}")
    except AssertionError as exc:
        RESULTS.append(Scenario(name, False, str(exc)))
        print(f"FAIL: {name} — {exc}")
    except Exception as exc:
        RESULTS.append(Scenario(name, False, f"{type(exc).__name__}: {exc}"))
        print(f"FAIL: {name} — {type(exc).__name__}: {exc}")


async def record_async(name: str, coro) -> None:
    try:
        await coro
        RESULTS.append(Scenario(name, True))
        print(f"PASS: {name}")
    except AssertionError as exc:
        RESULTS.append(Scenario(name, False, str(exc)))
        print(f"FAIL: {name} — {exc}")
    except Exception as exc:
        RESULTS.append(Scenario(name, False, f"{type(exc).__name__}: {exc}"))
        print(f"FAIL: {name} — {type(exc).__name__}: {exc}")


def _menu_labels(kb) -> set[str]:
    return {btn.text for row in kb.keyboard for btn in row}


async def _set_modes(session, *, booking: bool, order: bool) -> None:
    from app.repositories import SettingsRepository
    from app.services.service_modes_service import save_booking_mode, save_order_mode

    repo = SettingsRepository(session)
    await repo.set("booking_mode_enabled", "true" if booking else "false")
    await repo.set("order_mode_enabled", "true" if order else "false")
    await session.commit()
    # Ensure save_* invariants
    if booking:
        await save_booking_mode(session, True)
    if order:
        await save_order_mode(session, True)
    await session.commit()


def _e2e_booking_slot(*, offset_minutes: int = 0) -> datetime:
    from app.utils.datetime_utils import normalize_slot, now_local

    now = now_local()
    slot = (now + timedelta(days=7)).replace(hour=10, minute=0, second=0, microsecond=0)
    slot += timedelta(minutes=offset_minutes)
    return normalize_slot(slot)


async def _seed_working_hours(session) -> None:
    from datetime import time as dt_time

    from app.repositories import WorkingHoursRepository

    wh_repo = WorkingHoursRepository(session)
    for day in range(7):
        await wh_repo.upsert_day(day, dt_time(9, 0), dt_time(18, 0))
    await session.commit()


async def scenario_db_migrations() -> None:
    from sqlalchemy import text

    from app.database.session import async_session_factory, init_db

    await init_db()
    async with async_session_factory() as session:
        for table in (
            "services",
            "bookings",
            "clients",
            "service_orders",
            "order_messages",
            "working_breaks",
            "bot_settings",
        ):
            r = await session.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name=:t"),
                {"t": table},
            )
            assert r.fetchone(), f"missing table {table}"

        cols = {
            row[1]
            for row in (
                await session.execute(text("PRAGMA table_info(services)"))
            ).fetchall()
        }
        for col in ("service_type", "price_mode"):
            assert col in cols, f"services missing column {col}"

        booking_cols = {
            row[1]
            for row in (
                await session.execute(text("PRAGMA table_info(bookings)"))
            ).fetchall()
        }
        for col in (
            "client_reminder_1_sent_at",
            "client_reminder_2_sent_at",
            "admin_reminder_sent_at",
        ):
            assert col in booking_cols, f"bookings missing {col}"

        client_cols = {
            row[1]
            for row in (
                await session.execute(text("PRAGMA table_info(clients)"))
            ).fetchall()
        }
        for col in ("language", "username", "phone"):
            assert col in client_cols, f"clients missing {col}"


async def scenario_mode_menus() -> None:
    from app.bot.i18n import t
    from app.bot.keyboards import admin_menu, main_menu
    from app.database.session import async_session_factory

    async with async_session_factory() as session:
        await _set_modes(session, booking=True, order=False)
        client_kb = main_menu(False, "ru", booking_enabled=True, order_enabled=False)
        admin_kb = admin_menu("ru", booking_enabled=True, order_enabled=False)
        labels = _menu_labels(client_kb)
        assert t("ru", "book_appointment") in labels
        assert t("ru", "my_bookings") in labels
        assert t("ru", "order_services_button") not in labels
        assert t("ru", "my_orders_button") not in labels
        admin_labels = _menu_labels(admin_kb)
        assert t("ru", "admin_bookings") in admin_labels
        assert t("ru", "schedule_button") in admin_labels
        assert t("ru", "orders_admin_button") not in admin_labels

        await _set_modes(session, booking=False, order=True)
        client_kb = main_menu(False, "ru", booking_enabled=False, order_enabled=True)
        admin_kb = admin_menu("ru", booking_enabled=False, order_enabled=True)
        labels = _menu_labels(client_kb)
        assert t("ru", "order_services_button") in labels
        assert t("ru", "book_appointment") not in labels
        admin_labels = _menu_labels(admin_kb)
        assert t("ru", "orders_admin_button") in admin_labels
        assert t("ru", "admin_bookings") not in admin_labels
        assert t("ru", "schedule_button") not in admin_labels

        await _set_modes(session, booking=True, order=True)
        client_kb = main_menu(False, "ru", booking_enabled=True, order_enabled=True)
        labels = _menu_labels(client_kb)
        assert t("ru", "main_menu_my_activity") in labels
        admin_kb = admin_menu("ru", booking_enabled=True, order_enabled=True)
        admin_labels = _menu_labels(admin_kb)
        assert t("ru", "admin_bookings") in admin_labels
        assert t("ru", "orders_admin_button") in admin_labels


async def scenario_booking_flow() -> None:
    from aiogram import Bot

    from app.bot.i18n import t
    from app.bot.keyboards.admin_bookings_kb import (
        admin_booking_detail_kb,
        admin_new_booking_notification_kb,
    )
    from app.database.session import async_session_factory
    from app.models import SERVICE_TYPE_BOOKING, BookingStatus
    from app.repositories import BookingRepository, ClientRepository, ServiceRepository
    from app.services.admin_bookings_service import BookingDetailSource, confirm_booking_by_admin
    from app.services.booking_notification_service import notify_admins_new_booking
    from app.services.booking_service import BookingService
    from app.utils.datetime_utils import normalize_slot, now_local
    from app.utils.formatting import format_booking

    bot = MagicMock(spec=Bot)
    bot.send_message = AsyncMock()

    async with async_session_factory() as session:
        await _seed_working_hours(session)
        service = await ServiceRepository(session).create(
            "E2E Lesson",
            "desc",
            60,
            1000,
            service_type=SERVICE_TYPE_BOOKING,
        )
        service.is_active = True
        await session.commit()

        start = _e2e_booking_slot()
        booking = await BookingService(session).create_booking(
            telegram_id=111001,
            service_id=service.id,
            start_at=start,
            client_name="E2E Client",
            client_phone="+79990001122",
        )
        await session.commit()
        assert booking.status == BookingStatus.PENDING

    async with async_session_factory() as session:
        service = await ServiceRepository(session).get_by_id(service.id)
        booking = await BookingRepository(session).get_by_id(booking.id)
        await notify_admins_new_booking(bot, booking, service)

    notif_kb = admin_new_booking_notification_kb(booking.id, "ru")
    cbs = [b.callback_data for row in notif_kb.inline_keyboard for b in row]
    assert any(cb and cb.startswith("adm_confirm:") for cb in cbs)
    assert any(cb and cb.startswith("adm_cancel:") for cb in cbs)

    result1 = await confirm_booking_by_admin(bot, booking.id)
    assert result1.booking and result1.booking.status == BookingStatus.CONFIRMED
    assert result1.client_notified is True
    assert bot.send_message.await_count >= 1

    result2 = await confirm_booking_by_admin(bot, booking.id)
    assert result2.already_confirmed
    assert result2.client_notified is False
    before = bot.send_message.await_count
    await confirm_booking_by_admin(bot, booking.id)
    assert bot.send_message.await_count == before

    async with async_session_factory() as session:
        booking = await BookingRepository(session).get_by_id(booking.id)
        service = await ServiceRepository(session).get_by_id(service.id)
    source = BookingDetailSource(section="active", page=0)
    kb = admin_booking_detail_kb(booking, source, "ru")
    cb_list = [b.callback_data for row in kb.inline_keyboard for b in row]
    assert any(cb and cb.startswith("adm_att:send:") for cb in cb_list)
    text = format_booking(booking, service, "ru", admin_view=True)
    assert t("ru", "booking_status_confirmed") in text
    assert t("ru", "client_response_no_response") in text

    async with async_session_factory() as session:
        await BookingService(session).cancel_booking(booking.id)
        await session.commit()
        cancelled = await BookingRepository(session).get_by_id(booking.id)
    assert cancelled.status == BookingStatus.CANCELLED
    kb_cancelled = admin_booking_detail_kb(cancelled, source, "ru")
    cancelled_cbs = [b.callback_data for row in kb_cancelled.inline_keyboard for b in row]
    assert not any(cb and cb.startswith("adm_confirm:") for cb in cancelled_cbs)


async def scenario_order_flow() -> None:
    from aiogram import Bot

    from app.bot.keyboards.orders_kb import admin_new_order_kb, admin_order_detail_kb, client_order_detail_kb
    from app.database.session import async_session_factory
    from app.models import SERVICE_TYPE_ORDER, ServiceOrderStatus
    from app.repositories import OrderMessageRepository, ServiceOrderRepository, ServiceRepository
    from app.services.order_service import (
        ORDER_MESSAGE_SENDER_ADMIN,
        ORDER_MESSAGE_SENDER_CLIENT,
        accept_order,
        add_order_message,
        create_order,
        decline_order,
        list_order_messages,
        update_order_status,
    )

    bot = MagicMock(spec=Bot)
    bot.send_message = AsyncMock()

    async with async_session_factory() as session:
        service = await ServiceRepository(session).create(
            "E2E Order Svc",
            "order desc",
            0,
            5000,
            service_type=SERVICE_TYPE_ORDER,
        )
        service.is_active = True
        await session.commit()

        order = await create_order(
            session,
            service_id=service.id,
            telegram_id=222002,
            client_name="Order Client",
            client_phone="+79991112233",
            client_username="orderclient",
            details="Need help with paperwork",
        )
        await session.commit()
        assert order.status == ServiceOrderStatus.NEW.value

    new_kb = admin_new_order_kb(order.id, "ru")
    admin_cbs = [b.callback_data for row in new_kb.inline_keyboard for b in row]
    for prefix in ("ord:accept:", "ord:decline:", "ord:view:", "ord:msg:"):
        assert any(cb and cb.startswith(prefix) for cb in admin_cbs), prefix

    async with async_session_factory() as session:
        accepted = await accept_order(session, order.id, admin_telegram_id=900001)
        await session.commit()
    assert accepted and accepted.status == ServiceOrderStatus.ACCEPTED.value

    async with async_session_factory() as session:
        dup = await accept_order(session, order.id, admin_telegram_id=900001)
        await session.commit()
    assert dup and dup.status == ServiceOrderStatus.ACCEPTED.value

    async with async_session_factory() as session:
        await update_order_status(session, order.id, ServiceOrderStatus.IN_PROGRESS.value)
        await session.commit()
        in_prog = await ServiceOrderRepository(session).get_by_id(order.id)
    assert in_prog.status == ServiceOrderStatus.IN_PROGRESS.value

    async with async_session_factory() as session:
        await update_order_status(session, order.id, ServiceOrderStatus.COMPLETED.value)
        await session.commit()
        done = await ServiceOrderRepository(session).get_by_id(order.id)
    assert done.status == ServiceOrderStatus.COMPLETED.value

    completed_kb = admin_order_detail_kb(order.id, ServiceOrderStatus.COMPLETED.value, "completed", 0, "ru")
    completed_cbs = [b.callback_data for row in completed_kb.inline_keyboard for b in row]
    assert not any(cb and cb.startswith("ord:accept:") for cb in completed_cbs)

    client_kb = client_order_detail_kb(order.id, ServiceOrderStatus.COMPLETED.value, "ru", section="history")
    client_cbs = [b.callback_data for row in client_kb.inline_keyboard for b in row]
    assert not any(cb and cb.startswith("myord:cancel:") for cb in client_cbs)

    # Decline flow on a fresh order
    async with async_session_factory() as session:
        order2 = await create_order(
            session,
            service_id=service.id,
            telegram_id=222003,
            client_name="Decline Client",
            client_phone=None,
            client_username=None,
            details="Please decline me",
        )
        await session.commit()
        declined = await decline_order(
            session,
            order2.id,
            reason="Not available this week",
            admin_telegram_id=900001,
        )
        await session.commit()
    assert declined.status == ServiceOrderStatus.DECLINED.value
    assert declined.decline_reason == "Not available this week"

    async with async_session_factory() as session:
        await add_order_message(
            session,
            order_id=order.id,
            sender_type=ORDER_MESSAGE_SENDER_CLIENT,
            message_text="Client follow-up question",
            sender_telegram_id=222002,
        )
        await add_order_message(
            session,
            order_id=order.id,
            sender_type=ORDER_MESSAGE_SENDER_ADMIN,
            message_text="Admin reply text",
            sender_telegram_id=900001,
        )
        await session.commit()
        messages = await list_order_messages(session, order.id)
    assert len(messages) >= 2
    assert any(m.message_text == "Admin reply text" for m in messages)


async def scenario_client_identity() -> None:
    from app.bot.handlers.client import show_my_bookings
    from app.bot.handlers import orders as orders_handlers

    show_src = inspect.getsource(show_my_bookings)
    assert "event.from_user.id" in show_src
    assert "callback.message.from_user" not in show_src

    act_src = inspect.getsource(orders_handlers.my_activity_bookings)
    assert "show_my_bookings(callback" in act_src


async def scenario_reminders_attendance() -> None:
    from app.bot.keyboards.admin_bookings_kb import admin_booking_detail_kb
    from app.database.session import async_session_factory
    from app.models import BookingStatus
    from app.repositories import BookingRepository, ServiceRepository
    from app.services.admin_bookings_service import BookingDetailSource
    from app.services.reminder_service import ReminderService
    from app.utils.datetime_utils import now_local, normalize_slot

    fixed_now = now_local()
    async with async_session_factory() as session:
        service = await ServiceRepository(session).create("Rem Svc", None, 30, 0)
        service.is_active = True
        from app.repositories import ClientRepository

        client = await ClientRepository(session).get_or_create(333003)
        client.language = "ru"
        start = normalize_slot(fixed_now + timedelta(hours=6))
        from app.repositories import BookingRepository as BR

        booking = await BR(session).create(
            client_id=client.id,
            service_id=service.id,
            start_at=start,
            end_at=start + timedelta(minutes=30),
            client_name="Rem Client",
            client_phone=None,
            status=BookingStatus.CONFIRMED,
        )
        await session.commit()
        booking_id = booking.id

    pending = SimpleNamespace(
        id=1,
        status=BookingStatus.PENDING,
        start_at=fixed_now + timedelta(days=1),
        service_id=1,
        client_id=1,
    )
    confirmed = SimpleNamespace(
        id=2,
        status=BookingStatus.CONFIRMED,
        start_at=fixed_now + timedelta(days=1),
        service_id=1,
        client_id=1,
        attendance_status=None,
    )
    source = BookingDetailSource(section="active", page=0)
    pending_cbs = [
        b.callback_data
        for row in admin_booking_detail_kb(pending, source, "ru").inline_keyboard
        for b in row
    ]
    confirmed_cbs = [
        b.callback_data
        for row in admin_booking_detail_kb(confirmed, source, "ru").inline_keyboard
        for b in row
    ]
    assert not any(cb and cb.startswith("adm_att:send:") for cb in pending_cbs)
    assert any(cb and cb.startswith("adm_att:send:") for cb in confirmed_cbs)

    bot = MagicMock()
    bot.send_message = AsyncMock(side_effect=[Exception("client fail"), None])
    reminder = ReminderService(bot)
    disabled = SimpleNamespace(enabled=False)
    session_cm = AsyncMock()
    session_cm.__aenter__.return_value = AsyncMock()
    session_cm.__aexit__.return_value = None
    with patch("app.services.reminder_service.async_session_factory", return_value=session_cm):
        with patch(
            "app.services.reminder_service.load_reminder_config",
            AsyncMock(return_value=disabled),
        ):
            await reminder.process_reminders()


async def scenario_availability() -> None:
    from app.database.session import async_session_factory
    from app.models import BookingStatus
    from app.repositories import BookingRepository, ClientRepository, ServiceRepository
    from app.services.booking_service import BookingService, SlotUnavailableError

    async with async_session_factory() as session:
        await _seed_working_hours(session)
        service = await ServiceRepository(session).create("Slot Svc", None, 60, 0)
        service.is_active = True
        await session.commit()
        service_id = service.id

        client1 = await ClientRepository(session).get_or_create(444004)
        client2 = await ClientRepository(session).get_or_create(444005)
        tid1, tid2 = client1.telegram_id, client2.telegram_id
        await session.commit()

        start = _e2e_booking_slot(offset_minutes=120)
        b1 = await BookingService(session).create_booking(
            telegram_id=tid1,
            service_id=service_id,
            start_at=start,
            client_name="A",
            client_phone=None,
        )
        assert b1.status == BookingStatus.PENDING
        b1_id = b1.id
        await session.commit()

        try:
            await BookingService(session).create_booking(
                telegram_id=tid2,
                service_id=service_id,
                start_at=start,
                client_name="B",
                client_phone=None,
            )
            raise AssertionError("second booking on same slot must fail")
        except SlotUnavailableError:
            pass

        await BookingService(session).cancel_booking(b1_id)
        await session.commit()
        b2 = await BookingService(session).create_booking(
            telegram_id=tid2,
            service_id=service_id,
            start_at=start,
            client_name="B",
            client_phone=None,
        )
        b2_id = b2.id
        await session.commit()
        assert b2_id != b1_id


async def scenario_price_and_service_type() -> None:
    from app.database.session import async_session_factory
    from app.models import PRICE_MODE_FROM, SERVICE_TYPE_BOOKING, SERVICE_TYPE_ORDER
    from app.repositories import ServiceRepository
    from app.utils.formatting import format_service_price_amount, normalize_price_mode

    async with async_session_factory() as session:
        booking_svc = await ServiceRepository(session).create(
            "Booking Svc",
            "b",
            60,
            3000,
            service_type=SERVICE_TYPE_BOOKING,
        )
        order_svc = await ServiceRepository(session).create(
            "Order Svc",
            "o",
            0,
            5000,
            service_type=SERVICE_TYPE_ORDER,
        )
        order_svc.price_mode = PRICE_MODE_FROM
        await session.commit()

    assert booking_svc.duration_minutes == 60
    assert order_svc.service_type == SERVICE_TYPE_ORDER
    assert normalize_price_mode("bogus") == "exact"
    price_from = format_service_price_amount(order_svc, "ru")
    assert "5000" in price_from
    assert "от" in price_from.lower() or "from" in format_service_price_amount(order_svc, "en").lower()


async def scenario_language() -> None:
    from app.bot.i18n import t
    from app.services.booking_notification_service import notify_client_booking_confirmed_by_admin
    from app.utils.formatting import format_booking

    booking = SimpleNamespace(
        id=1,
        status=SimpleNamespace(value="confirmed"),
        start_at=datetime(2026, 7, 1, 10, 0),
        end_at=datetime(2026, 7, 1, 11, 0),
        service_id=1,
        client_id=1,
        client_name="RU Client",
        client_phone=None,
        location_text=None,
        client_comment=None,
        service_location_title=None,
        service_location_address=None,
        attendance_status=None,
    )
    service = SimpleNamespace(id=1, name="Услуга", requires_location=False, ask_client_comment=False)
    text = format_booking(booking, service, "ru", admin_view=True)
    assert t("ru", "booking_status_confirmed") in text

    bot = MagicMock()
    bot.send_message = AsyncMock()
    with patch(
        "app.services.booking_notification_service.resolve_client_lang_for_client",
        AsyncMock(return_value="ru"),
    ), patch(
        "app.database.session.async_session_factory"
    ) as sf:
        cm = MagicMock()
        cm.__aenter__ = AsyncMock(return_value=MagicMock(get=AsyncMock(return_value=MagicMock(telegram_id=1))))
        cm.__aexit__ = AsyncMock(return_value=None)
        sf.return_value = cm
        await notify_client_booking_confirmed_by_admin(bot, booking, service)
    sent = bot.send_message.await_args.args[1]
    assert "подтверждена" in sent.lower() or "confirmed" in sent.lower()


async def scenario_calendar_safety() -> None:
    from app.database.session import async_session_factory
    from app.services.booking_service import BookingService
    from app.services.calendar_service import CalendarService

    class FakeRefreshError(Exception):
        pass

    with patch.dict("sys.modules", {"google.auth.exceptions": SimpleNamespace(RefreshError=FakeRefreshError)}):
        exc = FakeRefreshError("invalid_grant: Token has been expired or revoked.")
        assert CalendarService._is_refresh_token_error(exc)

    async with async_session_factory() as session:
        await _seed_working_hours(session)
        from app.repositories import ServiceRepository

        service = await ServiceRepository(session).create("Cal", None, 30, 0)
        service.is_active = True
        await session.commit()
        service_id = service.id
        with patch("app.services.booking_service._schedule_calendar_sync_create"):
            booking = await BookingService(session).create_booking(
                telegram_id=555006,
                service_id=service_id,
                start_at=_e2e_booking_slot(offset_minutes=240),
                client_name="Cal Client",
                client_phone=None,
                auto_confirm=True,
            )
        assert booking is not None
        assert booking.status.value == "confirmed"


async def scenario_security_patterns() -> None:
    from app.bot.handlers import admin as admin_handlers

    for handler_name in ("admin_confirm_booking", "admin_cancel_booking", "admin_message_client"):
        src = inspect.getsource(getattr(admin_handlers, handler_name))
        assert "is_admin" in src
        assert "access_denied" in src or "if not is_admin" in src


async def scenario_stale_parsers() -> None:
    from app.services.admin_bookings_service import (
        parse_admin_confirm_callback,
        parse_admin_simple_booking_id,
        parse_booking_detail_source,
    )

    for bad in ("adm_confirm:abc",):
        try:
            parse_admin_confirm_callback(bad)
            raise AssertionError("adm_confirm:abc should not parse")
        except ValueError:
            pass
    assert parse_admin_simple_booking_id("adm_cancel:abc", "adm_cancel:") is None
    assert parse_admin_simple_booking_id("adm_msg:xyz", "adm_msg:") is None
    bid, src = parse_booking_detail_source("adm_book:view:abc:from:active:0")
    assert bid is None


async def run_all() -> int:
    print(f"=== E2E full audit (temp DB: {_TEMP_DB}) ===\n")
    await init_test_database()

    await record_async("DB migrations and schema", scenario_db_migrations())
    await record_async("Mode menus (booking / order / both)", scenario_mode_menus())
    await record_async("Booking flow confirm idempotency cancel", scenario_booking_flow())
    await record_async("Order flow accept decline messages", scenario_order_flow())
    await record_async("Client identity from event.from_user.id", scenario_client_identity())
    await record_async("Reminders and attendance UI rules", scenario_reminders_attendance())
    await record_async("Booking slot availability", scenario_availability())
    await record_async("Price mode and service type display", scenario_price_and_service_type())
    await record_async("Language RU notifications", scenario_language())
    await record_async("Calendar failure safety", scenario_calendar_safety())
    await record_async("Admin security handler patterns", scenario_security_patterns())
    await record_async("Stale callback parsers", scenario_stale_parsers())

    passed = sum(1 for r in RESULTS if r.passed)
    failed = [r for r in RESULTS if not r.passed]
    print(f"\n=== Summary: {passed}/{len(RESULTS)} passed ===")
    if failed:
        for item in failed:
            print(f"  FAIL: {item.name} — {item.detail}")
        return 1
    print("=== E2E full audit passed ===")
    return 0


def main() -> int:
    return asyncio.run(run_all())


if __name__ == "__main__":
    raise SystemExit(main())
