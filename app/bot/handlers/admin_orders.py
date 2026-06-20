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
    order_history_kb,
)
from app.bot.states import AdminMessageStates, AdminOrderStates, OrderStates
from app.bot.utils.callbacks import safe_callback_answer
from app.bot.utils.menu_helpers import menu_mode_kwargs
from app.bot.utils.telegram_ui import edit_or_send, safe_edit_text
from app.database.session import async_session_factory
from app.models import Client, ServiceOrderStatus
from app.repositories import ServiceOrderRepository, ServiceRepository
from app.services.booking_notification_service import notify_client_order_cancelled_by_admin
from app.services.order_service import (
    ORDER_MESSAGE_SENDER_ADMIN,
    accept_order,
    add_admin_note,
    add_order_message,
    build_order_history_text,
    decline_order,
    notify_client_order_accepted,
    notify_client_order_declined,
    notify_client_order_message,
    order_status_counts,
    update_order_status,
)
from app.utils.formatting import format_order_admin

router = Router()
logger = logging.getLogger(__name__)

PAGE_SIZE = 10


async def _load_order_bundle(session, order_id: int):
    order = await ServiceOrderRepository(session).get_by_id(order_id)
    service = await ServiceRepository(session).get_by_id(order.service_id) if order else None
    return order, service


async def show_orders_hub(event: CallbackQuery | Message, lang: str) -> None:
    async with async_session_factory() as session:
        counts = await order_status_counts(session)
    text = f"{t(lang, 'orders_title')}\n\n{t(lang, 'orders_hub_intro')}"
    keyboard = admin_orders_hub_kb(counts, lang)
    if isinstance(event, CallbackQuery):
        await edit_or_send(event, text, reply_markup=keyboard)
    else:
        await event.answer(text, reply_markup=keyboard)


async def show_admin_order_detail(
    event: CallbackQuery | Message,
    lang: str,
    order_id: int,
    section: str,
    page: int,
) -> None:
    async with async_session_factory() as session:
        order, service = await _load_order_bundle(session, order_id)
    if not order:
        if isinstance(event, CallbackQuery):
            await event.message.answer(t(lang, "not_found"))
        else:
            await event.answer(t(lang, "not_found"))
        return
    text = format_order_admin(order, service, lang)
    keyboard = admin_order_detail_kb(order.id, order.status, section, page, lang)
    if isinstance(event, CallbackQuery):
        await safe_edit_text(event.message, text, reply_markup=keyboard)
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
    await show_admin_order_detail(callback, lang, int(parts[2]), parts[3], int(parts[4]))


