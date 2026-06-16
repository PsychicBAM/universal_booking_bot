import logging
from datetime import date as date_cls, timedelta

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.i18n import t
from app.bot.keyboards import SKIP_TEXTS, cancel_kb, main_menu, skip_cancel_kb
from app.bot.keyboards.booking_edit_kb import (
    client_booking_detail_kb,
    edit_location_kb,
    reschedule_confirm_kb,
    reschedule_dates_kb,
    reschedule_times_kb,
)
from app.bot.states import ClientBookingEditStates
from app.bot.utils.callbacks import safe_callback_answer
from app.bot.utils.telegram_ui import edit_or_send
from app.config import get_settings
from app.database.session import async_session_factory
from app.models import Booking, BookingStatus, Service
from app.repositories import (
    BookingRepository,
    ClientRepository,
    ServiceLocationRepository,
    ServiceRepository,
    UnavailableRepository,
    WorkingHoursRepository,
    WorkingBreakRepository,
)
from app.services.availability_service import AvailabilityService
from app.services.booking_notification_service import notify_admins_client_cancelled
from app.services.booking_service import BookingService
from app.services.exceptions import SlotUnavailableError
from app.services.calendar_service import CalendarService
from app.services.language_service import get_user_language
from app.utils.datetime_utils import now_local, slot_from_timestamp, to_local_naive
from app.utils.formatting import format_client_booking_detail, format_date, format_datetime

router = Router()
logger = logging.getLogger(__name__)


def _availability_service(session):
    return AvailabilityService(
        WorkingHoursRepository(session),
        UnavailableRepository(session),
        BookingRepository(session),
        CalendarService(session),
        WorkingBreakRepository(session),
    )


def _is_editable_status(booking: Booking) -> bool:
    return booking.status in (BookingStatus.PENDING, BookingStatus.CONFIRMED)


async def _notify_admins_booking_changed(
    bot: Bot,
    booking: Booking,
    service: Service | None,
    old_value: str,
    new_value: str,
    lang: str,
) -> None:
    settings = get_settings()
    service_name = service.name if service else f"#{booking.service_id}"
    for admin_id in settings.admin_ids:
        admin_lang = await get_user_language(admin_id)
        try:
            await bot.send_message(
                admin_id,
                t(
                    admin_lang,
                    "booking_changed_admin",
                    service=service_name,
                    client_name=booking.client_name,
                    phone=booking.client_phone or t(admin_lang, "phone_not_provided"),
                    old_value=old_value,
                    new_value=new_value,
                ),
            )
        except Exception:
            logger.exception("Failed to notify admin %s about booking change", admin_id)


def _detail_options(
    booking: Booking,
    service: Service | None,
    active_locations_count: int,
) -> dict:
    settings = get_settings()
    editable = _is_editable_status(booking)
    can_act = editable and to_local_naive(booking.start_at) - now_local() > timedelta(
        hours=settings.cancel_booking_hours_before
    )
    can_reschedule = editable and (
        to_local_naive(booking.start_at) - now_local()
        > timedelta(hours=settings.effective_reschedule_hours_before())
    )
    requires_location = bool(service and service.requires_location)
    asks_comment = bool(service and service.ask_client_comment)
    return {
        "can_reschedule": can_reschedule,
        "can_cancel": can_act,
        "can_change_location": editable and active_locations_count > 0,
        "can_change_address": editable and requires_location,
        "can_change_comment": editable and asks_comment,
    }


async def show_client_booking_detail(
    event: Message | CallbackQuery,
    booking_id: int,
    telegram_id: int,
    lang: str,
    *,
    bot: Bot | None = None,
) -> bool:
    async with async_session_factory() as session:
        booking = await BookingRepository(session).get_by_id(booking_id)
        client = await ClientRepository(session).get_by_telegram_id(telegram_id)
        if not booking or not client or booking.client_id != client.id:
            if isinstance(event, CallbackQuery):
                await safe_callback_answer(event, t(lang, "access_denied"), show_alert=True)
            else:
                await event.answer(t(lang, "access_denied"))
            return False
        service = await ServiceRepository(session).get_by_id(booking.service_id)
        locations = await ServiceLocationRepository(session).list_active_for_service(booking.service_id)
        opts = _detail_options(booking, service, len(locations))

    text = format_client_booking_detail(booking, service, lang)
    keyboard = client_booking_detail_kb(booking_id, lang, **opts)
    if isinstance(event, CallbackQuery):
        await edit_or_send(event, text, reply_markup=keyboard)
        await safe_callback_answer(event)
    else:
        await event.answer(text, reply_markup=keyboard)
    return True


