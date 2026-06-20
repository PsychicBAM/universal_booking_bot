import logging

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.i18n import t
from app.bot.keyboards import (
    MAIN_MENU_MY_ACTIVITY_TEXTS,
    MY_ORDERS_TEXTS,
    ORDER_SERVICES_TEXTS,
    cancel_kb,
    main_menu,
    my_activity_kb,
    services_kb,
)
from app.services.booking_notification_service import notify_admins_order_cancelled_by_client
from app.bot.keyboards.orders_kb import (
    client_order_detail_kb,
    client_order_history_kb,
    client_orders_active_kb,
    client_orders_empty_active_kb,
    client_orders_empty_history_kb,
    client_orders_history_kb,
    client_orders_hub_kb,
)
from app.bot.order_client_data import show_order_confirmation, start_order_flow
from app.bot.states import BookingStates, OrderStates
from app.bot.utils.callbacks import safe_callback_answer
from app.bot.utils.menu_helpers import menu_mode_kwargs
from app.bot.utils.service_helpers import client_service_unavailable_key, is_order_service, is_service_bookable
from app.bot.utils.telegram_ui import edit_or_send
from app.database.session import async_session_factory
from app.models import SERVICE_TYPE_ORDER, ServiceOrderStatus
from app.repositories import ClientRepository, ServiceOrderRepository, ServiceRepository
from app.services.client_orders_service import (
    compute_client_orders_hub_counts,
    resolve_client_order_section,
    sort_active_client_orders,
    sort_history_client_orders,
    split_client_orders,
)
from app.services.order_service import (
    ORDER_MESSAGE_SENDER_CLIENT,
    add_order_message,
    build_order_history_text,
    cancel_order,
    create_order,
    notify_admins_new_order,
    notify_admins_order_message,
)
from app.utils.formatting import format_order_client

router = Router()
logger = logging.getLogger(__name__)


async def _order_services(session):
    return await ServiceRepository(session).list_client_services(service_type=SERVICE_TYPE_ORDER)


@router.message(F.text.in_(MAIN_MENU_MY_ACTIVITY_TEXTS))
async def my_activity_hub(message: Message, lang: str) -> None:
    await message.answer(
        f"{t(lang, 'my_activity_title')}\n\n{t(lang, 'my_activity_intro')}",
        reply_markup=my_activity_kb(lang),
    )