@router.callback_query(F.data.regexp(r"^ord:accept:\d+$"))
async def admin_order_accept(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    order_id = int(callback.data.rsplit(":", 1)[1])
    async with async_session_factory() as session:
        order = await accept_order(session, order_id, admin_telegram_id=callback.from_user.id)
        await session.commit()
        order, service = await _load_order_bundle(session, order_id)
    if not order:
        await safe_callback_answer(callback, t(lang, "not_found"), show_alert=True)
        return
    await notify_client_order_accepted(callback.bot, order, service)
    await safe_callback_answer(callback, t(lang, "order_accepted_admin"))
    await show_admin_order_detail(callback, lang, order_id, "new", 0)


@router.callback_query(F.data.regexp(r"^ord:decline:\d+$"))
async def admin_order_decline_start(
    callback: CallbackQuery,
    state: FSMContext,
    is_admin: bool,
    lang: str,
) -> None:
    if not is_admin:
        return
    order_id = int(callback.data.rsplit(":", 1)[1])
    async with async_session_factory() as session:
        order = await ServiceOrderRepository(session).get_by_id(order_id)
    if not order or order.status != ServiceOrderStatus.NEW.value:
        await safe_callback_answer(callback, t(lang, "not_found"), show_alert=True)
        return
    await state.update_data(order_decline_id=order_id, flow_origin="admin")
    await state.set_state(AdminOrderStates.entering_decline_reason)
    await callback.message.answer(t(lang, "order_decline_reason_prompt"), reply_markup=cancel_kb(lang))
    await safe_callback_answer(callback)


@router.message(AdminOrderStates.entering_decline_reason, F.text)
async def admin_order_decline_save(
    message: Message,
    state: FSMContext,
    bot: Bot,
    is_admin: bool,
    lang: str,
) -> None:
    if not is_admin:
        return
    data = await state.get_data()
    order_id = data.get("order_decline_id")
    reason = (message.text or "").strip()
    if not order_id or not reason:
        await message.answer(t(lang, "order_decline_reason_prompt"), reply_markup=cancel_kb(lang))
        return
    async with async_session_factory() as session:
        order = await decline_order(
            session,
            order_id,
            reason,
            admin_telegram_id=message.from_user.id,
        )
        await session.commit()
        order, service = await _load_order_bundle(session, order_id)
    await state.clear()
    if not order:
        await message.answer(t(lang, "not_found"))
        return
    await notify_client_order_declined(bot, order, service)
    await message.answer(t(lang, "order_declined_admin"))
    await show_admin_order_detail(message, lang, order_id, "declined", 0)


@router.callback_query(F.data.regexp(r"^ord:status:[a-z_]+:\d+$"))
async def admin_order_status(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    _, _, status, order_id_s = callback.data.split(":", 3)
    order_id = int(order_id_s)
    async with async_session_factory() as session:
        order = await ServiceOrderRepository(session).get_by_id(order_id)
        if not order:
            await safe_callback_answer(callback, t(lang, "not_found"), show_alert=True)
            return
        if status == ServiceOrderStatus.IN_PROGRESS.value and order.status not in (
            ServiceOrderStatus.ACCEPTED.value,
            ServiceOrderStatus.IN_PROGRESS.value,
        ):
            await safe_callback_answer(callback, t(lang, "not_found"), show_alert=True)
            return
        order = await update_order_status(session, order_id, status)
        await session.commit()
        order, service = await _load_order_bundle(session, order_id)
    if not order:
        await safe_callback_answer(callback, t(lang, "not_found"), show_alert=True)
        return
    if status == ServiceOrderStatus.CANCELLED.value:
        await notify_client_order_cancelled_by_admin(callback.bot, order, service)
    await safe_callback_answer(callback, t(lang, "order_status_updated"))
    section = "in_progress" if status in (ServiceOrderStatus.IN_PROGRESS.value, ServiceOrderStatus.ACCEPTED.value) else status
    await show_admin_order_detail(callback, lang, order_id, section, 0)


@router.callback_query(F.data.regexp(r"^ord:history:\d+:[a-z_]+:\d+$"))
async def admin_order_history(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    await safe_callback_answer(callback)
    parts = callback.data.split(":")
    order_id = int(parts[2])
    section = parts[3]
    page = int(parts[4])
    async with async_session_factory() as session:
        text = await build_order_history_text(session, order_id, lang)
    await safe_edit_text(
        callback.message,
        text,
        reply_markup=order_history_kb(order_id, section, page, lang),
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
    await state.update_data(msg_order_id=order_id, flow_origin="admin")
    await state.set_state(AdminMessageStates.entering_message)
    await callback.message.answer(t(lang, "order_message_prompt_admin"), reply_markup=cancel_kb(lang))
    await safe_callback_answer(callback)


@router.message(AdminMessageStates.entering_message, F.text)
async def admin_order_message_save(message: Message, state: FSMContext, bot: Bot, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    data = await state.get_data()
    order_id = data.get("msg_order_id")
    if not order_id:
        return
    text = (message.text or "").strip()
    if not text:
        await message.answer(t(lang, "order_message_prompt_admin"), reply_markup=cancel_kb(lang))
        return
    async with async_session_factory() as session:
        order, service = await _load_order_bundle(session, order_id)
        if not order:
            await state.clear()
            await message.answer(t(lang, "not_found"))
            return
        await add_order_message(
            session,
            order_id=order_id,
            sender_type=ORDER_MESSAGE_SENDER_ADMIN,
            message_text=text,
            sender_telegram_id=message.from_user.id,
        )
        await session.commit()
    await state.clear()
    await notify_client_order_message(bot, order, service, text)
    await message.answer(t(lang, "order_message_sent_admin"))


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
