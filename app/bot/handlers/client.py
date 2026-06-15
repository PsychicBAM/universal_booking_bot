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
from app.bot.utils.service_helpers import client_service_unavailable_key, is_service_bookable
from app.bot.utils.telegram_ui import edit_or_send
from app.bot.keyboards import (
    BOOK_APPOINTMENT_TEXTS,
    MY_BOOKINGS_TEXTS,
    SKIP_TEXTS,
    admin_menu,
    bookings_kb,
    cancel_kb,
    confirm_kb,
    dates_kb,
    main_menu,
    services_kb,
    skip_cancel_kb,
    times_kb,
)
from app.bot.states import BookingStates
from app.config import get_settings
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

router = Router()
logger = logging.getLogger(__name__)


def _parse_service_id(callback_data: str) -> int:
    return int(callback_data.rsplit(":", 1)[1])


def _booking_summary(data: dict, lang: str) -> str:
    slot = slot_from_timestamp(data["slot_ts"])
    service_name = escape(str(data.get("service_name") or ""))
    client_name = escape(str(data.get("client_name") or ""))
    phone = escape(str(data.get("client_phone") or "")) or t(lang, "not_provided")
    requires_location = bool(data.get("requires_location"))
    ask_client_comment = bool(data.get("ask_client_comment"))
    lines = [
        f"{t(lang, 'confirm_booking')}\n",
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
        reply_markup=confirm_kb(lang),
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
    logger.info(
        "book timing: answer=%.2fs service=%.2fs availability=%.2fs send=%.2fs total=%.2fs dates=%s",
        t_answer,
        t_service,
        t_availability,
        t_send,
        time.perf_counter() - t_total,
        len(dates),
    )


async def _notify_admins_new_booking(bot, booking, service, lang: str) -> None:
    settings = get_settings()
    for admin_id in settings.admin_ids:
        admin_lang = await get_user_language(admin_id)
        try:
            await bot.send_message(
                admin_id,
                f"{t(admin_lang, 'new_booking_admin')}\n\n{format_booking(booking, service, admin_lang, admin_view=True)}",
            )
        except Exception:
            pass


@router.message(F.text.in_(BOOK_APPOINTMENT_TEXTS))
async def start_booking(message: Message, state: FSMContext, lang: str) -> None:
    async with async_session_factory() as session:
        services = await ServiceRepository(session).list_client_services()
    if not services:
        await message.answer(t(lang, "no_services"))
        return
    await state.update_data(flow_origin="client")
    await state.set_state(BookingStates.choosing_service)
    await message.answer(t(lang, "choose_service"), reply_markup=services_kb(services, lang))


@router.callback_query(BookingStates.choosing_service, F.data.regexp(r"^svc:\d+$"))
async def view_service(callback: CallbackQuery, state: FSMContext, lang: str, bot: Bot) -> None:
    service_id = int(callback.data.split(":", 1)[1])
    async with async_session_factory() as session:
        service = await ServiceRepository(session).get_by_id(service_id)
        if not is_service_bookable(service):
            await safe_callback_answer(callback, t(lang, client_service_unavailable_key(service)), show_alert=True)
            return
        media_items = await ServiceMediaRepository(session).list_for_service(service_id)
        photos = await ServiceMediaRepository(session).count_photos(service_id)
        videos = await ServiceMediaRepository(session).count_videos(service_id)

    await safe_callback_answer(callback)
    await state.update_data(flow_origin="client")
    await state.set_state(BookingStates.choosing_service)
    chat_id = callback.message.chat.id
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        await callback.message.edit_reply_markup(reply_markup=None)

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


@router.callback_query(BookingStates.choosing_service_location, F.data == "cb:svc_back")
@router.callback_query(BookingStates.choosing_service, F.data == "cb:svc_back")
async def back_to_services(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    async with async_session_factory() as session:
        services = await ServiceRepository(session).list_client_services()
    if not services:
        await edit_or_send(callback, t(lang, "no_services"))
        await state.clear()
        await safe_callback_answer(callback)
        return
    await state.set_state(BookingStates.choosing_service)
    await state.update_data(
        service_location_id=None,
        service_location_title=None,
        service_location_address=None,
    )
    await edit_or_send(callback, t(lang, "choose_service"), reply_markup=services_kb(services, lang))
    await safe_callback_answer(callback)


@router.callback_query(BookingStates.choosing_service, F.data.startswith("cb:photos:"))
async def view_service_photos(callback: CallbackQuery, lang: str, bot: Bot) -> None:
    service_id = _parse_service_id(callback.data)
    async with async_session_factory() as session:
        service = await ServiceRepository(session).get_by_id(service_id)
        if not is_service_bookable(service):
            await safe_callback_answer(callback, t(lang, client_service_unavailable_key(service)), show_alert=True)
            return
        if not service.show_media_to_clients:
            await safe_callback_answer(callback, t(lang, "not_found"), show_alert=True)
            return
        media_items = await ServiceMediaRepository(session).list_for_service(service_id)
        photos = await ServiceMediaRepository(session).count_photos(service_id)
        videos = await ServiceMediaRepository(session).count_videos(service_id)

    await safe_callback_answer(callback)
    chat_id = callback.message.chat.id
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        await callback.message.edit_reply_markup(reply_markup=None)

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


@router.callback_query(BookingStates.choosing_service, F.data.startswith("cb:video:"))
async def view_service_video(callback: CallbackQuery, lang: str, bot: Bot) -> None:
    service_id = _parse_service_id(callback.data)
    async with async_session_factory() as session:
        service = await ServiceRepository(session).get_by_id(service_id)
        if not is_service_bookable(service):
            await safe_callback_answer(callback, t(lang, client_service_unavailable_key(service)), show_alert=True)
            return
        if not service.show_media_to_clients:
            await safe_callback_answer(callback, t(lang, "not_found"), show_alert=True)
            return
        media_items = await ServiceMediaRepository(session).list_for_service(service_id)
        photos = await ServiceMediaRepository(session).count_photos(service_id)
        videos = await ServiceMediaRepository(session).count_videos(service_id)

    await safe_callback_answer(callback)
    chat_id = callback.message.chat.id
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        await callback.message.edit_reply_markup(reply_markup=None)

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
        if not is_service_bookable(service):
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


@router.callback_query(BookingStates.choosing_date, F.data.startswith("date:"))
async def choose_date(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    from datetime import date as date_cls

    await safe_callback_answer(callback)
    target_date = date_cls.fromisoformat(callback.data.split(":", 1)[1])
    data = await state.get_data()
    service_id = data["service_id"]

    async with async_session_factory() as session:
        availability = AvailabilityService(
            WorkingHoursRepository(session),
            UnavailableRepository(session),
            BookingRepository(session),
            CalendarService(session),
        )
        slots = await availability.get_available_slots(service_id, target_date, ServiceRepository(session))

    if not slots:
        await callback.message.answer(t(lang, "no_slots"))
        return

    await state.update_data(target_date=target_date.isoformat())
    await state.set_state(BookingStates.choosing_time)
    await edit_or_send(
        callback,
        f"{format_date(target_date)}\n{t(lang, 'choose_time')}",
        reply_markup=times_kb(slots, lang),
    )


@router.callback_query(BookingStates.choosing_time, F.data.startswith("time:"))
async def choose_time(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await safe_callback_answer(callback)
    slot_ts = int(callback.data.split(":", 1)[1])
    slot = slot_from_timestamp(slot_ts)
    await state.update_data(slot_ts=slot_ts, flow_origin="client")
    await state.set_state(BookingStates.entering_name)
    await edit_or_send(callback, t(lang, "selected", dt=format_datetime(slot)))
    await callback.message.answer(t(lang, "enter_name"), reply_markup=cancel_kb(lang))


@router.message(BookingStates.entering_name, F.text)
async def enter_name(message: Message, state: FSMContext, lang: str) -> None:
    name = message.text.strip()
    if not name:
        await message.answer(t(lang, "enter_name"), reply_markup=cancel_kb(lang))
        return
    await state.update_data(client_name=name, flow_origin="client")
    await state.set_state(BookingStates.entering_phone)
    await message.answer(t(lang, "enter_phone"), reply_markup=cancel_kb(lang))


@router.message(BookingStates.entering_phone, F.text)
async def enter_phone(message: Message, state: FSMContext, lang: str) -> None:
    phone = message.text.strip()
    if not phone:
        await message.answer(t(lang, "enter_phone"), reply_markup=cancel_kb(lang))
        return
    data = await state.get_data()
    await state.update_data(client_phone=phone, flow_origin="client")
    if data.get("requires_location"):
        await state.set_state(BookingStates.entering_location)
        await message.answer(t(lang, "enter_location"), reply_markup=cancel_kb(lang))
        return
    if data.get("ask_client_comment"):
        await _prompt_comment(message, state, lang)
        return
    await _show_confirmation(message, state, lang)


@router.message(BookingStates.entering_location, F.text)
async def enter_location(message: Message, state: FSMContext, lang: str) -> None:
    location = message.text.strip()
    if not location:
        await message.answer(t(lang, "enter_location"), reply_markup=cancel_kb(lang))
        return
    await state.update_data(location_text=location, flow_origin="client")
    data = await state.get_data()
    if data.get("ask_client_comment"):
        await _prompt_comment(message, state, lang)
        return
    await _show_confirmation(message, state, lang)


@router.message(BookingStates.entering_comment, F.text.in_(SKIP_TEXTS))
async def skip_comment(message: Message, state: FSMContext, lang: str) -> None:
    await state.update_data(client_comment=None, flow_origin="client")
    await _show_confirmation(message, state, lang)


@router.message(BookingStates.entering_comment, F.text)
async def enter_comment(message: Message, state: FSMContext, lang: str) -> None:
    await state.update_data(client_comment=message.text.strip(), flow_origin="client")
    await _show_confirmation(message, state, lang)


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
    await edit_or_send(
        callback,
        f"{msg}\n\n{format_booking(booking, service, lang, show_location_comment=True)}",
    )
    await _notify_admins_new_booking(callback.bot, booking, service, lang)
    await state.clear()
    await callback.message.answer(t(lang, "main_menu"), reply_markup=main_menu(is_admin, lang))


@router.message(F.text.in_(MY_BOOKINGS_TEXTS))
async def my_bookings(message: Message, lang: str) -> None:
    async with async_session_factory() as session:
        client = await ClientRepository(session).get_by_telegram_id(message.from_user.id)
        if not client:
            await message.answer(t(lang, "no_bookings_yet"))
            return
        bookings = await BookingRepository(session).list_for_client(client.id)
    if not bookings:
        await message.answer(t(lang, "no_bookings"))
        return
    await message.answer(t(lang, "your_bookings"), reply_markup=bookings_kb(bookings))


@router.callback_query(F.data == "my_bookings")
async def my_bookings_cb(callback: CallbackQuery, lang: str) -> None:
    async with async_session_factory() as session:
        client = await ClientRepository(session).get_by_telegram_id(callback.from_user.id)
        bookings = await BookingRepository(session).list_for_client(client.id) if client else []
    await edit_or_send(callback, t(lang, "your_bookings"), reply_markup=bookings_kb(bookings))
    await safe_callback_answer(callback)
