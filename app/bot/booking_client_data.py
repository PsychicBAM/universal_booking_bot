from __future__ import annotations

from aiogram.types import Message, ReplyKeyboardRemove, User

from app.bot.i18n import t
from app.bot.keyboards import cancel_kb, skip_cancel_kb
from app.bot.keyboards.client_data_kb import (
    confirm_telegram_name_kb,
    request_contact_reply_kb,
    saved_phone_kb,
)
from app.bot.states import BookingStates
from app.database.session import async_session_factory
from app.models import Booking, Client
from app.repositories import BookingRepository, ClientRepository
from app.services.client_data_service import (
    ClientDataSettings,
    build_telegram_full_name,
    can_fast_reuse_saved_data,
    load_client_data_settings,
    missing_client_data_fields,
    resolve_saved_client_name,
    resolve_saved_client_phone,
    validate_client_name,
    validate_manual_phone,
)


async def load_settings() -> ClientDataSettings:
    async with async_session_factory() as session:
        return await load_client_data_settings(session)


async def get_client(user_id: int) -> Client | None:
    async with async_session_factory() as session:
        return await ClientRepository(session).get_by_telegram_id(user_id)


async def get_client_booking_context(user_id: int) -> tuple[Client | None, Booking | None]:
    async with async_session_factory() as session:
        client = await ClientRepository(session).get_by_telegram_id(user_id)
        if not client:
            return None, None
        latest = await BookingRepository(session).get_latest_for_client(client.id)
        return client, latest


async def continue_booking_after_time(
    message: Message,
    state,
    lang: str,
    user: User,
) -> None:
    settings = await load_settings()
    client, latest_booking = await get_client_booking_context(user.id)

    if can_fast_reuse_saved_data(client, latest_booking, user, settings):
        name = resolve_saved_client_name(client, latest_booking, user, settings)
        phone = resolve_saved_client_phone(client, latest_booking)
        await state.update_data(client_name=name, client_phone=phone)
        await continue_after_phone(message, state, lang)
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
        if not settings.phone_required:
            await state.update_data(client_phone=phone)
        await continue_after_phone(message, state, lang)
        return

    if need_name:
        await begin_name_collection(message, state, lang, user, settings)
        return

    await begin_phone_step(message, state, lang, user.id, settings)


async def begin_name_collection(
    message: Message,
    state,
    lang: str,
    user: User,
    settings: ClientDataSettings | None = None,
) -> None:
    if settings is None:
        settings = await load_settings()
    telegram_name = build_telegram_full_name(user) if settings.use_telegram_name else None
    if telegram_name:
        if settings.confirm_telegram_name:
            await state.set_state(BookingStates.confirming_telegram_name)
            await message.answer(
                t(lang, "booking_use_telegram_name_prompt", telegram_full_name=telegram_name),
                reply_markup=confirm_telegram_name_kb(lang),
            )
            return
        await state.update_data(client_name=telegram_name)
        await begin_phone_step(message, state, lang, user.id, settings)
        return
    await state.set_state(BookingStates.entering_name)
    await message.answer(t(lang, "enter_name"), reply_markup=cancel_kb(lang))


async def begin_client_data_collection(
    message: Message,
    state,
    lang: str,
    user: User,
) -> None:
    data = await state.get_data()
    if data.get("client_name"):
        settings = await load_settings()
        await begin_phone_step(message, state, lang, user.id, settings)
        return
    await continue_booking_after_time(message, state, lang, user)


async def begin_phone_step(
    message: Message,
    state,
    lang: str,
    user_id: int,
    settings: ClientDataSettings | None = None,
) -> None:
    if settings is None:
        settings = await load_settings()
    data = await state.get_data()
    if data.get("client_phone"):
        await continue_after_phone(message, state, lang)
        return
    if not settings.phone_required and data.get("client_phone") is None and "client_phone" in data:
        await continue_after_phone(message, state, lang)
        return

    client = await get_client(user_id)
    if client and client.phone and not data.get("client_phone"):
        await state.set_state(BookingStates.choosing_phone_method)
        await message.answer(
            t(lang, "booking_saved_phone_prompt", phone=client.phone),
            reply_markup=saved_phone_kb(
                lang,
                request_contact_enabled=settings.phone_request_contact,
                manual_enabled=settings.phone_manual_input,
                phone_required=settings.phone_required,
            ),
        )
        return
    await show_phone_collection(message, state, lang, settings)


async def show_phone_collection(
    message: Message,
    state,
    lang: str,
    settings: ClientDataSettings,
) -> None:
    await state.set_state(BookingStates.choosing_phone_method)
    if settings.phone_request_contact:
        await message.answer(
            t(lang, "booking_contact_prompt"),
            reply_markup=request_contact_reply_kb(
                lang,
                manual_enabled=settings.phone_manual_input,
                phone_required=settings.phone_required,
            ),
        )
        return
    if settings.phone_manual_input:
        await state.set_state(BookingStates.entering_phone_manual)
        await message.answer(t(lang, "booking_manual_phone_prompt"), reply_markup=cancel_kb(lang))
        return
    if not settings.phone_required:
        await state.update_data(client_phone=None)
        await continue_after_phone(message, state, lang)
        return
    await message.answer(t(lang, "booking_manual_phone_prompt"), reply_markup=cancel_kb(lang))


