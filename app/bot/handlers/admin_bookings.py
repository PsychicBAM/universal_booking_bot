import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.i18n import t
from app.bot.keyboards import ADMIN_BOOKINGS_TEXTS, cancel_kb
from app.bot.keyboards.admin_bookings_kb import (
    admin_booking_detail_kb,
    admin_bookings_folder_kb,
    admin_bookings_hub_kb,
)
from app.bot.states import AdminBookingSearchStates
from app.bot.utils.callbacks import safe_callback_answer
from app.bot.utils.menu_helpers import show_admin_panel
from app.bot.utils.telegram_ui import edit_or_send, safe_edit_text
from app.database.session import async_session_factory
from app.models import Client
from app.repositories import BookingRepository, ServiceRepository
from app.services.admin_bookings_service import (
    BookingDetailSource,
    build_bookings_folder_body,
    build_bookings_hub_body,
    is_manual_attendance_send_eligible,
    load_bookings_folder,
    load_bookings_hub,
    paginate_bookings_folder,
    parse_booking_detail_source,
    parse_bookings_list_callback,
    parse_bookings_view_callback,
    search_bookings,
)
from app.utils.formatting import format_booking

router = Router()
logger = logging.getLogger(__name__)


async def _load_service_names(session, bookings) -> dict[int, str]:
    service_ids = {booking.service_id for booking in bookings if booking.service_id}
    names: dict[int, str] = {}
    repo = ServiceRepository(session)
    for service_id in service_ids:
        service = await repo.get_by_id(service_id)
        if service and service.name and service.name.strip():
            names[service_id] = service.name.strip()
    return names


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
        page_items, filtered, page, total_pages = await load_bookings_folder(session, section, page)
        service_names = await _load_service_names(session, filtered)
    text = build_bookings_folder_body(section, page_items, lang)
    keyboard = admin_bookings_folder_kb(
        page_items,
        section,
        page,
        total_pages,
        lang,
        service_names=service_names,
    )
    if isinstance(event, CallbackQuery):
        await edit_or_send(event, text, reply_markup=keyboard)
    else:
        await event.answer(text, reply_markup=keyboard)


async def show_booking_detail(
    callback: CallbackQuery,
    lang: str,
    booking_id: int,
    source: BookingDetailSource,
    *,
    prefix: str | None = None,
) -> None:
    async with async_session_factory() as session:
        booking = await BookingRepository(session).get_by_id(booking_id)
        service = await ServiceRepository(session).get_by_id(booking.service_id) if booking else None
        client = await session.get(Client, booking.client_id) if booking else None
    if not booking:
        await safe_callback_answer(callback, t(lang, "not_found"), show_alert=True)
        return
    username = client.username if client else None
    show_send = is_manual_attendance_send_eligible(booking)
    text = format_booking(booking, service, lang, admin_view=True, client_username=username)
    if prefix:
        text = f"{prefix}\n\n{text}"
    await safe_edit_text(
        callback.message,
        text,
        reply_markup=admin_booking_detail_kb(
            booking,
            source,
            lang,
            show_send_confirmation=show_send,
        ),
    )


@router.message(F.text.in_(ADMIN_BOOKINGS_TEXTS))
async def admin_bookings_message(message: Message, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    async with async_session_factory() as session:
        from app.services.service_modes_service import load_service_modes

        modes = await load_service_modes(session)
    if not modes.booking_enabled:
        await message.answer(t(lang, "bookings_disabled_booking_off"))
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
    await show_admin_panel(callback.message, lang)


@router.callback_query(F.data.regexp(r"^adm_book:list:"))
async def admin_bookings_folder_callback(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    section, page = parse_bookings_list_callback(callback.data)
    await safe_callback_answer(callback)
    await show_bookings_folder(callback, lang, section, page)


@router.callback_query(F.data == "adm_book:search")
async def admin_bookings_search_start(
    callback: CallbackQuery,
    state: FSMContext,
    is_admin: bool,
    lang: str,
) -> None:
    if not is_admin:
        return
    await state.set_state(AdminBookingSearchStates.entering_query)
    await callback.message.answer(t(lang, "bookings_search_prompt"), reply_markup=cancel_kb(lang))
    await safe_callback_answer(callback)


@router.message(AdminBookingSearchStates.entering_query, F.text)
async def admin_bookings_search_query(
    message: Message,
    state: FSMContext,
    is_admin: bool,
    lang: str,
) -> None:
    if not is_admin:
        return
    query = (message.text or "").strip()
    async with async_session_factory() as session:
        bookings = await BookingRepository(session).list_all_bookings()
        service_names = await _load_service_names(session, bookings)
        results = search_bookings(bookings, query, service_names)
    await state.clear()
    if not results:
        await message.answer(t(lang, "bookings_search_no_results"), reply_markup=admin_bookings_hub_kb(lang))
        return
    page_items, page, total_pages = paginate_bookings_folder(results, 0)
    text = "\n".join(
        [
            t(lang, "bookings_search_button"),
            "",
            t(lang, "bookings_choose_action"),
        ]
    )
    keyboard = admin_bookings_folder_kb(
        page_items,
        "search",
        page,
        total_pages,
        lang,
        service_names=service_names,
    )
    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data.regexp(r"^adm_book:view:"))
async def admin_bookings_view_callback(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    booking_id, source = parse_bookings_view_callback(callback.data)
    if not booking_id:
        await safe_callback_answer(callback, t(lang, "booking_back_context_invalid"), show_alert=True)
        return
    await show_booking_detail(callback, lang, booking_id, source)
    await safe_callback_answer(callback)


@router.callback_query(F.data.startswith("adm_booking:"))
async def admin_booking_legacy_view(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    booking_id, source = parse_booking_detail_source(callback.data)
    if booking_id is None or source is None:
        await safe_callback_answer(callback, t(lang, "booking_back_context_invalid"), show_alert=True)
        return
    await show_booking_detail(callback, lang, booking_id, source)
    await safe_callback_answer(callback)
