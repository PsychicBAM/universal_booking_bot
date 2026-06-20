import logging
import asyncio
import time

from datetime import datetime, timedelta
from html import escape

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.i18n import t
from app.bot.utils.callbacks import safe_callback_answer
from app.bot.utils.service_helpers import (
    client_service_unavailable_key,
    is_booking_service,
    is_service_bookable,
)
from app.bot.utils.telegram_ui import edit_or_send
from app.bot.keyboards import (
    BOOK_APPOINTMENT_TEXTS,
    MAIN_MENU_SERVICES_TEXTS,
    MY_BOOKINGS_TEXTS,
    SKIP_TEXTS,
    admin_menu,
    bookings_kb,
    cancel_kb,
    dates_kb,
    main_menu,
    services_kb,
    skip_cancel_kb,
)
from app.bot.keyboards.booking_time_kb import time_grid_kb, time_periods_kb
from app.bot.utils.time_periods import (
    Period,
    build_period_screen_text,
    build_time_grid_text,
    group_slots_by_period,
    non_empty_periods,
)
from app.bot.states import BookingStates
from app.config import get_settings
from app.bot.booking_client_data import (
    begin_name_collection,
    begin_phone_edit,
    begin_phone_step,
    continue_after_phone,
    continue_booking_after_time,
    handle_contact_message,
    handle_manual_name,
    handle_manual_phone_text,
    handle_phone_method_text,
    load_settings,
    return_to_confirmation,
    show_phone_collection,
)
from app.bot.keyboards.booking_confirm_kb import booking_confirm_kb, booking_edit_menu_kb
from app.models import SERVICE_TYPE_BOOKING
from app.database.session import async_session_factory
from app.repositories import (
    BookingRepository,
    ClientRepository,
    ServiceLocationRepository,
    ServiceMediaRepository,
    ServiceRepository,
    SettingsRepository,
    UnavailableRepository,
    WorkingHoursRepository,
    WorkingBreakRepository,
)
from app.bot.keyboards.service_location_kb import client_locations_kb
from app.services.service_media_service import send_service_presentation
from app.services.availability_service import AvailabilityService
from app.services.booking_service import BookingService
from app.services.exceptions import SlotUnavailableError
from app.services.calendar_service import CalendarService
from app.services.language_service import get_user_language
from app.utils.datetime_utils import now_local, slot_from_timestamp, to_local_naive
from app.utils.formatting import format_booking, format_date, format_datetime, format_service, format_time
from app.utils.perf_logging import log_action_timing

router = Router()
logger = logging.getLogger(__name__)


def _parse_service_id(callback_data: str) -> int:
    return int(callback_data.rsplit(":", 1)[1])


def _booking_summary(data: dict, lang: str) -> str:
    slot = slot_from_timestamp(data["slot_ts"])
    service_name = escape(str(data.get("service_name") or ""))
    client_name = escape(str(data.get("client_name") or ""))
    phone = escape(str(data.get("client_phone") or "")) or t(lang, "booking_phone_not_provided")
    requires_location = bool(data.get("requires_location"))
    ask_client_comment = bool(data.get("ask_client_comment"))
    lines = [
        f"{t(lang, 'booking_review_title')}\n",
        f"{t(lang, 'label_service')}: {service_name}",
        f"{t(lang, 'label_datetime')}: {format_datetime(slot)}",
        f"{t(lang, 'label_name')}: {client_name}",
        f"{t(lang, 'label_phone')}: {phone}",
    ]
    if data.get("service_location_title"):
        lines.append(
            t(lang, "service_location_label", title=escape(str(data["service_location_title"])))
        )
        if data.get("service_location_address"):
            lines.append(
                t(lang, "address_label", address=escape(str(data["service_location_address"])))
            )
    if requires_location or data.get("location_text"):
        location = (
            escape(str(data["location_text"]))
            if data.get("location_text")
            else t(lang, "not_provided")
        )
        lines.append(t(lang, "client_address_label", location=location))
    if ask_client_comment or data.get("client_comment"):
        if data.get("client_comment"):
            comment = escape(str(data["client_comment"]))
        elif ask_client_comment:
            comment = t(lang, "comment_not_provided")
        else:
            comment = escape(str(data["client_comment"]))
        lines.append(t(lang, "service_comment_label", comment=comment))
    return "\n".join(lines)


async def _prompt_comment(message: Message, state: FSMContext, lang: str) -> None:
    await state.set_state(BookingStates.entering_comment)
    await message.answer(
        f"{t(lang, 'ask_comment_prompt')}\n{t(lang, 'comment_optional_hint')}",
        reply_markup=skip_cancel_kb(lang),
    )


async def _show_confirmation(message: Message, state: FSMContext, lang: str) -> None:
    await state.set_state(BookingStates.confirming)
    await message.answer(
        _booking_summary(await state.get_data(), lang),
        reply_markup=booking_confirm_kb(lang),
    )