@router.callback_query(F.data.startswith("cancel_booking:"))
async def legacy_cancel_booking(callback: CallbackQuery, is_admin: bool, lang: str, state: FSMContext) -> None:
    booking_id = int(callback.data.split(":", 1)[1])
    booking = None
    service = None
    try:
        async with async_session_factory() as session:
            booking = await BookingService(session).cancel_booking(
                booking_id, telegram_id=callback.from_user.id
            )
            service = await ServiceRepository(session).get_by_id(booking.service_id)
    except ValueError as exc:
        msg = t(lang, "cancel_too_late") if "Too late" in str(exc) else t(lang, "access_denied")
        await safe_callback_answer(callback, msg, show_alert=True)
        return
    except Exception:
        logger.exception("Client cancel failed for booking %s", booking_id)
        await safe_callback_answer(callback, t(lang, "error_generic"), show_alert=True)
        return
    if booking:
        await notify_admins_client_cancelled(callback.bot, booking, service, lang=lang)
    await state.clear()
    await edit_or_send(callback, t(lang, "booking_cancelled"))
    await callback.message.answer(t(lang, "main_menu"), reply_markup=main_menu(is_admin, lang))
    await safe_callback_answer(callback)


@router.callback_query(F.data.startswith("my:view:"))
async def my_booking_view(callback: CallbackQuery, lang: str, state: FSMContext) -> None:
    await state.clear()
    booking_id = int(callback.data.split(":")[-1])
    await show_client_booking_detail(callback, booking_id, callback.from_user.id, lang)


@router.callback_query(F.data.startswith("mybooking:"))
async def legacy_my_booking_view(callback: CallbackQuery, lang: str, state: FSMContext) -> None:
    await state.clear()
    booking_id = int(callback.data.split(":", 1)[1])
    await show_client_booking_detail(callback, booking_id, callback.from_user.id, lang)


@router.callback_query(F.data.startswith("my:cancel:"))
async def my_cancel_booking(callback: CallbackQuery, is_admin: bool, lang: str, state: FSMContext) -> None:
    booking_id = int(callback.data.split(":")[-1])
    booking = None
    service = None
    try:
        async with async_session_factory() as session:
            booking = await BookingService(session).cancel_booking(
                booking_id, telegram_id=callback.from_user.id
            )
            service = await ServiceRepository(session).get_by_id(booking.service_id)
    except ValueError as exc:
        msg = t(lang, "cancel_too_late") if "Too late" in str(exc) else t(lang, "access_denied")
        await safe_callback_answer(callback, msg, show_alert=True)
        return
    except Exception:
        logger.exception("Client cancel failed for booking %s", booking_id)
        await safe_callback_answer(callback, t(lang, "error_generic"), show_alert=True)
        return
    if booking:
        await notify_admins_client_cancelled(callback.bot, booking, service, lang=lang)
    await state.clear()
    await edit_or_send(callback, t(lang, "booking_cancelled"))
    await callback.message.answer(t(lang, "main_menu"), reply_markup=main_menu(is_admin, lang))
    await safe_callback_answer(callback)


async def begin_client_reschedule(
    callback: CallbackQuery,
    booking_id: int,
    lang: str,
    state: FSMContext,
) -> bool:
    settings = get_settings()
    async with async_session_factory() as session:
        booking = await BookingRepository(session).get_by_id(booking_id)
        client = await ClientRepository(session).get_by_telegram_id(callback.from_user.id)
        if not booking or not client or booking.client_id != client.id:
            await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
            return False
        if not _is_editable_status(booking):
            await safe_callback_answer(callback, t(lang, "booking_not_editable"), show_alert=True)
            return False
        if to_local_naive(booking.start_at) - now_local() <= timedelta(
            hours=settings.effective_reschedule_hours_before()
        ):
            await safe_callback_answer(callback, t(lang, "reschedule_too_late"), show_alert=True)
            return False
        service_repo = ServiceRepository(session)
        availability = _availability_service(session)
        dates = await availability.get_available_dates(
            booking.service_id, service_repo, exclude_booking_id=booking.id
        )

    if not dates:
        await safe_callback_answer(callback, t(lang, "no_dates"), show_alert=True)
        return False

    await state.update_data(
        flow_origin="client_edit",
        edit_booking_id=booking_id,
        reschedule_old_ts=int(to_local_naive(booking.start_at).timestamp()),
    )
    await state.set_state(ClientBookingEditStates.reschedule_choosing_date)
    await edit_or_send(
        callback,
        t(lang, "choose_date"),
        reply_markup=reschedule_dates_kb(booking_id, dates, lang),
    )
    await safe_callback_answer(callback)
    return True