async def apply_phone_and_continue(
    message: Message,
    state,
    lang: str,
    phone: str | None,
) -> None:
    if phone:
        async with async_session_factory() as session:
            await ClientRepository(session).set_phone(message.from_user.id, phone, source="manual")
            await session.commit()
        await state.update_data(client_phone=phone.strip())
    else:
        await state.update_data(client_phone=None)
    data = await state.get_data()
    if data.get("editing_from_confirm"):
        await state.update_data(editing_from_confirm=False)
        await return_to_confirmation(message, state, lang)
        return
    await continue_after_phone(message, state, lang, phone_ack=True)


async def save_contact_and_continue(message: Message, state, lang: str, phone: str) -> None:
    async with async_session_factory() as session:
        await ClientRepository(session).set_phone(
            message.from_user.id, phone, source="telegram_contact"
        )
        await session.commit()
    await state.update_data(client_phone=phone)
    data = await state.get_data()
    if data.get("editing_from_confirm"):
        await state.update_data(editing_from_confirm=False)
        await return_to_confirmation(message, state, lang)
        return
    await continue_after_phone(message, state, lang, phone_ack=True)


async def continue_after_phone(
    message: Message,
    state,
    lang: str,
    *,
    phone_ack: bool = False,
) -> None:
    from app.bot.handlers.client import _show_confirmation

    data = await state.get_data()
    ack = f"{t(lang, 'booking_phone_received')}\n\n" if phone_ack else ""
    if data.get("requires_location") and not data.get("location_text"):
        await state.set_state(BookingStates.entering_location)
        await message.answer(f"{ack}{t(lang, 'enter_location')}", reply_markup=cancel_kb(lang))
        return
    if data.get("ask_client_comment") and data.get("client_comment") is None and not _comment_skipped(data):
        await state.set_state(BookingStates.entering_comment)
        await message.answer(
            f"{ack}{t(lang, 'ask_comment_prompt')}\n{t(lang, 'comment_optional_hint')}",
            reply_markup=skip_cancel_kb(lang),
        )
        return
    if phone_ack:
        await message.answer(t(lang, "booking_phone_received"), reply_markup=ReplyKeyboardRemove())
    await _show_confirmation(message, state, lang)


def _comment_skipped(data: dict) -> bool:
    return "client_comment" in data and data.get("client_comment") is None


async def return_to_confirmation(message: Message, state, lang: str) -> None:
    from app.bot.handlers.client import _show_confirmation

    await _show_confirmation(message, state, lang)


async def handle_manual_name(message: Message, state, lang: str) -> bool:
    name = message.text.strip()
    if not validate_client_name(name):
        await message.answer(t(lang, "enter_name"), reply_markup=cancel_kb(lang))
        return False
    await state.update_data(client_name=name)
    async with async_session_factory() as session:
        await ClientRepository(session).set_display_name(message.from_user.id, name)
        await session.commit()
    data = await state.get_data()
    if data.get("editing_from_confirm"):
        await state.update_data(editing_from_confirm=False)
        await return_to_confirmation(message, state, lang)
        return True
    await begin_phone_step(message, state, lang, message.from_user.id)
    return True


async def handle_manual_phone_text(message: Message, state, lang: str) -> bool:
    settings = await load_settings()
    phone = message.text.strip()
    if message.text.strip() == t(lang, "booking_skip_phone") and not settings.phone_required:
        await state.update_data(client_phone=None)
        data = await state.get_data()
        if data.get("editing_from_confirm"):
            await state.update_data(editing_from_confirm=False)
            await return_to_confirmation(message, state, lang)
            return True
        await continue_after_phone(message, state, lang, phone_ack=True)
        return True
    if not validate_manual_phone(phone, required=settings.phone_required):
        await message.answer(t(lang, "booking_manual_phone_prompt"), reply_markup=cancel_kb(lang))
        return False
    await apply_phone_and_continue(message, state, lang, phone)
    return True


async def handle_contact_message(message: Message, state, lang: str) -> bool:
    contact = message.contact
    if not contact or contact.user_id != message.from_user.id:
        await message.answer(t(lang, "booking_wrong_contact"))
        return False
    phone = contact.phone_number
    if not phone:
        await message.answer(t(lang, "booking_wrong_contact"))
        return False
    await save_contact_and_continue(message, state, lang, phone)
    return True


async def handle_phone_method_text(message: Message, state, lang: str) -> bool:
    settings = await load_settings()
    text = message.text.strip()
    if text == t(lang, "booking_enter_phone_manual"):
        await state.set_state(BookingStates.entering_phone_manual)
        await message.answer(t(lang, "booking_manual_phone_prompt"), reply_markup=cancel_kb(lang))
        return True
    if text == t(lang, "booking_skip_phone") and not settings.phone_required:
        await state.update_data(client_phone=None)
        data = await state.get_data()
        if data.get("editing_from_confirm"):
            await state.update_data(editing_from_confirm=False)
            await return_to_confirmation(message, state, lang)
            return True
        await continue_after_phone(message, state, lang, phone_ack=True)
        return True
    return False


async def begin_phone_edit(message: Message, state, lang: str, user_id: int) -> None:
    settings = await load_settings()
    await show_phone_collection(message, state, lang, settings)