async def _start_date_selection(
    callback: CallbackQuery,
    state: FSMContext,
    lang: str,
    service_id: int,
    *,
    t_answer: float = 0.0,
) -> None:
    t_total = time.perf_counter()
    settings = get_settings()
    service = None
    dates: list = []
    t_service = 0.0
    t_availability = 0.0

    await edit_or_send(callback, t(lang, "searching_dates"))

    try:
        async with asyncio.timeout(settings.availability_timeout_seconds):
            t0 = time.perf_counter()
            async with async_session_factory() as session:
                service = await ServiceRepository(session).get_by_id(service_id)
                if not is_service_bookable(service):
                    await callback.message.answer(t(lang, client_service_unavailable_key(service)))
                    await state.clear()
                    return
                t_service = time.perf_counter() - t0

                await state.set_state(BookingStates.choosing_date)

                t0 = time.perf_counter()
                availability = AvailabilityService(
                    WorkingHoursRepository(session),
                    UnavailableRepository(session),
                    BookingRepository(session),
                    CalendarService(session),
                    WorkingBreakRepository(session),
                )
                dates = await availability.get_available_dates(
                    service_id, ServiceRepository(session)
                )
                t_availability = time.perf_counter() - t0
    except TimeoutError:
        logger.warning(
            "book availability timed out after %.1fs service_id=%s user_id=%s",
            settings.availability_timeout_seconds,
            service_id,
            callback.from_user.id,
        )
        await edit_or_send(callback, t(lang, "dates_load_timeout"))
        await state.clear()
        return
    except Exception:
        logger.exception("book availability failed service_id=%s", service_id)
        await edit_or_send(callback, t(lang, "dates_load_timeout"))
        await state.clear()
        return

    t0 = time.perf_counter()
    if not dates:
        await edit_or_send(callback, t(lang, "no_dates"))
        await state.clear()
        t_send = time.perf_counter() - t0
        logger.info(
            "book timing: answer=%.2fs service=%.2fs availability=%.2fs send=%.2fs total=%.2fs (no dates)",
            t_answer,
            t_service,
            t_availability,
            t_send,
            time.perf_counter() - t_total,
        )
        return

    await edit_or_send(
        callback,
        f"{format_service(service, lang)}\n\n{t(lang, 'choose_date')}",
        reply_markup=dates_kb(dates, lang),
    )
    t_send = time.perf_counter() - t0
    total = time.perf_counter() - t_total
    log_action_timing(
        "loading dates",
        service_id=service_id,
        db=t_service,
        availability=t_availability,
        send=t_send,
        total=total,
    )


async def _navigate_to_time_selection(
    callback: CallbackQuery,
    state: FSMContext,
    lang: str,
) -> None:
    from datetime import date as date_cls

    data = await state.get_data()
    service_id = data.get("service_id")
    target_date_raw = data.get("target_date")
    period = data.get("time_period")
    if not service_id:
        await edit_or_send(callback, t(lang, "session_expired"))
        return
    if not target_date_raw:
        await _show_dates_screen(callback, state, lang, service_id)
        return
    target_date = date_cls.fromisoformat(target_date_raw)
    if period in ("morning", "day", "evening"):
        await _show_time_grid_for_period(
            callback, state, lang, service_id, target_date, period  # type: ignore[arg-type]
        )
        return
    await _show_period_screen(callback, state, lang, service_id, target_date)


async def _show_service_card(
    callback: CallbackQuery,
    state: FSMContext,
    lang: str,
    bot: Bot,
    service_id: int,
) -> None:
    async with async_session_factory() as session:
        service = await ServiceRepository(session).get_by_id(service_id)
        if not is_service_bookable(service):
            await edit_or_send(callback, t(lang, client_service_unavailable_key(service)))
            return
        media_items = await ServiceMediaRepository(session).list_for_service(service_id)
        photos = await ServiceMediaRepository(session).count_photos(service_id)
        videos = await ServiceMediaRepository(session).count_videos(service_id)

    await state.set_state(BookingStates.choosing_service)
    chat_id = callback.message.chat.id
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass

    if service.show_media_to_clients and media_items:
        await send_service_presentation(
            bot,
            chat_id,
            service,
            media_items,
            lang,
            photos_count=photos,
            videos_count=videos,
            media_mode="open",
        )
    else:
        await send_service_presentation(
            bot,
            chat_id,
            service,
            media_items,
            lang,
            photos_count=photos,
            videos_count=videos,
            media_mode="card_only",
        )


async def _show_service_or_location_back(
    callback: CallbackQuery,
    state: FSMContext,
    lang: str,
    bot: Bot,
) -> None:
    data = await state.get_data()
    service_id = data.get("service_id")
    if not service_id:
        await edit_or_send(callback, t(lang, "session_expired"))
        await state.clear()
        return

    await state.update_data(
        target_date=None,
        time_period=None,
        slot_ts=None,
        service_location_id=None,
        service_location_title=None,
        service_location_address=None,
    )

    async with async_session_factory() as session:
        service = await ServiceRepository(session).get_by_id(service_id)
        if not is_service_bookable(service):
            await edit_or_send(callback, t(lang, client_service_unavailable_key(service)))
            return
        locations = await ServiceLocationRepository(session).list_active_for_service(service_id)

    if locations:
        await state.set_state(BookingStates.choosing_service_location)
        await edit_or_send(
            callback,
            f"{format_service(service, lang)}\n\n{t(lang, 'choose_service_location')}",
            reply_markup=client_locations_kb(locations, lang),
        )
        return

    await _show_service_card(callback, state, lang, bot, service_id)