@router.callback_query(F.data.regexp(r"^my:res:\d+$"))
async def start_reschedule(callback: CallbackQuery, lang: str, state: FSMContext) -> None:
    booking_id = int(callback.data.split(":")[-1])
    await begin_client_reschedule(callback, booking_id, lang, state)


@router.callback_query(F.data.startswith("my:res:date:"))
async def reschedule_choose_date(callback: CallbackQuery, lang: str, state: FSMContext) -> None:
    parts = callback.data.split(":")
    booking_id = int(parts[3])
    target_date = date_cls.fromisoformat(parts[4])
    data = await state.get_data()
    if data.get("edit_booking_id") != booking_id:
        await safe_callback_answer(callback, t(lang, "session_expired"), show_alert=True)
        await state.clear()
        return

    async with async_session_factory() as session:
        booking = await BookingRepository(session).get_by_id(booking_id)
        client = await ClientRepository(session).get_by_telegram_id(callback.from_user.id)
        if not booking or not client or booking.client_id != client.id:
            await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
            return
        service_repo = ServiceRepository(session)
        availability = _availability_service(session)
        slots = await availability.get_available_slots(
            booking.service_id, target_date, service_repo, exclude_booking_id=booking.id
        )

    if not slots:
        await safe_callback_answer(callback, t(lang, "no_slots"), show_alert=True)
        return

    await state.update_data(reschedule_target_date=target_date.isoformat())
    await state.set_state(ClientBookingEditStates.reschedule_choosing_time)
    await edit_or_send(
        callback,
        f"{format_date(target_date)}\n{t(lang, 'choose_time')}",
        reply_markup=reschedule_times_kb(booking_id, slots, lang),
    )
    await safe_callback_answer(callback)


@router.callback_query(F.data.startswith("my:res:time:"))
async def reschedule_choose_time(callback: CallbackQuery, lang: str, state: FSMContext) -> None:
    parts = callback.data.split(":")
    booking_id = int(parts[3])
    slot_ts = int(parts[4])
    data = await state.get_data()
    if data.get("edit_booking_id") != booking_id:
        await safe_callback_answer(callback, t(lang, "session_expired"), show_alert=True)
        await state.clear()
        return

    slot = slot_from_timestamp(slot_ts)
    old_ts = data.get("reschedule_old_ts")
    old_dt = format_datetime(slot_from_timestamp(old_ts)) if old_ts else "—"
    await state.update_data(reschedule_new_ts=slot_ts)
    await state.set_state(ClientBookingEditStates.reschedule_confirm)
    await edit_or_send(
        callback,
        t(lang, "confirm_reschedule", old_datetime=old_dt, new_datetime=format_datetime(slot)),
        reply_markup=reschedule_confirm_kb(booking_id, lang),
    )
    await safe_callback_answer(callback)


