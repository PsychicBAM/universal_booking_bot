from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from app.bot.utils.callbacks import safe_callback_answer

from app.bot.i18n import CANCEL_TEXTS, t
from app.bot.keyboards import main_menu
from app.bot.utils.menu_helpers import menu_mode_kwargs, show_admin_panel
from app.database.session import async_session_factory
from app.bot.keyboards.attendance_kb import attendance_action_kb
from app.bot.settings_ui import send_settings_main_after_cancel
from app.bot.states import (
    AdminServiceLocationStates,
    AdminServiceMediaStates,
    AdminStartScreenStates,
    AdminConfirmationTextStates,
    AdminClientSearchStates,
    AdminBookingSearchStates,
    AdminOrderStates,
    AdminSupportStates,
    AdminUnavailableStates,
    AdminWorkingHoursStates,
    OrderStates,
    WorkingBreakStates,
    AttendanceStates,
    ClientBookingEditStates,
    ClientSupportStates,
)

router = Router()

ADMIN_STATE_PREFIXES = (
    "AdminServiceStates",
    "AdminServiceMediaStates",
    "AdminServiceLocationStates",
    "AdminWorkingHoursStates",
    "OrderStates",
    "WorkingBreakStates",
    "AdminUnavailableStates",
    "AdminMessageStates",
    "AdminSettingsStates",
    "AdminStartScreenStates",
    "AdminConfirmationTextStates",
    "AdminSupportStates",
)


def is_admin_state(state: str | None) -> bool:
    if not state:
        return False
    return any(state.startswith(prefix) for prefix in ADMIN_STATE_PREFIXES)


async def cancel_destination(state: FSMContext, is_admin: bool) -> str:
    data = await state.get_data()
    flow_origin = data.get("flow_origin")
    current = await state.get_state()
    if flow_origin == "admin":
        return "admin"
    if flow_origin == "client":
        return "client"
    if is_admin and is_admin_state(current):
        return "admin"
    return "client"


async def _send_cancel_destination(message: Message, destination: str, is_admin: bool, lang: str) -> None:
    if destination == "admin":
        await show_admin_panel(message, lang)
    else:
        async with async_session_factory() as session:
            kwargs = await menu_mode_kwargs(session)
        await message.answer(t(lang, "main_menu"), reply_markup=main_menu(is_admin, lang, **kwargs))