async def _fetch_slots_for_date(service_id: int, target_date) -> list:
    async with async_session_factory() as session:
        availability = AvailabilityService(
            WorkingHoursRepository(session),
            UnavailableRepository(session),
            BookingRepository(session),
            CalendarService(session),
            WorkingBreakRepository(session),
        )
        return await availability.get_available_slots(
            service_id, target_date, ServiceRepository(session)
        )


async def _show_dates_screen(
    callback: CallbackQuery,
    state: FSMContext,
    lang: str,
    service_id: int,
) -> None:
    async with async_session_factory() as session:
        service = await ServiceRepository(session).get_by_id(service_id)
        if not is_service_bookable(service):
            await edit_or_send(callback, t(lang, client_service_unavailable_key(service)))
            await state.clear()
            return
        availability = AvailabilityService(
            WorkingHoursRepository(session),
            UnavailableRepository(session),
            BookingRepository(session),
            CalendarService(session),
            WorkingBreakRepository(session),
        )
        dates = await availability.get_available_dates(service_id, ServiceRepository(session))

    if not dates:
        await edit_or_send(callback, t(lang, "no_dates"))
        await state.clear()
        return

    await state.set_state(BookingStates.choosing_date)
    await state.update_data(time_period=None)
    await edit_or_send(
        callback,
        f"{format_service(service, lang)}\n\n{t(lang, 'choose_date')}",
        reply_markup=dates_kb(dates, lang),
    )


async def _show_period_screen(
    callback: CallbackQuery,
    state: FSMContext,
    lang: str,
    service_id: int,
    target_date,
) -> None:
    t_total = time.perf_counter()
    t0 = time.perf_counter()
    slots = await _fetch_slots_for_date(service_id, target_date)
    t_slots = time.perf_counter() - t0

    if not slots:
        await edit_or_send(callback, t(lang, "no_slots"))
        await state.set_state(BookingStates.choosing_date)
        return

    grouped = group_slots_by_period(slots)
    available_periods = non_empty_periods(grouped)
    if not available_periods:
        await edit_or_send(callback, t(lang, "no_slots"))
        await state.set_state(BookingStates.choosing_date)
        return

    await state.update_data(target_date=target_date.isoformat(), time_period=None)
    await state.set_state(BookingStates.choosing_time_period)

    text = build_period_screen_text(target_date, grouped, lang)
    t0 = time.perf_counter()
    await edit_or_send(callback, text, reply_markup=time_periods_kb(available_periods, lang))
    t_send = time.perf_counter() - t0
    log_action_timing(
        "time period",
        date=target_date.isoformat(),
        periods=len(available_periods),
        total_slots=len(slots),
        slots=t_slots,
        send=t_send,
        total=time.perf_counter() - t_total,
    )


async def _show_time_grid_for_period(
    callback: CallbackQuery,
    state: FSMContext,
    lang: str,
    service_id: int,
    target_date,
    period: Period,
) -> None:
    t_total = time.perf_counter()
    t0 = time.perf_counter()
    slots = await _fetch_slots_for_date(service_id, target_date)
    period_slots = group_slots_by_period(slots).get(period, [])
    t_slots = time.perf_counter() - t0

    if not period_slots:
        await _show_period_screen(callback, state, lang, service_id, target_date)
        return

    await state.update_data(time_period=period)
    await state.set_state(BookingStates.choosing_time)

    text = build_time_grid_text(target_date, period, lang)
    t0 = time.perf_counter()
    await edit_or_send(callback, text, reply_markup=time_grid_kb(period_slots, lang))
    t_send = time.perf_counter() - t0
    log_action_timing(
        "time grid",
        date=target_date.isoformat(),
        period=period,
        slots=len(period_slots),
        load=t_slots,
        send=t_send,
        total=time.perf_counter() - t_total,
    )


async def _notify_admins_new_booking(bot, booking, service, lang: str) -> None:
    settings = get_settings()
    async with async_session_factory() as session:
        from app.models import Client

        client = await session.get(Client, booking.client_id)
        username = client.username if client else None
    for admin_id in settings.admin_ids:
        admin_lang = await get_user_language(admin_id)
        try:
            await bot.send_message(
                admin_id,
                f"{t(admin_lang, 'new_booking_admin')}\n\n{format_booking(booking, service, admin_lang, admin_view=True, client_username=username)}",
            )
        except Exception:
            pass