@router.callback_query(F.data.startswith("my:res:confirm:"))
async def reschedule_confirm(callback: CallbackQuery, bot: Bot, lang: str, state: FSMContext) -> None:
    booking_id = int(callback.data.split(":")[-1])
    data = await state.get_data()
    if data.get("reschedule_confirm_in_progress"):
        logger.info("Duplicate reschedule confirm ignored booking_id=%s user=%s", booking_id, callback.from_user.id)
        await safe_callback_answer(callback, t(lang, "booking_request_in_progress"), show_alert=True)
        return

    if data.get("edit_booking_id") != booking_id or not data.get("reschedule_new_ts"):
        await safe_callback_answer(callback, t(lang, "session_expired"), show_alert=True)
        await state.clear()
        return

    await safe_callback_answer(callback)
    await state.update_data(reschedule_confirm_in_progress=True)
    try:
        await callback.message.edit_text(t(lang, "booking_creating"), reply_markup=None)
    except Exception:
        pass

    old_ts = data.get("reschedule_old_ts")
    old_dt = format_datetime(slot_from_timestamp(old_ts)) if old_ts else "—"
    new_slot = slot_from_timestamp(data["reschedule_new_ts"])
    new_dt = format_datetime(new_slot)

    try:
        async with async_session_factory() as session:
            booking_service = BookingService(session)
            booking = await booking_service.reschedule_booking(
                booking_id, callback.from_user.id, new_slot
            )
            service = await ServiceRepository(session).get_by_id(booking.service_id)
    except SlotUnavailableError:
        await state.update_data(reschedule_confirm_in_progress=False)
        await edit_or_send(callback, t(lang, "slot_unavailable"))
        return
    except ValueError as exc:
        err = str(exc)
        await state.update_data(reschedule_confirm_in_progress=False)
        if "Too late" in err:
            msg = t(lang, "reschedule_too_late")
        elif "Not allowed" in err or "Not editable" in err:
            msg = t(lang, "access_denied")
        else:
            msg = t(lang, "error_generic")
        await edit_or_send(callback, msg)
        return
    except Exception:
        logger.exception("Reschedule failed booking_id=%s", booking_id)
        await state.update_data(reschedule_confirm_in_progress=False)
        await edit_or_send(callback, t(lang, "error_generic"))
        return

    await _notify_admins_booking_changed(bot, booking, service, old_dt, new_dt, lang)
    await state.clear()
    await edit_or_send(callback, t(lang, "booking_rescheduled"))
    await show_client_booking_detail(callback, booking_id, callback.from_user.id, lang)


@router.callback_query(F.data.regexp(r"^my:loc:\d+$"))
async def start_change_location(callback: CallbackQuery, lang: str, state: FSMContext) -> None:
    booking_id = int(callback.data.split(":")[-1])
    async with async_session_factory() as session:
        booking = await BookingRepository(session).get_by_id(booking_id)
        client = await ClientRepository(session).get_by_telegram_id(callback.from_user.id)
        if not booking or not client or booking.client_id != client.id:
            await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
            return
        if not _is_editable_status(booking):
            await safe_callback_answer(callback, t(lang, "booking_not_editable"), show_alert=True)
            return
        locations = await ServiceLocationRepository(session).list_active_for_service(booking.service_id)

    if not locations:
        await safe_callback_answer(callback, t(lang, "no_locations"), show_alert=True)
        return

    await state.update_data(flow_origin="client_edit", edit_booking_id=booking_id)
    await state.set_state(ClientBookingEditStates.changing_service_location)
    await edit_or_send(
        callback,
        t(lang, "choose_service_location"),
        reply_markup=edit_location_kb(booking_id, locations, lang),
    )
    await safe_callback_answer(callback)


@router.callback_query(F.data.startswith("my:loc:set:"))
async def change_location_set(callback: CallbackQuery, bot: Bot, lang: str, state: FSMContext) -> None:
    parts = callback.data.split(":")
    booking_id = int(parts[3])
    location_id = int(parts[4])

    old_value = t(lang, "not_provided")
    try:
        async with async_session_factory() as session:
            booking_before = await BookingRepository(session).get_by_id(booking_id)
            if booking_before and booking_before.service_location_title:
                old_value = booking_before.service_location_title
            booking_service = BookingService(session)
            booking = await booking_service.change_service_location(
                booking_id, callback.from_user.id, location_id
            )
            service = await ServiceRepository(session).get_by_id(booking.service_id)
            new_value = booking.service_location_title or t(lang, "not_provided")
    except ValueError:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    except Exception:
        logger.exception("Change location failed booking_id=%s", booking_id)
        await safe_callback_answer(callback, t(lang, "error_generic"), show_alert=True)
        return

    await _notify_admins_booking_changed(bot, booking, service, old_value, new_value, lang)
    await state.clear()
    await edit_or_send(callback, t(lang, "service_location_changed"))
    await show_client_booking_detail(callback, booking_id, callback.from_user.id, lang)


@router.callback_query(F.data.startswith("my:addr:"))
async def start_change_address(callback: CallbackQuery, lang: str, state: FSMContext) -> None:
    booking_id = int(callback.data.split(":")[-1])
    async with async_session_factory() as session:
        booking = await BookingRepository(session).get_by_id(booking_id)
        client = await ClientRepository(session).get_by_telegram_id(callback.from_user.id)
        service = await ServiceRepository(session).get_by_id(booking.service_id) if booking else None
        if not booking or not client or booking.client_id != client.id:
            await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
            return
        if not _is_editable_status(booking) or not service or not service.requires_location:
            await safe_callback_answer(callback, t(lang, "booking_not_editable"), show_alert=True)
            return

    await state.update_data(flow_origin="client_edit", edit_booking_id=booking_id)
    await state.set_state(ClientBookingEditStates.changing_client_address)
    await safe_callback_answer(callback)
    await callback.message.answer(t(lang, "enter_new_address"), reply_markup=cancel_kb(lang))


