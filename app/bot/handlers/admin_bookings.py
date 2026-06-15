import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.bot.i18n import t
from app.bot.keyboards import ADMIN_BOOKINGS_TEXTS, admin_menu
from app.bot.keyboards.admin_bookings_kb import (
    admin_booking_detail_kb,
    admin_bookings_folder_kb,
    admin_bookings_hub_kb,
)
from app.bot.utils.callbacks import safe_callback_answer
from app.bot.utils.telegram_ui import edit_or_send, safe_edit_text
from app.database.session import async_session_factory
from app.models import Client
from app.repositories import BookingRepository, ServiceRepository
from app.services.admin_bookings_service import (
    build_bookings_folder_body,
    build_bookings_hub_body,
    load_bookings_folder,
    load_bookings_hub,
    parse_bookings_list_callback,
    parse_bookings_view_callback,
)
from app.services.attendance_service import is_booking_attendance_eligible
from app.utils.formatting import format_booking

router = Router()
logger = logging.getLogger(__name__)


async def show_bookings_hub(
    event: CallbackQuery | Message,
    lang: str,
    *,
    prefix: str | None = None,
) -> None:
    async with async_session_factory() as session:
        _bookings, counts = await load_bookings_hub(session)
    text = build_bookings_hub_body(counts, lang)
    if prefix:
        text = f"{prefix}\n\n{text}"
    keyboard = admin_bookings_hub_kb(lang)
    if isinstance(event, CallbackQuery):
        await edit_or_send(event, text, reply_markup=keyboard)
    else:
        await event.answer(text, reply_markup=keyboard)


async def show_bookings_folder(
    event: CallbackQuery | Message,
    lang: str,
    section: str,
    page: int,
) -> None:
    async with async_session_factory() as session:
        page_items, _filtered, page, total_pages = await load_bookings_folder(session, section, page)
    text = build_bookings_folder_body(section, page_items, lang)
    keyboard = admin_bookings_folder_kb(page_items, section, page, total_pages, lang)
    if isinstance(event, CallbackQuery):
        await edit_or_send(event, text, reply_markup=keyboard)
    else:
        await event.answer(text, reply_markup=keyboard)


async def show_booking_detail(
    callback: CallbackQuery,
    lang: str,
    booking_id: int,
    section: str,
    page: int,
) -> None:
    async with async_session_factory() as session:
        booking = await BookingRepository(session).get_by_id(booking_id)
        service = await ServiceRepository(session).get_by_id(booking.service_id) if booking else None
        client = await session.get(Client, booking.client_id) if booking else None
    if not booking:
        await safe_callback_answer(callback, t(lang, "not_found"), show_alert=True)
        return
    username = client.username if client else None
    show_send = is_booking_attendance_eligible(booking)
    await safe_edit_text(
        callback.message,
        format_booking(booking, service, lang, admin_view=True, client_username=username),
        reply_markup=admin_booking_detail_kb(
            booking_id,
            booking.status.value,
            section,
            page,
            lang,
            show_send_confirmation=show_send,
        ),
    )


@router.message(F.text.in_(ADMIN_BOOKINGS_TEXTS))
async def admin_bookings_message(message: Message, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    await show_bookings_hub(message, lang)


@router.callback_query(F.data == "adm_book:hub")
@router.callback_query(F.data == "adm_bookings:list")
async def admin_bookings_hub_callback(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    await safe_callback_answer(callback)
    await show_bookings_hub(callback, lang)


@router.callback_query(F.data == "adm_book:admin_back")
async def admin_bookings_back_to_panel(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    await safe_callback_answer(callback)
    await callback.message.answer(t(lang, "admin_panel"), reply_markup=admin_menu(lang))


@router.callback_query(F.data.regexp(r"^adm_book:list:"))
async def admin_bookings_folder_callback(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    section, page = parse_bookings_list_callback(callback.data)
    await safe_callback_answer(callback)
    await show_bookings_folder(callback, lang, section, page)


@router.callback_query(F.data.regexp(r"^adm_book:view:"))
async def admin_bookings_view_callback(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    booking_id, section, page = parse_bookings_view_callback(callback.data)
    await show_booking_detail(callback, lang, booking_id, section, page)
    await safe_callback_answer(callback)


@router.callback_query(F.data.startswith("adm_booking:"))
async def admin_booking_legacy_view(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    booking_id = int(callback.data.split(":", 1)[1])
    await show_booking_detail(callback, lang, booking_id, "upcoming", 0)
    await safe_callback_answer(callback)