@router.message(F.text.in_(MAIN_MENU_SERVICES_TEXTS))
async def start_unified_services_from_client(message: Message, state: FSMContext, lang: str) -> None:
    async with async_session_factory() as session:
        services = await ServiceRepository(session).list_client_services()
    if not services:
        await message.answer(t(lang, "no_services"))
        return
    await state.update_data(flow_origin="client", flow_kind="unified")
    await state.set_state(BookingStates.choosing_service)
    await message.answer(
        t(lang, "choose_service"),
        reply_markup=services_kb(services, lang, show_type_icons=True),
    )


@router.message(F.text.in_(BOOK_APPOINTMENT_TEXTS))
async def start_booking(message: Message, state: FSMContext, lang: str) -> None:
    async with async_session_factory() as session:
        services = await ServiceRepository(session).list_client_services(
            service_type=SERVICE_TYPE_BOOKING
        )
    if not services:
        await message.answer(t(lang, "no_services"))
        return
    await state.update_data(flow_origin="client", flow_kind="booking")
    await state.set_state(BookingStates.choosing_service)
    await message.answer(t(lang, "choose_service"), reply_markup=services_kb(services, lang))


@router.callback_query(BookingStates.choosing_service, F.data.regexp(r"^svc:\d+$"))
async def view_service(callback: CallbackQuery, state: FSMContext, lang: str, bot: Bot) -> None:
    t_total = time.perf_counter()
    service_id = int(callback.data.split(":", 1)[1])
    await safe_callback_answer(callback)

    t0 = time.perf_counter()
    async with async_session_factory() as session:
        service = await ServiceRepository(session).get_by_id(service_id)
        if not is_service_bookable(service):
            await callback.message.answer(t(lang, client_service_unavailable_key(service)))
            return
        media_items = await ServiceMediaRepository(session).list_for_service(service_id)
        photos = await ServiceMediaRepository(session).count_photos(service_id)
        videos = await ServiceMediaRepository(session).count_videos(service_id)
    t_db = time.perf_counter() - t0

    flow_kind = (await state.get_data()).get("flow_kind", "booking")
    await state.update_data(flow_origin="client", flow_kind=flow_kind)
    await state.set_state(BookingStates.choosing_service)
    chat_id = callback.message.chat.id
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass

    t0 = time.perf_counter()
    if service.show_media_to_clients and media_items:
        await send_service_presentation(
            bot,
            chat_id,
            service,
            media_items,
            lang,
            photos_count=photos,
            videos_count=videos,
            media_mode="open",
        )
    else:
        await send_service_presentation(
            bot,
            chat_id,
            service,
            media_items,
            lang,
            photos_count=photos,
            videos_count=videos,
            media_mode="card_only",
        )
    t_send = time.perf_counter() - t0
    log_action_timing(
        "service card",
        service_id=service_id,
        db=t_db,
        send=t_send,
        total=time.perf_counter() - t_total,
    )


async def _services_for_back(state: FSMContext, session) -> tuple[list, bool]:
    data = await state.get_data()
    flow_kind = data.get("flow_kind", "booking")
    repo = ServiceRepository(session)
    if flow_kind == "order":
        return await repo.list_client_services(service_type=SERVICE_TYPE_ORDER), False
    if flow_kind == "unified":
        return await repo.list_client_services(), True
    return await repo.list_client_services(service_type=SERVICE_TYPE_BOOKING), False


