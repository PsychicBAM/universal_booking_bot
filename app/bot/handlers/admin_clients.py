import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.i18n import t
from app.bot.keyboards import ADMIN_CLIENTS_TEXTS, cancel_kb
from app.bot.keyboards.admin_clients_kb import (
    admin_client_bookings_kb,
    admin_client_detail_kb,
    admin_clients_list_kb,
    admin_clients_main_kb,
    admin_clients_search_results_kb,
)
from app.bot.states import AdminClientSearchStates, AdminMessageStates
from app.bot.utils.menu_helpers import show_admin_panel
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

# adm_cli callback patterns (namespace adm_cli):
#   adm_cli:admin_back
#   adm_cli:menu
#   adm_cli:search
#   adm_cli:all                          — legacy list shortcut (filter=all, page=0)
#   adm_cli:list:{filter}:{page}         — client list (filter: all|upcoming|visited|new|returning|cancelled)
#   adm_cli:view:{client_id}:{filter}:{page}
#   adm_cli:{future|hist}:{client_id}:{filter}:{page}[:{section_page}]
#   adm_cli:section:{future|hist}:{client_id}:{filter}:{page}[:{section_page}]  — legacy section prefix
#   adm_cli:msg:{client_id}:{filter}:{page}
#   adm_cli:confirm:{client_id}:{filter}:{page}


def _safe_page_token(token: str | None) -> int:
    return int(token) if token and token.isdigit() else 0


def _safe_client_id_token(token: str | None) -> int | None:
    return int(token) if token and token.isdigit() else None


def _parse_list_callback(data: str) -> tuple[str, int] | None:
    parts = data.split(":")
    if len(parts) < 2 or parts[0] != "adm_cli":
        return None
    # Legacy shortcut: adm_cli:all
    if len(parts) == 2 and parts[1] == "all":
        return DEFAULT_CLIENT_FILTER, 0
    if parts[1] != "list":
        return None
    filter_key = normalize_client_filter(parts[2] if len(parts) > 2 else DEFAULT_CLIENT_FILTER)
    page = _safe_page_token(parts[3] if len(parts) > 3 else None)
    return filter_key, page


def _parse_view_callback(data: str) -> tuple[int | None, str, int]:
    parts = data.split(":")
    if len(parts) < 3 or parts[0] != "adm_cli" or parts[1] != "view":
        return None, DEFAULT_CLIENT_FILTER, 0
    client_id = _safe_client_id_token(parts[2])
    filter_key = normalize_client_filter(parts[3] if len(parts) > 3 else DEFAULT_CLIENT_FILTER)
    page = _safe_page_token(parts[4] if len(parts) > 4 else None)
    return client_id, filter_key, page


def _parse_section_callback(
    data: str,
) -> tuple[str, int | None, str, int, int] | None:
    parts = data.split(":")
    if len(parts) < 2 or parts[0] != "adm_cli":
        return None
    # Not a section callback (e.g. adm_cli:all, adm_cli:list:...)
    if parts[1] in ("all", "list", "view", "menu", "search", "admin_back", "msg", "confirm"):
        return None
    if parts[1] == "section" and len(parts) >= 4:
        section = parts[2]
        client_token = parts[3]
        filter_idx = 4
        page_idx = 5
        section_page_idx = 6
    elif parts[1] in ("future", "hist"):
        section = parts[1]
        client_token = parts[2] if len(parts) > 2 else None
        filter_idx = 3
        page_idx = 4
        section_page_idx = 5
    else:
        return None
    if section not in ("future", "hist"):
        return None
    client_id = _safe_client_id_token(client_token)
    filter_key = normalize_client_filter(
        parts[filter_idx] if len(parts) > filter_idx else DEFAULT_CLIENT_FILTER
    )
    page = _safe_page_token(parts[page_idx] if len(parts) > page_idx else None)
    section_page = _safe_page_token(parts[section_page_idx] if len(parts) > section_page_idx else None)
    return section, client_id, filter_key, page, section_page


async def _handle_invalid_clients_callback(callback: CallbackQuery, lang: str) -> None:
    logger.warning("Invalid admin clients callback: %s", callback.data)
    await safe_callback_answer(callback, t(lang, "client_callback_invalid"), show_alert=True)
    await show_clients_main(callback, lang)


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
    await show_admin_panel(callback.message, lang)


@router.callback_query(F.data == "adm_cli:menu")
async def clients_menu_callback(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    await safe_callback_answer(callback)
    await show_clients_main(callback, lang)


@router.callback_query(F.data.regexp(r"^adm_cli:(list:|all$)"))
async def clients_list_callback(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    parsed = _parse_list_callback(callback.data)
    if parsed is None:
        await _handle_invalid_clients_callback(callback, lang)
        return
    filter_key, page = parsed
    await safe_callback_answer(callback)
    await show_clients_list(callback, lang, filter_key, page)


@router.callback_query(F.data.regexp(r"^adm_cli:view:"))
async def client_view_callback(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    client_id, filter_key, page = _parse_view_callback(callback.data)
    if client_id is None:
        await _handle_invalid_clients_callback(callback, lang)
        return
    await safe_callback_answer(callback)
    await show_client_detail(callback, lang, client_id, filter_key, page)


@router.callback_query(F.data.regexp(r"^adm_cli:(future|hist|section):"))
async def client_section_callback(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    parsed = _parse_section_callback(callback.data)
    if parsed is None:
        await _handle_invalid_clients_callback(callback, lang)
        return
    section, client_id, filter_key, page, section_page = parsed
    if client_id is None:
        await _handle_invalid_clients_callback(callback, lang)
        return
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
    if client_id is None:
        await _handle_invalid_clients_callback(callback, lang)
        return
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
    if client_id is None:
        await _handle_invalid_clients_callback(callback, lang)
        return
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
