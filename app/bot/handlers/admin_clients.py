import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.i18n import t
from app.bot.keyboards import ADMIN_CLIENTS_TEXTS, admin_menu, cancel_kb
from app.bot.keyboards.admin_clients_kb import (
    admin_client_bookings_kb,
    admin_client_detail_kb,
    admin_clients_list_kb,
    admin_clients_main_kb,
    admin_clients_search_results_kb,
)
from app.bot.states import AdminClientSearchStates, AdminMessageStates
from app.bot.utils.callbacks import safe_callback_answer
from app.bot.utils.telegram_ui import edit_or_send
from app.database.session import async_session_factory
from app.models import Client
from app.repositories import BookingRepository, ClientRepository, ServiceRepository
from app.services.admin_attendance_service import mark_manual_attendance_sent, send_attendance_question_to_client
from app.services.client_history_service import (
    CLIENT_PAGE_SIZE,
    DEFAULT_CLIENT_FILTER,
    format_booking_history_row,
    format_client_detail_text,
    format_future_booking_row,
    get_client_history,
    get_client_stats,
    list_clients,
    normalize_client_filter,
    search_clients,
)

router = Router()
logger = logging.getLogger(__name__)


def _parse_list_callback(data: str) -> tuple[str, int]:
    parts = data.split(":")
    filter_key = normalize_client_filter(parts[3] if len(parts) > 3 else DEFAULT_CLIENT_FILTER)
    page = int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else 0
    return filter_key, page


def _parse_view_callback(data: str) -> tuple[int, str, int]:
    parts = data.split(":")
    client_id = int(parts[2])
    filter_key = normalize_client_filter(parts[3] if len(parts) > 3 else DEFAULT_CLIENT_FILTER)
    page = int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else 0
    return client_id, filter_key, page


def _parse_section_callback(data: str) -> tuple[str, int, str, int, int]:
    parts = data.split(":")
    section = parts[2]
    client_id = int(parts[3])
    filter_key = normalize_client_filter(parts[4] if len(parts) > 4 else DEFAULT_CLIENT_FILTER)
    page = int(parts[5]) if len(parts) > 5 and parts[5].isdigit() else 0
    section_page = int(parts[6]) if len(parts) > 6 and parts[6].isdigit() else 0
    return section, client_id, filter_key, page, section_page


async def show_clients_main(event: CallbackQuery | Message, lang: str) -> None:
    text = f"{t(lang, 'clients_hub_simplified_title')}\n\n{t(lang, 'clients_hub_simplified_intro')}"
    keyboard = admin_clients_main_kb(lang)
    if isinstance(event, CallbackQuery):
        await edit_or_send(event, text, reply_markup=keyboard)
    else:
        await event.answer(text, reply_markup=keyboard)


async def show_clients_list(
    event: CallbackQuery,
    lang: str,
    filter_key: str,
    page: int,
) -> None:
    async with async_session_factory() as session:
        page_items, page, total_pages = await list_clients(session, filter_key, page=page)
    filter_label = t(lang, "clients_all_button") if filter_key == "all" else t(lang, f"clients_filter_{filter_key}")
    lines = [t(lang, "clients_hub_simplified_title"), "", filter_label, ""]
    if not page_items:
        lines.append(t(lang, "clients_no_results"))
    text = "\n".join(lines)
    keyboard = admin_clients_list_kb(page_items, filter_key, page, total_pages, lang)
    await edit_or_send(event, text, reply_markup=keyboard)


async def show_client_detail(
    event: CallbackQuery,
    lang: str,
    client_id: int,
    filter_key: str,
    page: int,
) -> None:
    async with async_session_factory() as session:
        stats = await get_client_stats(session, client_id)
    if not stats:
        await safe_callback_answer(event, t(lang, "not_found"), show_alert=True)
        return
    text = format_client_detail_text(stats, lang)
    keyboard = admin_client_detail_kb(client_id, filter_key, page, username=stats.username, lang=lang)
    await edit_or_send(event, text, reply_markup=keyboard)


