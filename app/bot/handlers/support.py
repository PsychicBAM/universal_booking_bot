import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from app.bot.i18n import t
from app.bot.keyboards import CONTACT_ADMIN_TEXTS, admin_menu, cancel_kb, main_menu
from app.bot.keyboards.support_kb import (
    format_request_list_label,
    support_booking_pick_kb,
    support_main_menu_kb,
    support_message_nav_kb,
    support_new_topics_kb,
    support_request_detail_kb,
    support_requests_list_kb,
)
from app.bot.states import AdminSupportStates, ClientSupportStates
from app.bot.utils.callbacks import safe_callback_answer
from app.config import get_settings
from app.database.session import async_session_factory
from app.models import SupportMessageStatus
from app.repositories import BookingRepository, ClientRepository, SupportMessageRepository
from app.services.support_service import (
    BOOKING_PICK_TOPICS,
    create_support_message,
    format_message_prompt,
    format_request_detail,
    get_user_language,
    notify_admins_new_support,
    topic_label,
    validate_support_text,
)

router = Router()
logger = logging.getLogger(__name__)


def _support_menu_text(lang: str) -> str:
    return f"{t(lang, 'support_menu_title')}\n{t(lang, 'support_menu_text')}"


async def _edit_or_answer(
    target: Message | CallbackQuery,
    text: str,
    reply_markup=None,
    *,
    edit: bool = False,
) -> None:
    if isinstance(target, CallbackQuery):
        await safe_callback_answer(target)
        if edit:
            try:
                await target.message.edit_text(text, reply_markup=reply_markup)
                return
            except TelegramBadRequest:
                pass
        await target.message.answer(text, reply_markup=reply_markup)
    else:
        await target.answer(text, reply_markup=reply_markup)


async def show_support_menu(target: Message | CallbackQuery, lang: str, *, edit: bool = False) -> None:
    await _edit_or_answer(
        target,
        _support_menu_text(lang),
        reply_markup=support_main_menu_kb(lang),
        edit=edit,
    )


async def show_topic_selection(target: Message | CallbackQuery, lang: str, *, edit: bool = False) -> None:
    await _edit_or_answer(
        target,
        t(lang, "support_choose_topic"),
        reply_markup=support_new_topics_kb(lang),
        edit=edit,
    )


async def _list_client_bookings(user_id: int):
    async with async_session_factory() as session:
        client = await ClientRepository(session).get_by_telegram_id(user_id)
        if not client:
            return []
        return await BookingRepository(session).list_for_client(client.id)


async def show_my_requests(
    target: Message | CallbackQuery, user_id: int, lang: str, *, edit: bool = False
) -> None:
    async with async_session_factory() as session:
        requests = await SupportMessageRepository(session).list_for_client_telegram(user_id)
    if not requests:
        await _edit_or_answer(
            target,
            f"{t(lang, 'support_my_requests')}\n\n{t(lang, 'support_my_requests_empty')}",
            reply_markup=support_main_menu_kb(lang),
            edit=edit,
        )
        return
    lines = [format_request_list_label(request, lang) for request in requests]
    text = f"{t(lang, 'support_my_requests')}\n\n" + "\n".join(f"• {line}" for line in lines)
    await _edit_or_answer(
        target,
        text,
        reply_markup=support_requests_list_kb(requests, lang),
        edit=edit,
    )


async def show_request_detail(
    target: Message | CallbackQuery, request_id: int, user_id: int, lang: str, *, edit: bool = False
) -> None:
    async with async_session_factory() as session:
        repo = SupportMessageRepository(session)
        request = await repo.get_by_id(request_id)
        if not request or request.client_telegram_id != user_id:
            if isinstance(target, CallbackQuery):
                await safe_callback_answer(target, t(lang, "not_found"), show_alert=True)
            else:
                await target.answer(t(lang, "not_found"))
            return
        booking = None
        if request.booking_id:
            booking = await BookingRepository(session).get_by_id(request.booking_id)
    await _edit_or_answer(
        target,
        format_request_detail(request, lang, booking),
        reply_markup=support_request_detail_kb(lang),
        edit=edit,
    )


async def _start_message_prompt(
    target: Message | CallbackQuery, state: FSMContext, lang: str, topic: str
) -> None:
    await state.set_state(ClientSupportStates.entering_message)
    text = format_message_prompt(lang, topic)
    if isinstance(target, CallbackQuery):
        await safe_callback_answer(target)
        try:
            await target.message.edit_reply_markup(reply_markup=None)
        except TelegramBadRequest:
            pass
        await target.message.answer(text, reply_markup=support_message_nav_kb(lang))
    else:
        await target.answer(text, reply_markup=support_message_nav_kb(lang))


