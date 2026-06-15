import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.handlers.booking_edit import begin_client_reschedule
from app.bot.i18n import t
from app.bot.keyboards import main_menu
from app.bot.keyboards.attendance_kb import attendance_action_kb, attendance_action_prompt_text
from app.bot.states import AttendanceStates
from app.bot.utils.callbacks import safe_callback_answer
from app.bot.utils.telegram_ui import edit_or_send
from app.database.session import async_session_factory
from app.repositories import ServiceRepository
from app.bot.utils.attendance_helpers import (
    ATTENDANCE_CANNOT_ATTEND,
    ATTENDANCE_CONFIRMED,
    ATTENDANCE_REASON_PROVIDED,
    MAX_ATTENDANCE_REASON_LEN,
)
from app.services.attendance_service import (
    format_attendance_reminder_text,
    get_client_booking,
    mark_attendance_response,
    notify_admins_attendance,
)
from app.services.booking_service import BookingService
from app.services.confirmation_text_service import load_confirmation_text_config, resolve_confirmation_text
from app.utils.formatting import format_datetime
from app.utils.datetime_utils import to_local_naive

router = Router()
logger = logging.getLogger(__name__)


def _booking_id_from_callback(data: str) -> int:
    return int(data.rsplit(":", 1)[1])


async def _service_name(session, booking) -> str:
    service = await ServiceRepository(session).get_by_id(booking.service_id)
    return service.name if service else f"#{booking.service_id}"


@router.callback_query(F.data.regexp(r"^att:yes:\d+$"))
async def attendance_yes(callback: CallbackQuery, lang: str, state: FSMContext) -> None:
    await state.clear()
    booking_id = _booking_id_from_callback(callback.data)
    async with async_session_factory() as session:
        pair = await get_client_booking(session, booking_id, callback.from_user.id)
        if not pair:
            await safe_callback_answer(callback, t(lang, "attendance_unavailable"), show_alert=True)
            return
        booking, _client = pair
        text_config = await load_confirmation_text_config(session)
        mark_attendance_response(booking, ATTENDANCE_CONFIRMED)
        service_name = await _service_name(session, booking)
        await session.commit()
    await notify_admins_attendance(
        callback.bot,
        booking,
        service_name,
        "yes_admin",
        text_config,
    )
    await safe_callback_answer(callback)
    date_time = format_datetime(to_local_naive(booking.start_at))
    text = format_attendance_reminder_text(
        booking, service_name, date_time, lang, text_config, include_prompt=False
    )
    text += f"\n\n{resolve_confirmation_text(text_config, lang, 'yes_response')}"
    await edit_or_send(callback, text, reply_markup=None)


@router.callback_query(F.data.regexp(r"^att:no:\d+$"))
async def attendance_no(callback: CallbackQuery, lang: str, state: FSMContext) -> None:
    await state.clear()
    booking_id = _booking_id_from_callback(callback.data)
    async with async_session_factory() as session:
        pair = await get_client_booking(session, booking_id, callback.from_user.id)
        if not pair:
            await safe_callback_answer(callback, t(lang, "attendance_unavailable"), show_alert=True)
            return
        booking, _client = pair
        text_config = await load_confirmation_text_config(session)
        mark_attendance_response(booking, ATTENDANCE_CANNOT_ATTEND)
        service_name = await _service_name(session, booking)
        await session.commit()
    await notify_admins_attendance(
        callback.bot,
        booking,
        service_name,
        "no_admin",
        text_config,
    )
    await safe_callback_answer(callback)
    await edit_or_send(
        callback,
        attendance_action_prompt_text(lang, text_config),
        reply_markup=attendance_action_kb(booking_id, lang),
    )


@router.callback_query(F.data.regexp(r"^att:keep:\d+$"))
async def attendance_keep(callback: CallbackQuery, lang: str, state: FSMContext) -> None:
    await state.clear()
    booking_id = _booking_id_from_callback(callback.data)
    async with async_session_factory() as session:
        pair = await get_client_booking(session, booking_id, callback.from_user.id)
        if not pair:
            await safe_callback_answer(callback, t(lang, "attendance_unavailable"), show_alert=True)
            return
    await safe_callback_answer(callback)
    await edit_or_send(callback, t(lang, "attendance_keep_saved"), reply_markup=None)


