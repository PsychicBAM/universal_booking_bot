import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.bot.i18n import t
from app.bot.keyboards.admin_attendance_kb import (
    admin_attendance_detail_kb,
    admin_attendance_list_kb,
    admin_attendance_resend_confirm_kb,
)
from app.bot.utils.attendance_helpers import attendance_admin_label_indicator, has_attendance_response
from app.services.attendance_service import is_booking_attendance_eligible
from app.bot.utils.callbacks import safe_callback_answer
from app.bot.utils.telegram_ui import edit_or_send
from app.database.session import async_session_factory
from app.models import Client
from app.repositories import BookingRepository, ServiceRepository
from app.services.admin_attendance_service import (
    DEFAULT_ATTENDANCE_FILTER,
    build_attendance_list_body,
    format_admin_attendance_detail,
    load_attendance_list,
    mark_manual_attendance_sent,
    normalize_attendance_filter,
    send_attendance_question_to_client,
)
from app.utils.datetime_utils import now_local, to_local_naive

router = Router()
logger = logging.getLogger(__name__)


def _parse_list_callback(data: str) -> tuple[str, int]:
    parts = data.split(":")
    # adm_att:list:{filter}:{page}
    filter_key = normalize_attendance_filter(parts[3] if len(parts) > 3 else DEFAULT_ATTENDANCE_FILTER)
    page = int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else 0
    return filter_key, page


def _parse_view_callback(data: str) -> tuple[int, str]:
    parts = data.split(":")
    booking_id = int(parts[2])
    back = ":".join(parts[3:]) if len(parts) > 3 else f"list:{DEFAULT_ATTENDANCE_FILTER}:0"
    return booking_id, back


def _parse_action_callback(data: str) -> tuple[int, str]:
    parts = data.split(":")
    booking_id = int(parts[2])
    back = ":".join(parts[3:]) if len(parts) > 3 else f"list:{DEFAULT_ATTENDANCE_FILTER}:0"
    return booking_id, back


async def _show_attendance_list(callback: CallbackQuery, lang: str, filter_key: str, page: int) -> None:
    async with async_session_factory() as session:
        page_items, _filtered, page, total_pages = await load_attendance_list(session, filter_key, page)
    body = build_attendance_list_body(page_items, lang, filter_key)
    keyboard = admin_attendance_list_kb(page_items, filter_key, page, total_pages, lang)
    await edit_or_send(callback, body, reply_markup=keyboard)


async def _show_attendance_detail(
    callback: CallbackQuery,
    lang: str,
    booking_id: int,
    back: str,
) -> None:
    async with async_session_factory() as session:
        booking = await BookingRepository(session).get_by_id(booking_id)
        if not booking or not is_booking_attendance_eligible(booking):
            await safe_callback_answer(callback, t(lang, "not_found"), show_alert=True)
            return
        if to_local_naive(booking.start_at) < now_local():
            await safe_callback_answer(callback, t(lang, "not_found"), show_alert=True)
            return
        service = await ServiceRepository(session).get_by_id(booking.service_id)
        service_name = service.name if service else f"#{booking.service_id}"
    text = format_admin_attendance_detail(booking, service_name, lang)
    keyboard = admin_attendance_detail_kb(booking_id, back, lang)
    await edit_or_send(callback, text, reply_markup=keyboard)


async def _do_send_question(
    callback: CallbackQuery,
    lang: str,
    booking_id: int,
    back: str,
) -> None:
    async with async_session_factory() as session:
        booking = await BookingRepository(session).get_by_id(booking_id)
        if not booking or not is_booking_attendance_eligible(booking):
            await safe_callback_answer(callback, t(lang, "not_found"), show_alert=True)
            return
        client = await session.get(Client, booking.client_id)
        if not client:
            await safe_callback_answer(callback, t(lang, "admin_attendance_send_failed"), show_alert=True)
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
            await safe_callback_answer(callback, t(lang, "admin_attendance_send_failed"), show_alert=True)
            return
        mark_manual_attendance_sent(booking, callback.from_user.id)
        await session.commit()
        service_name = service.name if service else f"#{booking.service_id}"

    await safe_callback_answer(callback, t(lang, "admin_attendance_sent"))
    text = format_admin_attendance_detail(booking, service_name, lang)
    keyboard = admin_attendance_detail_kb(booking_id, back, lang)
    await edit_or_send(callback, text, reply_markup=keyboard)


@router.callback_query(F.data.regexp(r"^adm_att:list:"))
async def admin_attendance_list(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    filter_key, page = _parse_list_callback(callback.data)
    await _show_attendance_list(callback, lang, filter_key, page)
    await safe_callback_answer(callback)


@router.callback_query(F.data.regexp(r"^adm_att:view:"))
async def admin_attendance_view(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    booking_id, back = _parse_view_callback(callback.data)
    await _show_attendance_detail(callback, lang, booking_id, back)
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
            await safe_callback_answer(callback)
            return
    await _do_send_question(callback, lang, booking_id, back)