@router.message(F.text.in_(CANCEL_TEXTS))
async def global_cancel(message: Message, state: FSMContext, is_admin: bool, lang: str) -> None:
    current = await state.get_state()

    if current is None:
        await message.answer(t(lang, "cancelled"), reply_markup=ReplyKeyboardRemove())
        await message.answer(t(lang, "main_menu"), reply_markup=main_menu(is_admin, lang))
        return

    if current == AdminWorkingHoursStates.manual_time.state:
        await state.clear()
        await message.answer(t(lang, "cancelled"), reply_markup=ReplyKeyboardRemove())
        from app.bot.handlers.working_hours import send_working_hours_main

        await send_working_hours_main(message, lang)
        return

    if current and current.startswith("OrderStates"):
        data = await state.get_data()
        order_id = data.get("client_order_message_id") or data.get("order_note_id")
        flow_origin = data.get("flow_origin")
        await state.clear()
        await message.answer(t(lang, "cancelled"), reply_markup=ReplyKeyboardRemove())
        if is_admin or flow_origin == "admin":
            await show_admin_panel(message, lang)
            return
        if order_id:
            from app.bot.handlers.orders import show_my_order_detail

            await show_my_order_detail(message, lang, order_id)
            return
        from app.bot.utils.menu_helpers import menu_mode_kwargs
        from app.database.session import async_session_factory

        async with async_session_factory() as session:
            kwargs = await menu_mode_kwargs(session)
        await message.answer(t(lang, "main_menu"), reply_markup=main_menu(is_admin, lang, **kwargs))
        return

    if current.startswith("AdminOrderStates"):
        data = await state.get_data()
        order_id = data.get("order_decline_id")
        await state.clear()
        await message.answer(t(lang, "cancelled"), reply_markup=ReplyKeyboardRemove())
        if order_id:
            from app.bot.handlers.admin_orders import show_admin_order_detail

            await show_admin_order_detail(message, lang, order_id, "new", 0)
            return
        from app.bot.handlers.admin_orders import show_orders_hub

        await show_orders_hub(message, lang)
        return

    if current and current.startswith("WorkingBreakStates"):
        data = await state.get_data()
        weekday = data.get("br_weekday")
        break_id = data.get("br_break_id")
        await state.clear()
        await message.answer(t(lang, "cancelled"), reply_markup=ReplyKeyboardRemove())
        from app.bot.handlers.working_hours import send_day_detail_message, send_working_hours_main
        from app.database.session import async_session_factory
        from app.repositories import WorkingBreakRepository

        if break_id is not None:
            async with async_session_factory() as session:
                br = await WorkingBreakRepository(session).get_by_id(break_id)
            if br:
                weekday = br.weekday
        if weekday is not None:
            await send_day_detail_message(message, int(weekday), lang)
        else:
            await send_working_hours_main(message, lang)
        return

    if current.startswith("AdminUnavailableStates"):
        await state.clear()
        await message.answer(t(lang, "cancelled"), reply_markup=ReplyKeyboardRemove())
        from app.bot.handlers.unavailable import send_unavailable_main

        await send_unavailable_main(message, lang)
        return

    if current.startswith("AdminServiceMediaStates"):
        data = await state.get_data()
        service_id = data.get("media_service_id")
        await state.clear()
        await message.answer(t(lang, "cancelled"), reply_markup=ReplyKeyboardRemove())
        if service_id:
            from app.bot.handlers.service_media import show_media_menu

            await show_media_menu(message, service_id, lang)
        else:
            await _send_cancel_destination(message, "admin", is_admin, lang)
        return

    if current.startswith("AdminServiceLocationStates"):
        data = await state.get_data()
        service_id = data.get("location_service_id")
        await state.clear()
        await message.answer(t(lang, "cancelled"), reply_markup=ReplyKeyboardRemove())
        if service_id:
            from app.bot.handlers.service_locations import show_locations_list

            await show_locations_list(message, service_id, lang)
        else:
            await _send_cancel_destination(message, "admin", is_admin, lang)
        return

    if current.startswith("ClientBookingEditStates"):
        data = await state.get_data()
        booking_id = data.get("edit_booking_id")
        await state.clear()
        await message.answer(t(lang, "cancelled"), reply_markup=ReplyKeyboardRemove())
        if booking_id:
            from app.bot.handlers.booking_edit import show_client_booking_detail

            await show_client_booking_detail(message, booking_id, message.from_user.id, lang)
        else:
            await _send_cancel_destination(message, "client", is_admin, lang)
        return

    if current.startswith("AttendanceStates"):
        data = await state.get_data()
        booking_id = data.get("attendance_booking_id")
        await state.clear()
        await message.answer(t(lang, "cancelled"), reply_markup=ReplyKeyboardRemove())
        if booking_id:
            await message.answer(
                t(lang, "attendance_action_prompt"),
                reply_markup=attendance_action_kb(booking_id, lang),
            )
        else:
            await _send_cancel_destination(message, "client", is_admin, lang)
        return

    if current.startswith("AdminConfirmationTextStates"):
        await state.clear()
        await message.answer(t(lang, "cancelled"), reply_markup=ReplyKeyboardRemove())
        from app.bot.settings_ui import send_confirmation_settings_menu

        await send_confirmation_settings_menu(message, lang)
        return

    if current.startswith("AdminStartScreenStates"):
        await state.clear()
        await message.answer(t(lang, "cancelled"), reply_markup=ReplyKeyboardRemove())
        from app.bot.settings_ui import send_start_screen_menu

        await send_start_screen_menu(message, lang)
        return

    if current.startswith("ClientSupportStates"):
        await state.clear()
        await message.answer(t(lang, "cancelled"), reply_markup=ReplyKeyboardRemove())
        await message.answer(t(lang, "main_menu"), reply_markup=main_menu(is_admin, lang))
        return

    if current.startswith("AdminSupportStates"):
        await state.clear()
        await message.answer(t(lang, "cancelled"), reply_markup=ReplyKeyboardRemove())
        await show_admin_panel(message, lang)
        return

    if current.startswith("AdminClientSearchStates"):
        await state.clear()
        await message.answer(t(lang, "cancelled"), reply_markup=ReplyKeyboardRemove())
        from app.bot.handlers.admin_clients import show_clients_main

        await show_clients_main(message, lang)
        return

    if current.startswith("AdminBookingSearchStates"):
        await state.clear()
        await message.answer(t(lang, "cancelled"), reply_markup=ReplyKeyboardRemove())
        from app.bot.handlers.admin_bookings import show_bookings_hub

        await show_bookings_hub(message, lang)
        return

    destination = await cancel_destination(state, is_admin)
    settings_state = current.startswith("AdminSettingsStates")
    await state.clear()
    await message.answer(t(lang, "cancelled"), reply_markup=ReplyKeyboardRemove())
    if settings_state and is_admin:
        await send_settings_main_after_cancel(message, lang, message.from_user.id)
        return
    await _send_cancel_destination(message, destination, is_admin, lang)