@router.callback_query(F.data.regexp(r"^att:reason:\d+$"))
async def attendance_reason_start(callback: CallbackQuery, lang: str, state: FSMContext) -> None:
    booking_id = _booking_id_from_callback(callback.data)
    async with async_session_factory() as session:
        pair = await get_client_booking(session, booking_id, callback.from_user.id)
        if not pair:
            await safe_callback_answer(callback, t(lang, "attendance_unavailable"), show_alert=True)
            return
    await state.update_data(attendance_booking_id=booking_id, flow_origin="client")
    await state.set_state(AttendanceStates.entering_reason)
    await safe_callback_answer(callback)
    await callback.message.answer(t(lang, "attendance_reason_prompt"))


@router.message(AttendanceStates.entering_reason, F.text)
async def attendance_reason_save(message: Message, state: FSMContext, lang: str, is_admin: bool) -> None:
    text = message.text.strip()
    if len(text) > MAX_ATTENDANCE_REASON_LEN:
        await message.answer(t(lang, "attendance_reason_too_long", max_len=str(MAX_ATTENDANCE_REASON_LEN)))
        return
    data = await state.get_data()
    booking_id = data.get("attendance_booking_id")
    if not booking_id:
        await state.clear()
        await message.answer(t(lang, "attendance_unavailable"))
        return
    async with async_session_factory() as session:
        pair = await get_client_booking(session, booking_id, message.from_user.id)
        if not pair:
            await state.clear()
            await message.answer(t(lang, "attendance_unavailable"))
            return
        booking, _client = pair
        text_config = await load_confirmation_text_config(session)
        mark_attendance_response(booking, ATTENDANCE_REASON_PROVIDED, reason=text)
        service_name = await _service_name(session, booking)
        await session.commit()
    await notify_admins_attendance(
        message.bot,
        booking,
        service_name,
        "no_admin",
        text_config,
        reason=text,
    )
    await state.clear()
    await message.answer(t(lang, "attendance_reason_saved"))
    await message.answer(
        attendance_action_prompt_text(lang, text_config),
        reply_markup=attendance_action_kb(booking_id, lang),
    )


@router.callback_query(F.data.regexp(r"^att:cancel:\d+$"))
async def attendance_cancel(callback: CallbackQuery, is_admin: bool, lang: str, state: FSMContext) -> None:
    booking_id = _booking_id_from_callback(callback.data)
    try:
        async with async_session_factory() as session:
            pair = await get_client_booking(session, booking_id, callback.from_user.id)
            if not pair:
                await safe_callback_answer(callback, t(lang, "attendance_unavailable"), show_alert=True)
                return
            await BookingService(session).cancel_booking(
                booking_id, telegram_id=callback.from_user.id
            )
    except ValueError as exc:
        msg = t(lang, "cancel_too_late") if "Too late" in str(exc) else t(lang, "attendance_unavailable")
        await safe_callback_answer(callback, msg, show_alert=True)
        return
    except Exception:
        logger.exception("Attendance cancel failed for booking %s", booking_id)
        await safe_callback_answer(callback, t(lang, "error_generic"), show_alert=True)
        return
    await state.clear()
    await edit_or_send(callback, t(lang, "booking_cancelled"), reply_markup=None)
    await callback.message.answer(t(lang, "main_menu"), reply_markup=main_menu(is_admin, lang))
    await safe_callback_answer(callback)


@router.callback_query(F.data.regexp(r"^att:res:\d+$"))
async def attendance_reschedule(callback: CallbackQuery, lang: str, state: FSMContext) -> None:
    booking_id = _booking_id_from_callback(callback.data)
    async with async_session_factory() as session:
        pair = await get_client_booking(session, booking_id, callback.from_user.id)
        if not pair:
            await safe_callback_answer(callback, t(lang, "attendance_unavailable"), show_alert=True)
            return
    started = await begin_client_reschedule(callback, booking_id, lang, state)
    if not started:
        return
