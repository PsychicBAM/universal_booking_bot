import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.bot.handlers.admin_bookings import show_booking_detail, show_bookings_folder
from app.bot.i18n import t
from app.bot.keyboards.admin_attendance_kb import admin_attendance_resend_confirm_kb
from app.bot.utils.attendance_helpers import has_attendance_response
from app.bot.utils.callbacks import safe_callback_answer
from app.bot.utils.telegram_ui import edit_or_send
from app.database.session import async_session_factory
from app.models import Client
from app.repositories import BookingRepository, ServiceRepository
from app.services.admin_attendance_service import (
    mark_manual_attendance_sent,
    send_attendance_question_to_client,
)
from app.services.admin_bookings_service import parse_attendance_back
from app.services.attendance_service import is_booking_attendance_eligible

router = Router()
logger = logging.getLogger(__name__)


def _parse_list_callback(data: str) -> tuple[str, int]:
    parts = data.split(":")
    filter_key = parts[3] if len(parts) > 3 else "7d"
    page = int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else 0
    return filter_key, page


def _parse_view_callback(data: str) -> tuple[int, str]:
    parts = data.split(":")
    booking_id = int(parts[2])
    back = ":".join(parts[3:]) if len(parts) > 3 else "from:waiting:0"
    return booking_id, back


def _parse_action_callback(data: str) -> tuple[int, str]:
    parts = data.split(":")
    booking_id = int(parts[2])
    back = ":".join(parts[3:]) if len(parts) > 3 else f"from:waiting:0"
    return booking_id, back


@router.callback_query(F.data.regexp(r"^adm_att:list:"))
async def admin_attendance_list_legacy(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    await safe_callback_answer(callback)
    await show_bookings_folder(callback, lang, "waiting_client_response", 0)


@router.callback_query(F.data.regexp(r"^adm_att:view:"))
async def admin_attendance_view(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    booking_id, back = _parse_view_callback(callback.data)
    section, page = parse_attendance_back(back)
    await show_booking_detail(callback, lang, booking_id, section, page)
    await safe_callback_answer(callback)


@router.callback_query(F.data.regexp(r"^adm_att:sendok:"))
async def admin_attendance_send_confirmed(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    booking_id, back = _parse_action_callback(callback.data)
    await _do_send_question(callback, lang, booking_id, back)


@router.callback_query(F.data.regexp(r"^adm_att:send:"))
async def admin_attendance_send(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    await safe_callback_answer(callback)
    booking_id, back = _parse_action_callback(callback.data)
    async with async_session_factory() as session:
        booking = await BookingRepository(session).get_by_id(booking_id)
        if not booking or not is_booking_attendance_eligible(booking):
            await safe_callback_answer(callback, t(lang, "not_found"), show_alert=True)
            return
        if has_attendance_response(booking):
            await edit_or_send(
                callback,
                t(lang, "admin_attendance_already_answered_confirm"),
                reply_markup=admin_attendance_resend_confirm_kb(booking_id, back, lang),
            )
            return
    await _do_send_question(callback, lang, booking_id, back)


async def _do_send_question(
    callback: CallbackQuery,
    lang: str,
    booking_id: int,
    back: str,
) -> None:
    async with async_session_factory() as session:
        booking = await BookingRepository(session).get_by_id(booking_id)
        if not booking or not is_booking_attendance_eligible(booking):
            await callback.message.answer(t(lang, "not_found"))
            return
        client = await session.get(Client, booking.client_id)
        if not client:
            await callback.message.answer(t(lang, "admin_attendance_send_failed"))
            return
        service = await ServiceRepository(session).get_by_id(booking.service_id)
        service_name = service.name if service else f"#{booking.service_id}"
        sent = await send_attendance_question_to_client(
            callback.bot,
            session,
            booking,
            client,
            service_name,
            manual=True,
        )
        if not sent:
            await callback.message.answer(t(lang, "admin_attendance_send_failed"))
            return
        mark_manual_attendance_sent(booking, callback.from_user.id)
        await session.commit()

    await callback.message.answer(t(lang, "admin_attendance_sent"))
    section, page = parse_attendance_back(back)
    await show_booking_detail(callback, lang, booking_id, section, page)