@router.callback_query(F.data == "cancel")
async def cancel_flow_callback(callback: CallbackQuery, state: FSMContext, is_admin: bool, lang: str) -> None:
    current = await state.get_state()
    if current is None:
        await safe_callback_answer(callback)
        try:
            await callback.message.edit_text(t(lang, "cancelled"))
        except TelegramBadRequest:
            await callback.message.answer(t(lang, "cancelled"))
        await callback.message.answer(t(lang, "main_menu"), reply_markup=main_menu(is_admin, lang))
        return

    if current.startswith("AdminServiceMediaStates"):
        data = await state.get_data()
        service_id = data.get("media_service_id")
        await state.clear()
        await safe_callback_answer(callback, t(lang, "cancelled"))
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except TelegramBadRequest:
            pass
        if service_id:
            from app.bot.handlers.service_media import show_media_menu

            await show_media_menu(callback, service_id, lang)
        return

    if current.startswith("AdminServiceLocationStates"):
        data = await state.get_data()
        service_id = data.get("location_service_id")
        await state.clear()
        await safe_callback_answer(callback, t(lang, "cancelled"))
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except TelegramBadRequest:
            pass
        if service_id:
            from app.bot.handlers.service_locations import show_locations_list

            await show_locations_list(callback, service_id, lang)
        return

    if current.startswith("ClientBookingEditStates"):
        data = await state.get_data()
        booking_id = data.get("edit_booking_id")
        await state.clear()
        await safe_callback_answer(callback, t(lang, "cancelled"))
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except TelegramBadRequest:
            pass
        if booking_id:
            from app.bot.handlers.booking_edit import show_client_booking_detail

            await show_client_booking_detail(callback, booking_id, callback.from_user.id, lang)
        return

    if current.startswith("AdminConfirmationTextStates"):
        await state.clear()
        await safe_callback_answer(callback, t(lang, "cancelled"))
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except TelegramBadRequest:
            pass
        from app.bot.settings_ui import send_confirmation_settings_menu

        await send_confirmation_settings_menu(callback.message, lang)
        return

    if current.startswith("AdminStartScreenStates"):
        await state.clear()
        await safe_callback_answer(callback, t(lang, "cancelled"))
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except TelegramBadRequest:
            pass
        from app.bot.settings_ui import send_start_screen_menu

        await send_start_screen_menu(callback.message, lang)
        return

    if current.startswith("ClientSupportStates"):
        await state.clear()
        await safe_callback_answer(callback, t(lang, "cancelled"))
        await callback.message.answer(t(lang, "main_menu"), reply_markup=main_menu(is_admin, lang))
        return

    if current.startswith("AdminSupportStates"):
        await state.clear()
        await safe_callback_answer(callback, t(lang, "cancelled"))
        await show_admin_panel(callback.message, lang)
        return

    if current.startswith("AdminClientSearchStates"):
        await state.clear()
        await safe_callback_answer(callback, t(lang, "cancelled"))
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except TelegramBadRequest:
            pass
        from app.bot.handlers.admin_clients import show_clients_main

        await show_clients_main(callback.message, lang)
        return

    if current.startswith("AdminBookingSearchStates"):
        await state.clear()
        await safe_callback_answer(callback, t(lang, "cancelled"))
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except TelegramBadRequest:
            pass
        from app.bot.handlers.admin_bookings import show_bookings_hub

        await show_bookings_hub(callback.message, lang)
        return

    destination = await cancel_destination(state, is_admin)
    await state.clear()
    try:
        await callback.message.edit_text(t(lang, "cancelled"))
    except TelegramBadRequest:
        try:
            await callback.message.delete()
        except TelegramBadRequest:
            pass
        await callback.message.answer(t(lang, "cancelled"))
    if destination == "admin":
        await show_admin_panel(callback.message, lang)
    else:
        async with async_session_factory() as session:
            kwargs = await menu_mode_kwargs(session)
        await callback.message.answer(t(lang, "main_menu"), reply_markup=main_menu(is_admin, lang, **kwargs))
    await safe_callback_answer(callback)