async def _start_topic_flow(
    target: Message | CallbackQuery,
    state: FSMContext,
    lang: str,
    topic: str,
    origin: str,
    user_id: int,
) -> None:
    await state.update_data(support_topic=topic, support_origin=origin, support_booking_id=None)
    if topic in BOOKING_PICK_TOPICS:
        bookings = await _list_client_bookings(user_id)
        if bookings:
            await state.set_state(ClientSupportStates.choosing_booking)
            await _edit_or_answer(
                target,
                f"{topic_label(lang, topic)}\n\n{t(lang, 'support_choose_booking')}",
                reply_markup=support_booking_pick_kb(bookings, lang),
                edit=isinstance(target, CallbackQuery),
            )
            return
    await _start_message_prompt(target, state, lang, topic)


@router.message(F.text.in_(CONTACT_ADMIN_TEXTS))
async def contact_admin_start(
    message: Message, state: FSMContext, is_admin: bool, lang: str
) -> None:
    await state.clear()
    await state.update_data(flow_origin="client")
    await show_support_menu(message, lang)


@router.callback_query(F.data == "sup:menu")
async def support_menu_callback(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await state.set_state(None)
    await show_support_menu(callback, lang, edit=True)


@router.callback_query(F.data == "sup:back:main")
async def support_back_main(
    callback: CallbackQuery, state: FSMContext, is_admin: bool, lang: str
) -> None:
    await state.clear()
    await safe_callback_answer(callback)
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass
    await callback.message.answer(t(lang, "main_menu"), reply_markup=main_menu(is_admin, lang))


@router.callback_query(F.data == "sup:back:menu")
async def support_back_menu(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await state.set_state(None)
    await state.update_data(support_origin="main")
    await show_support_menu(callback, lang, edit=True)


@router.callback_query(F.data == "sup:new")
async def support_new_request(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await state.update_data(support_origin="new")
    await show_topic_selection(callback, lang, edit=True)


@router.callback_query(F.data == "sup:my")
async def support_my_requests(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await state.set_state(None)
    await show_my_requests(callback, callback.from_user.id, lang, edit=True)


@router.callback_query(F.data == "sup:back:my")
async def support_back_my_requests(callback: CallbackQuery, lang: str) -> None:
    await show_my_requests(callback, callback.from_user.id, lang, edit=True)


@router.callback_query(F.data.regexp(r"^sup:req:\d+$"))
async def support_view_request(callback: CallbackQuery, lang: str) -> None:
    request_id = int(callback.data.split(":")[-1])
    await show_request_detail(callback, request_id, callback.from_user.id, lang, edit=True)


@router.callback_query(F.data.regexp(r"^sup:topic:(booking|reschedule|cancel|payment|other)$"))
async def support_select_topic(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    topic = callback.data.split(":")[-1]
    data = await state.get_data()
    origin = data.get("support_origin") or "main"
    await _start_topic_flow(callback, state, lang, topic, origin, callback.from_user.id)


@router.callback_query(F.data == "sup:back:topic")
async def support_back_topic(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    data = await state.get_data()
    origin = data.get("support_origin", "main")
    await state.set_state(None)
    if origin == "new":
        await show_topic_selection(callback, lang, edit=True)
    else:
        await show_support_menu(callback, lang, edit=True)


@router.callback_query(F.data == "sup:back:prompt")
async def support_back_prompt(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    data = await state.get_data()
    topic = data.get("support_topic")
    origin = data.get("support_origin", "main")
    if topic in BOOKING_PICK_TOPICS:
        bookings = await _list_client_bookings(callback.from_user.id)
        if bookings:
            await state.set_state(ClientSupportStates.choosing_booking)
            await state.update_data(support_booking_id=None)
            await _edit_or_answer(
                callback,
                f"{topic_label(lang, topic)}\n\n{t(lang, 'support_choose_booking')}",
                reply_markup=support_booking_pick_kb(bookings, lang),
                edit=True,
            )
            return

    await state.set_state(None)
    if origin == "new":
        await show_topic_selection(callback, lang, edit=True)
    else:
        await show_support_menu(callback, lang, edit=True)


@router.callback_query(F.data.regexp(r"^sup:book:\d+$"))
async def support_pick_booking(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    booking_id = int(callback.data.split(":")[-1])
    async with async_session_factory() as session:
        client = await ClientRepository(session).get_by_telegram_id(callback.from_user.id)
        booking = await BookingRepository(session).get_by_id(booking_id)
        if not client or not booking or booking.client_id != client.id:
            await safe_callback_answer(callback, t(lang, "not_found"), show_alert=True)
            return
    data = await state.get_data()
    topic = data.get("support_topic", "booking")
    await state.update_data(support_booking_id=booking_id)
    await _start_message_prompt(callback, state, lang, topic)


@router.callback_query(F.data == "sup:book:skip")
async def support_skip_booking(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    data = await state.get_data()
    topic = data.get("support_topic", "booking")
    await state.update_data(support_booking_id=None)
    await _start_message_prompt(callback, state, lang, topic)


@router.message(ClientSupportStates.entering_message, F.text)
async def client_send_support_message(
    message: Message, state: FSMContext, bot: Bot, is_admin: bool, lang: str
) -> None:
    error_key = validate_support_text(message.text or "")
    if error_key:
        await message.answer(t(lang, error_key))
        return

    settings = get_settings()
    if not settings.admin_ids:
        await state.clear()
        await message.answer(
            t(lang, "support_no_admin"),
            reply_markup=ReplyKeyboardRemove(),
        )
        await message.answer(t(lang, "main_menu"), reply_markup=main_menu(is_admin, lang))
        return

    data = await state.get_data()
    client_name = (message.from_user.full_name or message.from_user.username or "—").strip()
    client_username = message.from_user.username

    async with async_session_factory() as session:
        await ClientRepository(session).get_or_create(message.from_user.id, client_name)
        support_msg = await create_support_message(
            session,
            client_telegram_id=message.from_user.id,
            client_name=client_name,
            client_username=client_username,
            message_text=message.text.strip(),
            topic=data.get("support_topic"),
            booking_id=data.get("support_booking_id"),
        )
        await session.commit()
        sent = await notify_admins_new_support(bot, session, support_msg)

    await state.clear()
    if not sent:
        logger.error("Support message id=%s created but admin notify failed", support_msg.id)
        await message.answer(t(lang, "support_send_failed"), reply_markup=main_menu(is_admin, lang))
        return

    await message.answer(t(lang, "support_request_sent"), reply_markup=main_menu(is_admin, lang))


@router.callback_query(F.data.regexp(r"^sup:reply:\d+$"))
async def admin_support_reply_start(
    callback: CallbackQuery, state: FSMContext, is_admin: bool, lang: str
) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return

    message_id = int(callback.data.split(":")[-1])
    async with async_session_factory() as session:
        support_msg = await SupportMessageRepository(session).get_by_id(message_id)

    if not support_msg or support_msg.status == SupportMessageStatus.CLOSED:
        await safe_callback_answer(callback, t(lang, "not_found"), show_alert=True)
        return

    await safe_callback_answer(callback)
    await state.update_data(flow_origin="admin_support", support_message_id=message_id)
    await state.set_state(AdminSupportStates.entering_reply)
    await callback.message.answer(t(lang, "support_reply_prompt"), reply_markup=cancel_kb(lang))


@router.message(AdminSupportStates.entering_reply, F.text)
async def admin_support_send_reply(
    message: Message, state: FSMContext, bot: Bot, is_admin: bool, lang: str
) -> None:
    if not is_admin:
        return

    error_key = validate_support_text(message.text or "")
    if error_key:
        await message.answer(t(lang, error_key))
        return

    data = await state.get_data()
    message_id = data.get("support_message_id")
    if not message_id:
        await state.clear()
        await message.answer(t(lang, "not_found"), reply_markup=admin_menu(lang))
        return

    async with async_session_factory() as session:
        repo = SupportMessageRepository(session)
        support_msg = await repo.get_by_id(int(message_id))
        if not support_msg or support_msg.status == SupportMessageStatus.CLOSED:
            await state.clear()
            await message.answer(t(lang, "not_found"), reply_markup=admin_menu(lang))
            return

        client_lang = await get_user_language(session, support_msg.client_telegram_id)
        try:
            await bot.send_message(
                support_msg.client_telegram_id,
                t(client_lang, "support_admin_reply", text=message.text.strip()),
            )
        except Exception:
            logger.exception(
                "Failed to send support reply to client_id=%s message_id=%s",
                support_msg.client_telegram_id,
                support_msg.id,
            )
            await message.answer(t(lang, "support_reply_failed"))
            return

        await repo.mark_replied(support_msg, message.from_user.id, message.text.strip())
        await session.commit()

    await state.clear()
    await message.answer(t(lang, "support_reply_sent"), reply_markup=admin_menu(lang))


@router.callback_query(F.data.regexp(r"^sup:close:\d+$"))
async def admin_support_close(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return

    message_id = int(callback.data.split(":")[-1])
    async with async_session_factory() as session:
        repo = SupportMessageRepository(session)
        support_msg = await repo.get_by_id(message_id)
        if not support_msg:
            await safe_callback_answer(callback, t(lang, "not_found"), show_alert=True)
            return
        if support_msg.status != SupportMessageStatus.CLOSED:
            await repo.mark_closed(support_msg)
            await session.commit()

    await safe_callback_answer(callback, t(lang, "support_closed"))
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
