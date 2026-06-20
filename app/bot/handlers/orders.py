import logging

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.i18n import t
from app.bot.keyboards import (
    MY_ORDERS_TEXTS,
    ORDER_SERVICES_TEXTS,
    cancel_kb,
    main_menu,
    services_kb,
)
from app.bot.keyboards.orders_kb import client_order_detail_kb, client_orders_kb
from app.bot.order_client_data import show_order_confirmation, start_order_flow
from app.bot.states import BookingStates, OrderStates
from app.bot.utils.callbacks import safe_callback_answer
from app.bot.utils.menu_helpers import menu_mode_kwargs
from app.bot.utils.service_helpers import client_service_unavailable_key, is_order_service, is_service_bookable
from app.bot.utils.telegram_ui import edit_or_send
from app.database.session import async_session_factory
from app.models import SERVICE_TYPE_ORDER, ServiceOrderStatus
from app.repositories import ClientRepository, ServiceOrderRepository, ServiceRepository
from app.services.order_service import cancel_order, create_order, notify_admins_new_order
from app.utils.formatting import format_order_client

router = Router()
logger = logging.getLogger(__name__)


async def _order_services(session):
    return await ServiceRepository(session).list_client_services(service_type=SERVICE_TYPE_ORDER)


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


@router.message(F.text.in_(MY_ORDERS_TEXTS))
async def my_orders_list(message: Message, state: FSMContext, lang: str) -> None:
    if await state.get_state():
        await state.clear()
    async with async_session_factory() as session:
        client = await ClientRepository(session).get_by_telegram_id(message.from_user.id)
        if not client:
            await message.answer(t(lang, "my_orders_empty"))
            return
        orders = await ServiceOrderRepository(session).list_for_client(client.id)
        names = {
            s.id: s.name
            for s in await ServiceRepository(session).list_all()
        }
    if not orders:
        await message.answer(t(lang, "my_orders_empty"))
        return
    from app.bot.utils.order_labels import format_client_order_button

    lines = [t(lang, "my_orders_title"), ""]
    for o in orders[:15]:
        lines.append(format_client_order_button(o, lang, service_name=names.get(o.service_id)))
    await message.answer("\n".join(lines), reply_markup=client_orders_kb(orders[:15], lang))


@router.callback_query(F.data == "myord:list")
async def my_orders_callback(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await safe_callback_answer(callback)
    await my_orders_list(callback.message, state, lang)


@router.callback_query(F.data.regexp(r"^myord:view:\d+$"))
async def my_order_detail(callback: CallbackQuery, lang: str) -> None:
    await safe_callback_answer(callback)
    order_id = int(callback.data.rsplit(":", 1)[1])
    async with async_session_factory() as session:
        order = await ServiceOrderRepository(session).get_by_id(order_id)
        service = await ServiceRepository(session).get_by_id(order.service_id) if order else None
        client = await ClientRepository(session).get_by_telegram_id(callback.from_user.id)
    if not order or not client or order.client_id != client.id:
        await callback.message.answer(t(lang, "not_found"))
        return
    await edit_or_send(
        callback,
        f"{t(lang, 'order_detail_title')}\n\n{format_order_client(order, service, lang)}",
        reply_markup=client_order_detail_kb(order.id, order.status, lang),
    )


@router.callback_query(F.data.regexp(r"^myord:cancel:\d+$"))
async def my_order_cancel(callback: CallbackQuery, lang: str) -> None:
    await safe_callback_answer(callback)
    order_id = int(callback.data.rsplit(":", 1)[1])
    async with async_session_factory() as session:
        order = await ServiceOrderRepository(session).get_by_id(order_id)
        client = await ClientRepository(session).get_by_telegram_id(callback.from_user.id)
        if not order or not client or order.client_id != client.id:
            await callback.message.answer(t(lang, "not_found"))
            return
        if order.status not in (ServiceOrderStatus.NEW.value, ServiceOrderStatus.IN_PROGRESS.value):
            await callback.message.answer(t(lang, "not_found"))
            return
        await cancel_order(session, order_id)
        await session.commit()
        order = await ServiceOrderRepository(session).get_by_id(order_id)
        service = await ServiceRepository(session).get_by_id(order.service_id)
    await edit_or_send(
        callback,
        f"{t(lang, 'order_detail_title')}\n\n{format_order_client(order, service, lang)}",
        reply_markup=client_order_detail_kb(order.id, order.status, lang),
    )