@router.message(ClientBookingEditStates.changing_client_address, F.text)
async def receive_new_address(message: Message, bot: Bot, lang: str, state: FSMContext) -> None:
    address = message.text.strip()
    if not address:
        await message.answer(t(lang, "enter_new_address"), reply_markup=cancel_kb(lang))
        return
    data = await state.get_data()
    booking_id = data.get("edit_booking_id")
    if not booking_id:
        await state.clear()
        return

    old_value = t(lang, "not_provided")
    try:
        async with async_session_factory() as session:
            booking_before = await BookingRepository(session).get_by_id(booking_id)
            if booking_before and booking_before.location_text:
                old_value = booking_before.location_text
            booking = await BookingService(session).change_client_address(
                booking_id, message.from_user.id, address
            )
            service = await ServiceRepository(session).get_by_id(booking.service_id)
            new_value = booking.location_text or t(lang, "not_provided")
    except ValueError:
        await message.answer(t(lang, "access_denied"))
        await state.clear()
        return
    except Exception:
        logger.exception("Change address failed booking_id=%s", booking_id)
        await message.answer(t(lang, "error_generic"))
        await state.clear()
        return

    await _notify_admins_booking_changed(bot, booking, service, old_value, new_value, lang)
    await state.clear()
    await message.answer(t(lang, "address_changed"))
    await show_client_booking_detail(message, booking_id, message.from_user.id, lang)


@router.callback_query(F.data.startswith("my:comment:"))
async def start_change_comment(callback: CallbackQuery, lang: str, state: FSMContext) -> None:
    booking_id = int(callback.data.split(":")[-1])
    async with async_session_factory() as session:
        booking = await BookingRepository(session).get_by_id(booking_id)
        client = await ClientRepository(session).get_by_telegram_id(callback.from_user.id)
        service = await ServiceRepository(session).get_by_id(booking.service_id) if booking else None
        if not booking or not client or booking.client_id != client.id:
            await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
            return
        if not _is_editable_status(booking) or not service or not service.ask_client_comment:
            await safe_callback_answer(callback, t(lang, "booking_not_editable"), show_alert=True)
            return

    await state.update_data(flow_origin="client_edit", edit_booking_id=booking_id)
    await state.set_state(ClientBookingEditStates.changing_comment)
    await safe_callback_answer(callback)
    await callback.message.answer(t(lang, "enter_new_comment"), reply_markup=skip_cancel_kb(lang))


@router.message(ClientBookingEditStates.changing_comment, F.text.in_(SKIP_TEXTS))
async def clear_comment(message: Message, bot: Bot, lang: str, state: FSMContext) -> None:
    await _save_comment(message, bot, lang, state, None)


@router.message(ClientBookingEditStates.changing_comment, F.text)
async def receive_new_comment(message: Message, bot: Bot, lang: str, state: FSMContext) -> None:
    await _save_comment(message, bot, lang, state, message.text.strip())


async def _save_comment(
    message: Message, bot: Bot, lang: str, state: FSMContext, comment: str | None
) -> None:
    data = await state.get_data()
    booking_id = data.get("edit_booking_id")
    if not booking_id:
        await state.clear()
        return

    old_value = t(lang, "not_provided")
    try:
        async with async_session_factory() as session:
            booking_before = await BookingRepository(session).get_by_id(booking_id)
            if booking_before and booking_before.client_comment:
                old_value = booking_before.client_comment
            booking = await BookingService(session).change_client_comment(
                booking_id, message.from_user.id, comment
            )
            service = await ServiceRepository(session).get_by_id(booking.service_id)
            new_value = booking.client_comment or t(lang, "not_provided")
    except ValueError:
        await message.answer(t(lang, "access_denied"))
        await state.clear()
        return
    except Exception:
        logger.exception("Change comment failed booking_id=%s", booking_id)
        await message.answer(t(lang, "error_generic"))
        await state.clear()
        return

    await _notify_admins_booking_changed(bot, booking, service, old_value, new_value, lang)
    await state.clear()
    await message.answer(t(lang, "comment_changed"))
    await show_client_booking_detail(message, booking_id, message.from_user.id, lang)
