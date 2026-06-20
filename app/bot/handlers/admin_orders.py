import logging

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.i18n import t
from app.bot.keyboards import ADMIN_ORDERS_TEXTS, admin_menu, cancel_kb
from app.bot.keyboards.orders_kb import (
    admin_order_detail_kb,
    admin_orders_folder_kb,
    admin_orders_hub_kb,
)
from app.bot.states import AdminMessageStates, OrderStates
from app.bot.utils.callbacks import safe_callback_answer
from app.bot.utils.menu_helpers import menu_mode_kwargs
from app.bot.utils.telegram_ui import edit_or_send, safe_edit_text
from app.database.session import async_session_factory
from app.models import Client, ServiceOrderStatus
from app.repositories import ServiceOrderRepository, ServiceRepository
from app.services.order_service import add_admin_note, order_status_counts, update_order_status
from app.services.booking_notification_service import notify_client_order_cancelled_by_admin
from app.utils.formatting import format_order_admin

router = Router()
logger = logging.getLogger(__name__)

PAGE_SIZE = 10


async def show_orders_hub(event: CallbackQuery | Message, lang: str) -> None:
    async with async_session_factory() as session:
        counts = await order_status_counts(session)
    text = f"{t(lang, 'orders_title')}\n\n{t(lang, 'orders_hub_intro')}"
    keyboard = admin_orders_hub_kb(counts, lang)
    if isinstance(event, CallbackQuery):
        await edit_or_send(event, text, reply_markup=keyboard)
    else:
        await event.answer(text, reply_markup=keyboard)


@router.message(F.text.in_(ADMIN_ORDERS_TEXTS))
async def admin_orders_message(message: Message, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    await show_orders_hub(message, lang)


@router.callback_query(F.data == "ord:hub")
async def admin_orders_hub(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    await safe_callback_answer(callback)
    await show_orders_hub(callback, lang)


@router.callback_query(F.data == "ord:back:admin")
async def admin_orders_back(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    await safe_callback_answer(callback)
    async with async_session_factory() as session:
        kwargs = await menu_mode_kwargs(session)
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(t(lang, "admin_panel"), reply_markup=admin_menu(lang, **kwargs))


@router.callback_query(F.data.regexp(r"^ord:folder:[a-z_]+:\d+$"))
async def admin_orders_folder(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    await safe_callback_answer(callback)
    _, _, section, page_s = callback.data.split(":", 3)
    page = int(page_s)
    async with async_session_factory() as session:
        orders, total = await ServiceOrderRepository(session).list_by_status(
            section if section != "all" else None, page=page, limit=PAGE_SIZE
        )
        names = {s.id: s.name for s in await ServiceRepository(session).list_all()}
    total_pages = max((total - 1) // PAGE_SIZE, 0)
    for o in orders:
        setattr(o, "_service_name", names.get(o.service_id))
    lines = [t(lang, f"orders_folder_{section}", count=str(total))]
    await safe_edit_text(
        callback.message,
        "\n".join(lines),
        reply_markup=admin_orders_folder_kb(orders, section, page, total_pages, lang),
    )


@router.callback_query(F.data.regexp(r"^ord:view:\d+:[a-z_]+:\d+$"))
async def admin_order_detail(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    await safe_callback_answer(callback)
    parts = callback.data.split(":")
    order_id = int(parts[2])
    section = parts[3]
    page = int(parts[4])
    async with async_session_factory() as session:
        order = await ServiceOrderRepository(session).get_by_id(order_id)
        service = await ServiceRepository(session).get_by_id(order.service_id) if order else None
    if not order:
        await callback.message.answer(t(lang, "not_found"))
        return
    await safe_edit_text(
        callback.message,
        format_order_admin(order, service, lang),
        reply_markup=admin_order_detail_kb(order.id, order.status, section, page, lang),
    )


@router.callback_query(F.data.regexp(r"^ord:status:[a-z_]+:\d+$"))
async def admin_order_status(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    _, _, status, order_id_s = callback.data.split(":", 3)
    order_id = int(order_id_s)
    async with async_session_factory() as session:
        order = await update_order_status(session, order_id, status)
        await session.commit()
        service = await ServiceRepository(session).get_by_id(order.service_id) if order else None
    if not order:
        await safe_callback_answer(callback, t(lang, "not_found"), show_alert=True)
        return
    if status == "cancelled":
        await notify_client_order_cancelled_by_admin(callback.bot, order, service)
    await safe_callback_answer(callback, t(lang, "order_status_updated"))
    await safe_edit_text(
        callback.message,
        format_order_admin(order, service, lang),
        reply_markup=admin_order_detail_kb(order.id, order.status, "new", 0, lang),
    )


@router.callback_query(F.data.regexp(r"^ord:msg:\d+$"))
async def admin_order_message_client(callback: CallbackQuery, state: FSMContext, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    order_id = int(callback.data.rsplit(":", 1)[1])
    async with async_session_factory() as session:
        order = await ServiceOrderRepository(session).get_by_id(order_id)
    if not order:
        await safe_callback_answer(callback, t(lang, "not_found"), show_alert=True)
        return
    await state.update_data(msg_client_id=order.client_id, flow_origin="admin")
    await state.set_state(AdminMessageStates.entering_message)
    await callback.message.answer(t(lang, "enter_message_client"), reply_markup=cancel_kb(lang))
    await safe_callback_answer(callback)


@router.callback_query(F.data.regexp(r"^ord:note:\d+$"))
async def admin_order_note_start(callback: CallbackQuery, state: FSMContext, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    order_id = int(callback.data.rsplit(":", 1)[1])
    await state.update_data(order_note_id=order_id, flow_origin="admin")
    await state.set_state(OrderStates.editing_note)
    await callback.message.answer(t(lang, "order_admin_note_prompt"), reply_markup=cancel_kb(lang))
    await safe_callback_answer(callback)


@router.message(OrderStates.editing_note, F.text)
async def admin_order_note_save(message: Message, state: FSMContext, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    data = await state.get_data()
    order_id = data.get("order_note_id")
    async with async_session_factory() as session:
        order = await add_admin_note(session, order_id, message.text.strip())
        await session.commit()
        kwargs = await menu_mode_kwargs(session)
    await state.clear()
    await message.answer(t(lang, "order_admin_note_saved"), reply_markup=admin_menu(lang, **kwargs))