@router.callback_query(BookingStates.choosing_service_location, F.data == "cb:svc_back")
@router.callback_query(BookingStates.choosing_service, F.data == "cb:svc_back")
async def back_to_services(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    async with async_session_factory() as session:
        services, show_icons = await _services_for_back(state, session)
    if not services:
        await edit_or_send(callback, t(lang, "no_services"))
        await state.clear()
        await safe_callback_answer(callback)
        return
    await state.set_state(BookingStates.choosing_service)
    data = await state.get_data()
    flow_kind = data.get("flow_kind", "booking")
    await state.update_data(flow_kind=flow_kind)
    await state.update_data(
        service_location_id=None,
        service_location_title=None,
        service_location_address=None,
    )
    await edit_or_send(
        callback,
        t(lang, "choose_service"),
        reply_markup=services_kb(services, lang, show_type_icons=show_icons),
    )
    await safe_callback_answer(callback)


@router.callback_query(BookingStates.choosing_service, F.data.startswith("cb:photos:"))
async def view_service_photos(callback: CallbackQuery, lang: str, bot: Bot) -> None:
    t_total = time.perf_counter()
    service_id = _parse_service_id(callback.data)
    await safe_callback_answer(callback)

    t0 = time.perf_counter()
    async with async_session_factory() as session:
        service = await ServiceRepository(session).get_by_id(service_id)
        if not is_service_bookable(service):
            await callback.message.answer(t(lang, client_service_unavailable_key(service)))
            return
        if not service.show_media_to_clients:
            await callback.message.answer(t(lang, "not_found"))
            return
        media_items = await ServiceMediaRepository(session).list_for_service(service_id)
        photos = await ServiceMediaRepository(session).count_photos(service_id)
        videos = await ServiceMediaRepository(session).count_videos(service_id)
    t_db = time.perf_counter() - t0

    chat_id = callback.message.chat.id
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass

    t0 = time.perf_counter()
    await send_service_presentation(
        bot,
        chat_id,
        service,
        media_items,
        lang,
        photos_count=photos,
        videos_count=videos,
        media_mode="photos",
    )
    t_send = time.perf_counter() - t0
    log_action_timing(
        "service photos",
        service_id=service_id,
        db=t_db,
        send=t_send,
        total=time.perf_counter() - t_total,
    )


@router.callback_query(BookingStates.choosing_service, F.data.startswith("cb:video:"))
async def view_service_video(callback: CallbackQuery, lang: str, bot: Bot) -> None:
    t_total = time.perf_counter()
    service_id = _parse_service_id(callback.data)
    await safe_callback_answer(callback)

    t0 = time.perf_counter()
    async with async_session_factory() as session:
        service = await ServiceRepository(session).get_by_id(service_id)
        if not is_service_bookable(service):
            await callback.message.answer(t(lang, client_service_unavailable_key(service)))
            return
        if not service.show_media_to_clients:
            await callback.message.answer(t(lang, "not_found"))
            return
        media_items = await ServiceMediaRepository(session).list_for_service(service_id)
        photos = await ServiceMediaRepository(session).count_photos(service_id)
        videos = await ServiceMediaRepository(session).count_videos(service_id)
    t_db = time.perf_counter() - t0

    chat_id = callback.message.chat.id
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass

    t0 = time.perf_counter()
    await send_service_presentation(
        bot,
        chat_id,
        service,
        media_items,
        lang,
        photos_count=photos,
        videos_count=videos,
        media_mode="video",
    )
    t_send = time.perf_counter() - t0
    log_action_timing(
        "service video",
        service_id=service_id,
        db=t_db,
        send=t_send,
        total=time.perf_counter() - t_total,
    )


@router.callback_query(F.data.startswith("cb:book:"))
async def choose_service(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    t_total = time.perf_counter()
    current_state = await state.get_state()
    service_id = int(callback.data.rsplit(":", 1)[1])
    logger.info(
        "book callback: data=%s parsed_service_id=%s fsm_state=%s user_id=%s",
        callback.data,
        service_id,
        current_state,
        callback.from_user.id,
    )

    t0 = time.perf_counter()
    await safe_callback_answer(callback)
    t_answer = time.perf_counter() - t0

    async with async_session_factory() as session:
        service = await ServiceRepository(session).get_by_id(service_id)
        if not is_service_bookable(service) or not is_booking_service(service):
            await callback.message.answer(t(lang, client_service_unavailable_key(service)))
            return
        locations = await ServiceLocationRepository(session).list_active_for_service(service_id)

    await state.update_data(
        service_id=service_id,
        service_name=service.name,
        requires_location=service.requires_location,
        ask_client_comment=service.ask_client_comment,
        flow_origin="client",
    )

    if locations:
        await state.set_state(BookingStates.choosing_service_location)
        await edit_or_send(
            callback,
            f"{format_service(service, lang)}\n\n{t(lang, 'choose_service_location')}",
            reply_markup=client_locations_kb(locations, lang),
        )
        logger.info(
            "book timing: answer=%.2fs total=%.2fs (location selection, %s locations)",
            t_answer,
            time.perf_counter() - t_total,
            len(locations),
        )
        log_action_timing(
            "service location",
            service_id=service_id,
            answer=t_answer,
            total=time.perf_counter() - t_total,
        )
        return

    await _start_date_selection(callback, state, lang, service_id, t_answer=t_answer)


@router.callback_query(BookingStates.choosing_service_location, F.data.startswith("cb:loc:"))
async def choose_service_location(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await safe_callback_answer(callback)
    location_id = int(callback.data.rsplit(":", 1)[1])
    data = await state.get_data()
    service_id = data.get("service_id")
    if not service_id:
        await state.clear()
        await callback.message.answer(t(lang, "session_expired"))
        return

    async with async_session_factory() as session:
        location = await ServiceLocationRepository(session).get_by_id(location_id)
        if (
            not location
            or location.service_id != service_id
            or not location.is_active
        ):
            await callback.message.answer(t(lang, "not_found"))
            return

    await state.update_data(
        service_location_id=location.id,
        service_location_title=location.title,
        service_location_address=location.address_text,
    )
    await _start_date_selection(callback, state, lang, service_id)


@router.callback_query(BookingStates.choosing_date, F.data == "bk:back:service")
async def back_to_service_from_dates(callback: CallbackQuery, state: FSMContext, lang: str, bot: Bot) -> None:
    await safe_callback_answer(callback)
    await _show_service_or_location_back(callback, state, lang, bot)


@router.callback_query(BookingStates.choosing_date, F.data.startswith("date:"))
async def choose_date(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    from datetime import date as date_cls

    await safe_callback_answer(callback)
    target_date = date_cls.fromisoformat(callback.data.split(":", 1)[1])
    data = await state.get_data()
    service_id = data["service_id"]
    await _show_period_screen(callback, state, lang, service_id, target_date)


@router.callback_query(BookingStates.choosing_time_period, F.data.startswith("bk:period:"))
async def choose_time_period(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    from datetime import date as date_cls

    await safe_callback_answer(callback)
    period = callback.data.rsplit(":", 1)[1]
    if period not in ("morning", "day", "evening"):
        return
    data = await state.get_data()
    service_id = data.get("service_id")
    target_date_raw = data.get("target_date")
    if not service_id or not target_date_raw:
        await edit_or_send(callback, t(lang, "session_expired"))
        return
    target_date = date_cls.fromisoformat(target_date_raw)
    await _show_time_grid_for_period(
        callback, state, lang, service_id, target_date, period  # type: ignore[arg-type]
    )


@router.callback_query(BookingStates.choosing_time_period, F.data == "bk:back:dates")
@router.callback_query(BookingStates.choosing_time, F.data == "bk:back:dates")
async def back_to_dates(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await safe_callback_answer(callback)
    data = await state.get_data()
    service_id = data.get("service_id")
    if not service_id:
        await edit_or_send(callback, t(lang, "session_expired"))
        await state.clear()
        return
    await _show_dates_screen(callback, state, lang, service_id)


@router.callback_query(BookingStates.choosing_time, F.data == "bk:back:periods")
async def back_to_periods(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    from datetime import date as date_cls

    await safe_callback_answer(callback)
    data = await state.get_data()
    service_id = data.get("service_id")
    target_date_raw = data.get("target_date")
    if not service_id or not target_date_raw:
        await edit_or_send(callback, t(lang, "session_expired"))
        return
    target_date = date_cls.fromisoformat(target_date_raw)
    await _show_period_screen(callback, state, lang, service_id, target_date)


@router.callback_query(BookingStates.choosing_time, F.data.startswith("time:"))
async def choose_time(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await safe_callback_answer(callback)
    slot_ts = int(callback.data.split(":", 1)[1])
    slot = slot_from_timestamp(slot_ts)
    await state.update_data(slot_ts=slot_ts, flow_origin="client")
    await edit_or_send(callback, t(lang, "selected", dt=format_datetime(slot)))
    await continue_booking_after_time(callback.message, state, lang, callback.from_user)


@router.callback_query(BookingStates.confirming_telegram_name, F.data == "bkdata:name:yes")
async def confirm_telegram_name_yes(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await safe_callback_answer(callback)
    from app.services.client_data_service import build_telegram_full_name

    name = build_telegram_full_name(callback.from_user)
    if not name:
        await state.set_state(BookingStates.entering_name)
        await callback.message.answer(t(lang, "enter_name"), reply_markup=cancel_kb(lang))
        return
    await state.update_data(client_name=name)
    async with async_session_factory() as session:
        await ClientRepository(session).set_display_name(callback.from_user.id, name)
        await session.commit()
    settings = await load_settings()
    await begin_phone_step(callback.message, state, lang, callback.from_user.id, settings)


@router.callback_query(BookingStates.confirming_telegram_name, F.data == "bkdata:name:manual")
async def confirm_telegram_name_manual(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await safe_callback_answer(callback)
    await state.set_state(BookingStates.entering_name)
    await callback.message.answer(t(lang, "enter_name"), reply_markup=cancel_kb(lang))


@router.callback_query(BookingStates.choosing_phone_method, F.data.startswith("bkdata:phone:"))
async def choose_phone_method(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await safe_callback_answer(callback)
    action = callback.data.split(":", 2)[2]
    settings = await load_settings()
    if action == "saved_yes":
        async with async_session_factory() as session:
            client = await ClientRepository(session).get_by_telegram_id(callback.from_user.id)
        if client and client.phone:
            await state.update_data(client_phone=client.phone)
            data = await state.get_data()
            if data.get("editing_from_confirm"):
                await state.update_data(editing_from_confirm=False)
                await return_to_confirmation(callback.message, state, lang)
                return
            await continue_after_phone(callback.message, state, lang)
        return
    if action == "contact":
        await show_phone_collection(callback.message, state, lang, settings)
        return
    if action == "manual":
        await state.set_state(BookingStates.entering_phone_manual)
        await callback.message.answer(t(lang, "booking_manual_phone_prompt"), reply_markup=cancel_kb(lang))
        return
    if action == "skip" and not settings.phone_required:
        await state.update_data(client_phone=None)
        data = await state.get_data()
        if data.get("editing_from_confirm"):
            await state.update_data(editing_from_confirm=False)
            await return_to_confirmation(callback.message, state, lang)
            return
        await continue_after_phone(callback.message, state, lang)


@router.message(BookingStates.entering_name, F.text)
async def enter_name(message: Message, state: FSMContext, lang: str) -> None:
    await state.update_data(flow_origin="client")
    await handle_manual_name(message, state, lang)


@router.message(BookingStates.entering_phone_manual, F.text)
async def enter_phone_manual(message: Message, state: FSMContext, lang: str) -> None:
    await state.update_data(flow_origin="client")
    await handle_manual_phone_text(message, state, lang)


@router.message(BookingStates.choosing_phone_method, F.contact)
async def enter_phone_contact(message: Message, state: FSMContext, lang: str) -> None:
    await state.update_data(flow_origin="client")
    await handle_contact_message(message, state, lang)


@router.message(BookingStates.choosing_phone_method, F.text)
async def enter_phone_method_text(message: Message, state: FSMContext, lang: str) -> None:
    await state.update_data(flow_origin="client")
    if await handle_phone_method_text(message, state, lang):
        return
    if message.text.strip() == t(lang, "cancel"):
        return
    settings = await load_settings()
    if message.text.strip() == t(lang, "booking_share_phone_button"):
        return
    await message.answer(t(lang, "booking_contact_prompt"))


@router.message(BookingStates.entering_phone, F.text)
async def enter_phone_legacy(message: Message, state: FSMContext, lang: str) -> None:
    await state.update_data(flow_origin="client")
    await handle_manual_phone_text(message, state, lang)


@router.message(BookingStates.entering_location, F.text)
async def enter_location(message: Message, state: FSMContext, lang: str) -> None:
    location = message.text.strip()
    if not location:
        await message.answer(t(lang, "enter_location"), reply_markup=cancel_kb(lang))
        return
    await state.update_data(location_text=location, flow_origin="client")
    data = await state.get_data()
    if data.get("editing_from_confirm"):
        await state.update_data(editing_from_confirm=False)
        await _show_confirmation(message, state, lang)
        return
    if data.get("ask_client_comment"):
        await _prompt_comment(message, state, lang)
        return
    await _show_confirmation(message, state, lang)


@router.message(BookingStates.entering_comment, F.text.in_(SKIP_TEXTS))
async def skip_comment(message: Message, state: FSMContext, lang: str) -> None:
    await state.update_data(client_comment=None, flow_origin="client")
    data = await state.get_data()
    if data.get("editing_from_confirm"):
        await state.update_data(editing_from_confirm=False)
    await _show_confirmation(message, state, lang)


@router.message(BookingStates.entering_comment, F.text)
async def enter_comment(message: Message, state: FSMContext, lang: str) -> None:
    await state.update_data(client_comment=message.text.strip(), flow_origin="client")
    data = await state.get_data()
    if data.get("editing_from_confirm"):
        await state.update_data(editing_from_confirm=False)
    await _show_confirmation(message, state, lang)


@router.callback_query(BookingStates.confirming, F.data == "bkdata:edit:menu")
async def booking_edit_menu(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await safe_callback_answer(callback)
    data = await state.get_data()
    await callback.message.answer(
        t(lang, "booking_edit_what"),
        reply_markup=booking_edit_menu_kb(
            lang,
            requires_location=bool(data.get("requires_location")),
            ask_client_comment=bool(data.get("ask_client_comment")),
        ),
    )


@router.callback_query(F.data == "bkdata:edit:back")
async def booking_edit_back(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await safe_callback_answer(callback)
    await return_to_confirmation(callback.message, state, lang)


@router.callback_query(F.data == "bkdata:edit:name")
async def booking_edit_name(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await safe_callback_answer(callback)
    await state.update_data(editing_from_confirm=True)
    await state.set_state(BookingStates.entering_name)
    await callback.message.answer(t(lang, "enter_name"), reply_markup=cancel_kb(lang))


@router.callback_query(F.data == "bkdata:edit:phone")
async def booking_edit_phone(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await safe_callback_answer(callback)
    await state.update_data(editing_from_confirm=True)
    await begin_phone_edit(callback.message, state, lang, callback.from_user.id)


@router.callback_query(F.data == "bkdata:edit:location")
async def booking_edit_location(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await safe_callback_answer(callback)
    await state.update_data(editing_from_confirm=True)
    await state.set_state(BookingStates.entering_location)
    await callback.message.answer(t(lang, "enter_location"), reply_markup=cancel_kb(lang))


@router.callback_query(F.data == "bkdata:edit:comment")
async def booking_edit_comment(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await safe_callback_answer(callback)
    await state.update_data(editing_from_confirm=True)
    await _prompt_comment(callback.message, state, lang)


@router.callback_query(BookingStates.confirming, F.data == "bk:back:time")
@router.callback_query(BookingStates.confirming_telegram_name, F.data == "bk:back:time")
@router.callback_query(BookingStates.choosing_phone_method, F.data == "bk:back:time")
async def back_to_time(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await safe_callback_answer(callback)
    await _navigate_to_time_selection(callback, state, lang)


@router.callback_query(BookingStates.confirming, F.data == "bk:confirm:back")
async def booking_confirm_back_legacy(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await safe_callback_answer(callback)
    await _navigate_to_time_selection(callback, state, lang)


@router.callback_query(BookingStates.confirming, F.data == "confirm:yes")
async def confirm_booking(callback: CallbackQuery, state: FSMContext, is_admin: bool, lang: str) -> None:
    data = await state.get_data()
    if data.get("booking_confirm_in_progress"):
        logger.info("Duplicate confirm tap ignored for user %s", callback.from_user.id)
        await safe_callback_answer(callback, t(lang, "booking_request_in_progress"), show_alert=True)
        return

    await safe_callback_answer(callback)

    service_id = data.get("service_id")
    slot_ts = data.get("slot_ts")
    client_name = data.get("client_name")
    if not service_id or slot_ts is None or not client_name:
        await state.clear()
        await edit_or_send(callback, t(lang, "session_expired"))
        await callback.message.answer(t(lang, "main_menu"), reply_markup=main_menu(is_admin, lang))
        return

    slot = slot_from_timestamp(slot_ts)
    await state.update_data(booking_confirm_in_progress=True)
    try:
        await callback.message.edit_text(t(lang, "booking_creating"), reply_markup=None)
    except TelegramBadRequest:
        pass

    try:
        t_db = 0.0
        t0 = time.perf_counter()
        async with async_session_factory() as session:
            booking_service = BookingService(session)
            auto_confirm = (await SettingsRepository(session).get("auto_confirm", "false")) == "true"
            booking = await booking_service.create_booking(
                telegram_id=callback.from_user.id,
                service_id=service_id,
                start_at=slot,
                client_name=client_name,
                client_phone=data.get("client_phone"),
                auto_confirm=auto_confirm,
                location_text=data.get("location_text"),
                client_comment=data.get("client_comment"),
                service_location_id=data.get("service_location_id"),
                service_location_title=data.get("service_location_title"),
                service_location_address=data.get("service_location_address"),
            )
            service = await ServiceRepository(session).get_by_id(booking.service_id)
        t_db = time.perf_counter() - t0
    except SlotUnavailableError:
        await edit_or_send(callback, t(lang, "slot_unavailable"))
        await state.clear()
        await callback.message.answer(t(lang, "main_menu"), reply_markup=main_menu(is_admin, lang))
        return
    except ValueError:
        await edit_or_send(callback, t(lang, "slot_unavailable"))
        await state.clear()
        await callback.message.answer(t(lang, "main_menu"), reply_markup=main_menu(is_admin, lang))
        return
    except Exception:
        logger.exception("Booking confirmation failed for user %s", callback.from_user.id)
        await edit_or_send(callback, t(lang, "error_generic"))
        await state.clear()
        await callback.message.answer(t(lang, "main_menu"), reply_markup=main_menu(is_admin, lang))
        return

    if booking.status.value == "confirmed":
        msg = t(lang, "booking_confirmed")
    else:
        msg = t(lang, "booking_created_pending")
    t0 = time.perf_counter()
    await edit_or_send(
        callback,
        f"{msg}\n\n{format_booking(booking, service, lang, show_location_comment=True)}",
        parse_mode="HTML",
    )
    t_ui = time.perf_counter() - t0
    t0 = time.perf_counter()
    await _notify_admins_new_booking(callback.bot, booking, service, lang)
    t_notify = time.perf_counter() - t0
    log_action_timing(
        "booking confirm",
        booking_id=booking.id,
        db=t_db,
        ui=t_ui,
        notify=t_notify,
        total=t_db + t_ui + t_notify,
    )
    await state.clear()
    await callback.message.answer(t(lang, "main_menu"), reply_markup=main_menu(is_admin, lang))


async def _booking_service_names(
    session,
    bookings: list,
    lang: str,
) -> dict[int, str]:
    names: dict[int, str] = {}
    repo = ServiceRepository(session)
    fallback = t(lang, "client_booking_service_fallback")
    for booking in bookings:
        if booking.service_id in names:
            continue
        service = await repo.get_by_id(booking.service_id)
        names[booking.service_id] = service.name if service and service.name else fallback
    return names


@router.message(F.text.in_(MY_BOOKINGS_TEXTS))
async def my_bookings(message: Message, lang: str) -> None:
    async with async_session_factory() as session:
        client = await ClientRepository(session).get_by_telegram_id(message.from_user.id)
        if not client:
            await message.answer(t(lang, "no_bookings_yet"))
            return
        bookings = await BookingRepository(session).list_for_client(client.id)
        service_names = await _booking_service_names(session, bookings, lang)
    if not bookings:
        await message.answer(t(lang, "my_bookings_empty"))
        return
    await message.answer(
        t(lang, "my_bookings_title"),
        reply_markup=bookings_kb(bookings, lang, service_names),
    )


@router.callback_query(F.data == "my_bookings")
async def my_bookings_cb(callback: CallbackQuery, lang: str) -> None:
    await safe_callback_answer(callback)
    async with async_session_factory() as session:
        client = await ClientRepository(session).get_by_telegram_id(callback.from_user.id)
        bookings = await BookingRepository(session).list_for_client(client.id) if client else []
        service_names = await _booking_service_names(session, bookings, lang) if bookings else {}
    if not bookings:
        await edit_or_send(callback, t(lang, "my_bookings_empty"))
        return
    await edit_or_send(
        callback,
        t(lang, "my_bookings_title"),
        reply_markup=bookings_kb(bookings, lang, service_names),
    )
