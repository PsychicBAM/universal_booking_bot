from aiogram.types import Message, ReplyKeyboardRemove

from app.bot.i18n import t
from app.bot.keyboards import cancel_kb
from app.bot.keyboards.orders_kb import order_confirm_kb
from app.bot.states import OrderStates
from app.bot.booking_client_data import begin_name_collection, load_settings
from app.models import SERVICE_TYPE_ORDER
from app.services.client_data_service import (
    can_fast_reuse_saved_data,
    missing_client_data_fields,
    resolve_saved_client_name,
    resolve_saved_client_phone,
)
from app.bot.booking_client_data import get_client_booking_context


async def start_order_flow(message: Message, state, lang: str, user, service_id: int, service_name: str) -> None:
    await state.update_data(
        flow_kind="order",
        flow_origin="client",
        service_id=service_id,
        service_name=service_name,
    )
    settings = await load_settings()
    client, latest_booking = await get_client_booking_context(user.id)

    if can_fast_reuse_saved_data(client, latest_booking, user, settings):
        name = resolve_saved_client_name(client, latest_booking, user, settings)
        phone = resolve_saved_client_phone(client, latest_booking)
        await state.update_data(client_name=name, client_phone=phone)
        await _ask_order_details(message, state, lang)
        return

    name = resolve_saved_client_name(client, latest_booking, user, settings)
    phone = resolve_saved_client_phone(client, latest_booking)
    need_name, need_phone = missing_client_data_fields(client, latest_booking, user, settings)
    updates: dict = {}
    if name:
        updates["client_name"] = name
    if phone:
        updates["client_phone"] = phone
    if updates:
        await state.update_data(**updates)
    if not need_name and not need_phone:
        await _ask_order_details(message, state, lang)
        return
    if need_name:
        await begin_name_collection(message, state, lang, user, settings)
        return
    from app.bot.booking_client_data import begin_phone_step

    await begin_phone_step(message, state, lang, user.id, settings)


async def continue_order_after_phone(message: Message, state, lang: str, *, phone_ack: bool = False) -> None:
    ack = f"{t(lang, 'booking_phone_received')}\n\n" if phone_ack else ""
    if phone_ack:
        await message.answer(t(lang, "booking_phone_received"), reply_markup=ReplyKeyboardRemove())
    await _ask_order_details(message, state, lang, prefix=ack)


async def _ask_order_details(message: Message, state, lang: str, *, prefix: str = "") -> None:
    await state.set_state(OrderStates.entering_details)
    await message.answer(f"{prefix}{t(lang, 'order_details_prompt')}", reply_markup=cancel_kb(lang))


async def show_order_confirmation(message: Message, state, lang: str) -> None:
    data = await state.get_data()
    lines = [
        t(lang, "order_confirm_title"),
        "",
        f"{t(lang, 'label_service')}: {data.get('service_name', '')}",
        f"{t(lang, 'label_name')}: {data.get('client_name', '')}",
        f"{t(lang, 'label_phone')}: {data.get('client_phone') or t(lang, 'not_provided')}",
        "",
        t(lang, "order_details_label"),
        data.get("order_details", ""),
    ]
    await state.set_state(OrderStates.confirming)
    await message.answer("\n".join(lines), reply_markup=order_confirm_kb(lang))