@router.callback_query(F.data == "myact:bookings")
async def my_activity_bookings(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await safe_callback_answer(callback)
    from app.bot.handlers.client import my_bookings

    await my_bookings(callback.message, lang)


@router.callback_query(F.data == "myact:orders")
async def my_activity_orders(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await safe_callback_answer(callback)
    await my_orders_list(callback.message, state, lang)


@router.callback_query(F.data == "myact:back")
async def my_activity_back(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    await safe_callback_answer(callback)
    async with async_session_factory() as session:
        kwargs = await menu_mode_kwargs(session)
    await callback.message.answer(t(lang, "main_menu"), reply_markup=main_menu(is_admin, lang, **kwargs))


@router.message(F.text.in_(ORDER_SERVICES_TEXTS))
async def start_order_services(message: Message, state: FSMContext, lang: str) -> None:
    async with async_session_factory() as session:
        services = await _order_services(session)
    if not services:
        await message.answer(t(lang, "no_services"))
        return
    await state.update_data(flow_origin="client", flow_kind="order")
    await state.set_state(BookingStates.choosing_service)
    await message.answer(t(lang, "choose_service"), reply_markup=services_kb(services, lang))


@router.callback_query(F.data.startswith("cb:order:"))
async def choose_order_service(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await safe_callback_answer(callback)
    service_id = int(callback.data.rsplit(":", 1)[1])
    async with async_session_factory() as session:
        service = await ServiceRepository(session).get_by_id(service_id)
    if not is_service_bookable(service) or not is_order_service(service):
        await callback.message.answer(t(lang, client_service_unavailable_key(service)))
        return
    await state.set_state(BookingStates.choosing_service)
    await start_order_flow(callback.message, state, lang, callback.from_user, service_id, service.name)


@router.message(OrderStates.entering_details, F.text)
async def order_enter_details(message: Message, state: FSMContext, lang: str) -> None:
    details = message.text.strip()
    if not details:
        await message.answer(t(lang, "order_details_required"), reply_markup=cancel_kb(lang))
        return
    await state.update_data(order_details=details)
    await show_order_confirmation(message, state, lang)


@router.callback_query(OrderStates.confirming, F.data == "ord:confirm:yes")
async def order_confirm_submit(callback: CallbackQuery, state: FSMContext, bot: Bot, lang: str) -> None:
    await safe_callback_answer(callback)
    data = await state.get_data()
    service_id = data.get("service_id")
    if not service_id:
        await state.clear()
        await callback.message.answer(t(lang, "session_expired"))
        return
    async with async_session_factory() as session:
        order = await create_order(
            session,
            service_id=service_id,
            telegram_id=callback.from_user.id,
            client_name=data.get("client_name"),
            client_phone=data.get("client_phone"),
            client_username=callback.from_user.username,
            details=data.get("order_details"),
        )
        await session.commit()
    await state.clear()
    async with async_session_factory() as session:
        kwargs = await menu_mode_kwargs(session)
    await callback.message.answer(t(lang, "order_submitted_client"), reply_markup=main_menu(lang=lang, **kwargs))
    await notify_admins_new_order(bot, order)


@router.callback_query(OrderStates.confirming, F.data == "ord:confirm:edit")
async def order_confirm_edit(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await safe_callback_answer(callback)
    await start_order_flow(
        callback.message,
        state,
        lang,
        callback.from_user,
        (await state.get_data()).get("service_id"),
        (await state.get_data()).get("service_name", ""),
    )


async def _load_client_orders(telegram_id: int):
    async with async_session_factory() as session:
        client = await ClientRepository(session).get_by_telegram_id(telegram_id)
        if not client:
            return None, [], {}
        orders = await ServiceOrderRepository(session).list_for_client(client.id)
        names = {s.id: s.name for s in await ServiceRepository(session).list_all()}
    return client, orders, names


def _build_my_orders_hub_body(counts, lang: str) -> str:
    return "\n".join(
        [
            t(lang, "my_orders_title"),
            t(lang, "my_orders_active_count", count=str(counts.active_count)),
            t(lang, "my_orders_history_count", count=str(counts.history_count)),
            "",
            t(lang, "my_orders_choose_section"),
        ]
    )


def _build_my_orders_active_body(counts, lang: str) -> str:
    return "\n".join(
        [
            t(lang, "my_orders_active_title"),
            t(lang, "my_orders_active_new_summary", count=str(counts.new_count)),
            t(lang, "my_orders_active_accepted_summary", count=str(counts.accepted_count)),
            t(lang, "my_orders_active_in_progress_summary", count=str(counts.in_progress_count)),
        ]
    )


def _build_my_orders_history_body(counts, lang: str) -> str:
    return "\n".join(
        [
            t(lang, "my_orders_history_title"),
            t(lang, "my_orders_history_completed_summary", count=str(counts.completed_count)),
            t(lang, "my_orders_history_cancelled_summary", count=str(counts.cancelled_count)),
            t(lang, "my_orders_history_declined_summary", count=str(counts.declined_count)),
        ]
    )


async def show_my_orders_hub(event: Message | CallbackQuery, lang: str) -> None:
    user_id = event.from_user.id
    client, orders, _names = await _load_client_orders(user_id)
    if not client:
        text = t(lang, "my_orders_empty")
        if isinstance(event, CallbackQuery):
            await event.message.answer(text)
        else:
            await event.answer(text)
        return
    counts = compute_client_orders_hub_counts(orders)
    text = _build_my_orders_hub_body(counts, lang)
    keyboard = client_orders_hub_kb(counts, lang)
    if isinstance(event, CallbackQuery):
        await edit_or_send(event, text, reply_markup=keyboard)
    else:
        await event.answer(text, reply_markup=keyboard)


async def show_my_orders_active(event: Message | CallbackQuery, lang: str) -> None:
    _client, orders, names = await _load_client_orders(event.from_user.id)
    active, _history = split_client_orders(orders)
    counts = compute_client_orders_hub_counts(orders)
    active = sort_active_client_orders(active)
    if not active:
        text = t(lang, "my_orders_empty_active")
        keyboard = client_orders_empty_active_kb(counts, lang)
    else:
        text = _build_my_orders_active_body(counts, lang)
        keyboard = client_orders_active_kb(active, lang, service_names=names)
    if isinstance(event, CallbackQuery):
        await edit_or_send(event, text, reply_markup=keyboard)
    else:
        await event.answer(text, reply_markup=keyboard)


async def show_my_orders_history(event: Message | CallbackQuery, lang: str) -> None:
    _client, orders, names = await _load_client_orders(event.from_user.id)
    _active, history = split_client_orders(orders)
    counts = compute_client_orders_hub_counts(orders)
    history = sort_history_client_orders(history)
    if not history:
        text = t(lang, "my_orders_empty_history")
        keyboard = client_orders_empty_history_kb(counts, lang)
    else:
        text = _build_my_orders_history_body(counts, lang)
        keyboard = client_orders_history_kb(history, lang, service_names=names)
    if isinstance(event, CallbackQuery):
        await edit_or_send(event, text, reply_markup=keyboard)
    else:
        await event.answer(text, reply_markup=keyboard)


async def show_my_order_detail(
    event: CallbackQuery | Message,
    lang: str,
    order_id: int,
    section: str | None = None,
) -> None:
    async with async_session_factory() as session:
        order = await ServiceOrderRepository(session).get_by_id(order_id)
        service = await ServiceRepository(session).get_by_id(order.service_id) if order else None
        user_id = event.from_user.id
        client = await ClientRepository(session).get_by_telegram_id(user_id)
    if not order or not client or order.client_id != client.id:
        if isinstance(event, CallbackQuery):
            await event.message.answer(t(lang, "not_found"))
        else:
            await event.answer(t(lang, "not_found"))
        return
    resolved_section = resolve_client_order_section(section, order)
    text = f"{t(lang, 'order_detail_title')}\n\n{format_order_client(order, service, lang)}"
    keyboard = client_order_detail_kb(order.id, order.status, lang, section=resolved_section)
    if isinstance(event, CallbackQuery):
        await edit_or_send(event, text, reply_markup=keyboard)
    else:
        await event.answer(text, reply_markup=keyboard)


@router.message(F.text.in_(MY_ORDERS_TEXTS))
async def my_orders_list(message: Message, state: FSMContext, lang: str) -> None:
    if await state.get_state():
        await state.clear()
    await show_my_orders_hub(message, lang)


@router.callback_query(F.data == "myord:list")
@router.callback_query(F.data == "myord:hub")
async def my_orders_hub_callback(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    if await state.get_state():
        await state.clear()
    await safe_callback_answer(callback)
    await show_my_orders_hub(callback, lang)


@router.callback_query(F.data == "myord:active")
async def my_orders_active_callback(callback: CallbackQuery, lang: str) -> None:
    await safe_callback_answer(callback)
    await show_my_orders_active(callback, lang)


@router.callback_query(F.data == "myord:history")
async def my_orders_history_callback(callback: CallbackQuery, lang: str) -> None:
    await safe_callback_answer(callback)
    await show_my_orders_history(callback, lang)


@router.callback_query(F.data == "myord:back")
async def my_orders_back(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    await safe_callback_answer(callback)
    async with async_session_factory() as session:
        kwargs = await menu_mode_kwargs(session)
    await callback.message.answer(t(lang, "main_menu"), reply_markup=main_menu(is_admin, lang, **kwargs))


@router.callback_query(F.data.regexp(r"^myord:view:\d+(?::(active|history))?$"))
async def my_order_detail(callback: CallbackQuery, lang: str) -> None:
    await safe_callback_answer(callback)
    parts = callback.data.split(":")
    order_id = int(parts[2])
    section = parts[3] if len(parts) > 3 else None
    await show_my_order_detail(callback, lang, order_id, section)


@router.callback_query(F.data.regexp(r"^myord:msg:\d+$"))
async def my_order_message_start(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await safe_callback_answer(callback)
    order_id = int(callback.data.rsplit(":", 1)[1])
    async with async_session_factory() as session:
        order = await ServiceOrderRepository(session).get_by_id(order_id)
        client = await ClientRepository(session).get_by_telegram_id(callback.from_user.id)
    if not order or not client or order.client_id != client.id:
        await callback.message.answer(t(lang, "not_found"))
        return
    if order.status not in (
        ServiceOrderStatus.NEW.value,
        ServiceOrderStatus.ACCEPTED.value,
        ServiceOrderStatus.IN_PROGRESS.value,
    ):
        await callback.message.answer(t(lang, "not_found"))
        return
    await state.update_data(client_order_message_id=order_id, flow_origin="client")
    await state.set_state(OrderStates.entering_message)
    await callback.message.answer(t(lang, "order_message_prompt_client"), reply_markup=cancel_kb(lang))


@router.message(OrderStates.entering_message, F.text)
async def my_order_message_save(message: Message, state: FSMContext, bot: Bot, lang: str) -> None:
    data = await state.get_data()
    order_id = data.get("client_order_message_id")
    if not order_id:
        return
    text = (message.text or "").strip()
    if not text:
        await message.answer(t(lang, "order_message_prompt_client"), reply_markup=cancel_kb(lang))
        return
    async with async_session_factory() as session:
        order = await ServiceOrderRepository(session).get_by_id(order_id)
        client = await ClientRepository(session).get_by_telegram_id(message.from_user.id)
        if not order or not client or order.client_id != client.id:
            await state.clear()
            await message.answer(t(lang, "not_found"))
            return
        service = await ServiceRepository(session).get_by_id(order.service_id)
        await add_order_message(
            session,
            order_id=order_id,
            sender_type=ORDER_MESSAGE_SENDER_CLIENT,
            message_text=text,
            sender_telegram_id=message.from_user.id,
        )
        await session.commit()
    await state.clear()
    await notify_admins_order_message(bot, order, service, text)
    await message.answer(t(lang, "order_message_sent_client"))


@router.callback_query(F.data.regexp(r"^myord:history:\d+(?::(active|history))?$"))
async def my_order_history(callback: CallbackQuery, lang: str) -> None:
    await safe_callback_answer(callback)
    parts = callback.data.split(":")
    order_id = int(parts[2])
    section = parts[3] if len(parts) > 3 else "hub"
    async with async_session_factory() as session:
        order = await ServiceOrderRepository(session).get_by_id(order_id)
        client = await ClientRepository(session).get_by_telegram_id(callback.from_user.id)
        if not order or not client or order.client_id != client.id:
            await callback.message.answer(t(lang, "not_found"))
            return
        text = await build_order_history_text(session, order_id, lang)
    resolved_section = resolve_client_order_section(section, order)
    await edit_or_send(
        callback,
        text,
        reply_markup=client_order_history_kb(order_id, resolved_section, lang),
    )


@router.callback_query(F.data.regexp(r"^myord:cancel:\d+(?::(active|history))?$"))
async def my_order_cancel(callback: CallbackQuery, lang: str) -> None:
    await safe_callback_answer(callback)
    parts = callback.data.split(":")
    order_id = int(parts[2])
    section = parts[3] if len(parts) > 3 else None
    async with async_session_factory() as session:
        order = await ServiceOrderRepository(session).get_by_id(order_id)
        client = await ClientRepository(session).get_by_telegram_id(callback.from_user.id)
        if not order or not client or order.client_id != client.id:
            await callback.message.answer(t(lang, "not_found"))
            return
        if order.status not in (
            ServiceOrderStatus.NEW.value,
            ServiceOrderStatus.ACCEPTED.value,
            ServiceOrderStatus.IN_PROGRESS.value,
        ):
            await callback.message.answer(t(lang, "not_found"))
            return
        await cancel_order(session, order_id)
        await session.commit()
        order = await ServiceOrderRepository(session).get_by_id(order_id)
        service = await ServiceRepository(session).get_by_id(order.service_id)
    await notify_admins_order_cancelled_by_client(callback.bot, order, service)
    await show_my_order_detail(callback, lang, order_id, section)