async def show_client_section(
    event: CallbackQuery,
    lang: str,
    section: str,
    client_id: int,
    filter_key: str,
    page: int,
    section_page: int,
) -> None:
    async with async_session_factory() as session:
        history = await get_client_history(session, client_id)
        if not history:
            await safe_callback_answer(event, t(lang, "not_found"), show_alert=True)
            return
        client = await ClientRepository(session).get_by_id(client_id)

    if section == "future":
        bookings = history.future_bookings
        title = t(lang, "client_future_bookings")
        row_formatter = format_future_booking_row
    else:
        bookings = history.history_bookings
        title = t(lang, "client_booking_history")
        row_formatter = format_booking_history_row

    total = len(bookings)
    total_pages = max(1, (total + CLIENT_PAGE_SIZE - 1) // CLIENT_PAGE_SIZE) if total else 1
    section_page = max(0, min(section_page, total_pages - 1))
    start = section_page * CLIENT_PAGE_SIZE
    page_items = bookings[start : start + CLIENT_PAGE_SIZE]

    lines = [title, ""]
    if not page_items:
        lines.append(t(lang, "clients_no_results"))
    else:
        for booking in page_items:
            row_text = row_formatter(booking, "", lang, client=client)
            lines.append(row_text)

    booking_labels = [
        (
            booking.id,
            row_formatter(booking, "", lang, client=client),
        )
        for booking in page_items
    ]
    text = "\n".join(lines)
    keyboard = admin_client_bookings_kb(
        booking_labels,
        client_id,
        filter_key,
        page,
        section,
        section_page,
        total_pages,
        lang,
    )
    await edit_or_send(event, text, reply_markup=keyboard)


@router.callback_query(F.data == "adm_cli:admin_back")
async def clients_back_admin(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    await safe_callback_answer(callback)
    await callback.message.answer(t(lang, "admin_panel"), reply_markup=admin_menu(lang))


@router.callback_query(F.data == "adm_cli:menu")
async def clients_menu_callback(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    await safe_callback_answer(callback)
    await show_clients_main(callback, lang)


@router.callback_query(F.data.regexp(r"^adm_cli:list:"))
async def clients_list_callback(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    filter_key, page = _parse_list_callback(callback.data)
    await safe_callback_answer(callback)
    await show_clients_list(callback, lang, filter_key, page)


@router.callback_query(F.data.regexp(r"^adm_cli:view:"))
async def client_view_callback(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    client_id, filter_key, page = _parse_view_callback(callback.data)
    await safe_callback_answer(callback)
    await show_client_detail(callback, lang, client_id, filter_key, page)


@router.callback_query(F.data.regexp(r"^adm_cli:(future|hist):"))
async def client_section_callback(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    section, client_id, filter_key, page, section_page = _parse_section_callback(callback.data)
    await safe_callback_answer(callback)
    await show_client_section(callback, lang, section, client_id, filter_key, page, section_page)


@router.callback_query(F.data.regexp(r"^adm_cli:msg:"))
async def client_message_callback(callback: CallbackQuery, state: FSMContext, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    client_id, filter_key, page = _parse_view_callback(
        callback.data.replace("adm_cli:msg:", "adm_cli:view:", 1)
    )
    await state.update_data(
        msg_client_id=client_id,
        msg_booking_id=None,
        flow_origin="admin_clients",
        clients_filter=filter_key,
        clients_page=page,
    )
    await state.set_state(AdminMessageStates.entering_message)
    await callback.message.answer(t(lang, "enter_message_client"), reply_markup=cancel_kb(lang))
    await safe_callback_answer(callback)


@router.callback_query(F.data.regexp(r"^adm_cli:confirm:"))
async def client_confirm_nearest_callback(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    client_id, filter_key, page = _parse_view_callback(
        callback.data.replace("adm_cli:confirm:", "adm_cli:view:", 1)
    )
    async with async_session_factory() as session:
        history = await get_client_history(session, client_id)
        if not history or not history.future_bookings:
            await safe_callback_answer(callback, t(lang, "client_no_upcoming_booking"), show_alert=True)
            return
        booking = history.future_bookings[0]
        client = await session.get(Client, client_id)
        if not client:
            await safe_callback_answer(callback, t(lang, "not_found"), show_alert=True)
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

    await safe_callback_answer(callback, t(lang, "admin_attendance_sent"))
    await show_client_detail(callback, lang, client_id, filter_key, page)


@router.callback_query(F.data == "adm_cli:search")
async def client_search_start(callback: CallbackQuery, state: FSMContext, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    await state.update_data(flow_origin="admin_clients")
    await state.set_state(AdminClientSearchStates.entering_query)
    await callback.message.answer(t(lang, "client_search_prompt"), reply_markup=cancel_kb(lang))
    await safe_callback_answer(callback)


@router.message(AdminClientSearchStates.entering_query, F.text)
async def client_search_query(message: Message, state: FSMContext, lang: str) -> None:
    query = message.text.strip()
    async with async_session_factory() as session:
        results = await search_clients(session, query)
    await state.clear()
    if not results:
        await message.answer(t(lang, "clients_no_results"), reply_markup=admin_clients_main_kb(lang))
        return
    lines = [t(lang, "clients_title"), "", t(lang, "clients_search"), ""]
    text = "\n".join(lines)
    await message.answer(text, reply_markup=admin_clients_search_results_kb(results, lang))


@router.message(F.text.in_(ADMIN_CLIENTS_TEXTS))
async def admin_clients_entry(message: Message, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    await show_clients_main(message, lang)
