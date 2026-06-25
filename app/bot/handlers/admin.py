import logging
import time

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.utils.callbacks import safe_callback_answer
from app.bot.handlers.admin_bookings import show_bookings_hub
from app.bot.utils.menu_helpers import menu_mode_kwargs, mode_aware_admin_menu, show_admin_panel
from app.bot.utils.telegram_ui import edit_or_send, safe_edit_text

from app.bot.i18n import format_buffer, format_duration, t
from app.bot.keyboards import (
    ADMIN_CALENDAR_TEXTS,
    ADMIN_SERVICES_TEXTS,
    admin_active_services_grouped_kb,
    admin_archived_services_kb,
    admin_disabled_services_kb,
    admin_menu,
    admin_service_delete_confirm_kb,
    admin_service_search_results_kb,
    admin_services_hub_kb,
    archived_service_detail_kb,
    cancel_kb,
    permanent_delete_confirm_kb,
)
from app.bot.keyboards.service_buffer_kb import service_buffer_kb
from app.bot.keyboards.service_duration_kb import service_duration_kb
from app.bot.keyboards.service_type_kb import service_type_change_kb, service_type_choose_kb
from app.bot.states import (
    AdminMessageStates,
    AdminServiceStates,
)
from app.config import get_settings
from app.database.session import async_session_factory
from app.models import BookingStatus, Client, SERVICE_TYPE_BOOKING, SERVICE_TYPE_ORDER
from app.repositories import (
    BookingRepository,
    ServiceRepository,
    SettingsRepository,
)
from app.services.booking_service import BookingService
from app.services.booking_notification_service import (
    notify_client_booking_cancelled_by_admin,
    schedule_calendar_auth_admin_notify,
)
from app.services.language_service import get_user_language
from app.services.service_media_service import build_admin_service_detail
from app.services.service_modes_service import default_service_type_for_modes, load_service_modes
from app.utils.formatting import format_booking, parse_time
from app.utils.perf_logging import log_action_timing

router = Router()
logger = logging.getLogger(__name__)

MIN_SERVICE_DURATION = 5
MAX_SERVICE_DURATION = 1440
MAX_SERVICE_BUFFER = 1440


def _duration_prompt(lang: str) -> str:
    return f"{t(lang, 'svc_duration_title')}\n{t(lang, 'svc_duration_choose')}"


def _buffer_prompt(lang: str) -> str:
    return (
        f"{t(lang, 'svc_buffer_title')}\n\n{t(lang, 'svc_buffer_choose')}\n\n{t(lang, 'buffer_explanation')}"
    )


def _is_valid_duration(value: str) -> bool:
    return value.isdigit() and MIN_SERVICE_DURATION <= int(value) <= MAX_SERVICE_DURATION


def _is_valid_buffer(value: str) -> bool:
    return value.isdigit() and 0 <= int(value) <= MAX_SERVICE_BUFFER


async def _apply_service_duration(
    minutes: int,
    state: FSMContext,
    lang: str,
    message: Message,
) -> None:
    data = await state.get_data()
    edit_service_id = data.get("edit_service_id")
    if edit_service_id and data.get("edit_field") == "dur":
        async with async_session_factory() as session:
            service = await ServiceRepository(session).get_by_id(edit_service_id)
            if not service:
                await message.answer(t(lang, "service_not_found"))
                await state.clear()
                return
            service.duration_minutes = minutes
            await session.commit()
            text, kb = await build_admin_service_detail(session, service, lang)
        await state.clear()
        await message.answer(text, reply_markup=kb)
        return
    await state.update_data(duration=minutes)
    await state.set_state(AdminServiceStates.buffer)
    await message.answer(t(lang, "duration_selected", duration=format_duration(lang, minutes)))
    await message.answer(_buffer_prompt(lang), reply_markup=service_buffer_kb(lang))


async def _apply_service_buffer(
    minutes: int,
    state: FSMContext,
    lang: str,
    message: Message,
) -> None:
    data = await state.get_data()
    edit_service_id = data.get("edit_service_id")
    if edit_service_id and data.get("edit_field") == "buf":
        async with async_session_factory() as session:
            service = await ServiceRepository(session).get_by_id(edit_service_id)
            if not service:
                await message.answer(t(lang, "service_not_found"))
                await state.clear()
                return
            service.buffer_after_minutes = minutes
            await session.commit()
            text, kb = await build_admin_service_detail(session, service, lang)
        await state.clear()
        await message.answer(text, reply_markup=kb)
        return
    await state.update_data(buffer_after_minutes=minutes)
    await state.set_state(AdminServiceStates.price)
    await message.answer(t(lang, "buffer_saved", buffer=format_buffer(lang, minutes)))
    await message.answer(t(lang, "enter_price"), reply_markup=cancel_kb(lang))


def _service_price_label(service, lang: str) -> str:
    return f"{service.price} ₽" if service.price else t(lang, "price_free")


def _format_archived_service_detail(service, bookings_count: int, lang: str) -> str:
    return t(
        lang,
        "archived_service_detail",
        name=service.name,
        duration=str(service.duration_minutes),
        price=_service_price_label(service, lang),
        bookings_count=str(bookings_count),
    )


def _active_services_text(services, lang: str) -> str:
    from app.models import SERVICE_TYPE_ORDER

    lines = [t(lang, "services_active_title"), ""]
    booking_services = sorted(
        [s for s in services if s.service_type != SERVICE_TYPE_ORDER],
        key=lambda s: s.name.lower(),
    )
    order_services = sorted(
        [s for s in services if s.service_type == SERVICE_TYPE_ORDER],
        key=lambda s: s.name.lower(),
    )
    if booking_services:
        lines.append(t(lang, "services_group_booking"))
    if order_services:
        lines.append(t(lang, "services_group_order"))
    if not services:
        lines.append(t(lang, "services_no_active"))
    return "\n".join(lines)


def _disabled_services_text(services, lang: str) -> str:
    lines = [t(lang, "services_disabled_title"), "", t(lang, "services_disabled_intro")]
    if not services:
        lines.append(t(lang, "services_no_disabled"))
    return "\n".join(lines)


def _services_hub_text(active_count: int, disabled_count: int, archived_count: int, lang: str) -> str:
    return "\n".join(
        [
            t(lang, "services_management"),
            "",
            t(lang, "services_hub_intro"),
            t(lang, "services_folder_active", count=str(active_count)),
            t(lang, "services_folder_disabled", count=str(disabled_count)),
            t(lang, "services_folder_archive", count=str(archived_count)),
        ]
    )


async def _show_admin_services_hub(callback: CallbackQuery, lang: str) -> None:
    async with async_session_factory() as session:
        repo = ServiceRepository(session)
        active_count = await repo.count_active_services()
        disabled_count = await repo.count_disabled_services()
        archived_count = await repo.count_archived_services()
    await safe_edit_text(
        callback.message,
        _services_hub_text(active_count, disabled_count, archived_count, lang),
        reply_markup=admin_services_hub_kb(
            active_count=active_count,
            disabled_count=disabled_count,
            archived_count=archived_count,
            lang=lang,
        ),
    )


async def _show_admin_active_services(callback: CallbackQuery, lang: str) -> None:
    async with async_session_factory() as session:
        services = await ServiceRepository(session).list_active_services()
    await safe_edit_text(
        callback.message,
        _active_services_text(services, lang),
        reply_markup=admin_active_services_grouped_kb(services, lang),
    )


async def _show_admin_services(callback: CallbackQuery, lang: str) -> None:
    await _show_admin_services_hub(callback, lang)


async def _show_disabled_services(callback: CallbackQuery, lang: str) -> None:
    async with async_session_factory() as session:
        services = await ServiceRepository(session).list_disabled_services()
    await safe_edit_text(callback.message,
        _disabled_services_text(services, lang),
        reply_markup=admin_disabled_services_kb(services, lang),
    )


async def _show_service_detail(callback: CallbackQuery, service_id: int, lang: str) -> bool:
    async with async_session_factory() as session:
        repo = ServiceRepository(session)
        service = await repo.get_by_id(service_id)
        if not service:
            await safe_callback_answer(callback, t(lang, "not_found"), show_alert=True)
            return False
        if service.archived_at is not None:
            bookings_count = await repo.count_bookings_for_service(service_id)
            await safe_edit_text(callback.message,
                _format_archived_service_detail(service, bookings_count, lang),
                reply_markup=archived_service_detail_kb(service_id, lang),
            )
            return True
        text, kb = await build_admin_service_detail(session, service, lang)
    await safe_edit_text(callback.message,text, reply_markup=kb)
    return True


@router.message(F.text.in_(ADMIN_SERVICES_TEXTS))
async def admin_services(message: Message, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    async with async_session_factory() as session:
        repo = ServiceRepository(session)
        active_count = await repo.count_active_services()
        disabled_count = await repo.count_disabled_services()
        archived_count = await repo.count_archived_services()
    await message.answer(
        _services_hub_text(active_count, disabled_count, archived_count, lang),
        reply_markup=admin_services_hub_kb(
            active_count=active_count,
            disabled_count=disabled_count,
            archived_count=archived_count,
            lang=lang,
        ),
    )


@router.callback_query(F.data.in_({"svc:list", "adm_svc:list", "svc:hub"}))
async def admin_services_list(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    await _show_admin_services_hub(callback, lang)
    await safe_callback_answer(callback)


@router.callback_query(F.data == "svc:active")
async def admin_active_services_list(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    await _show_admin_active_services(callback, lang)
    await safe_callback_answer(callback)


@router.callback_query(F.data == "svc:search")
async def admin_services_search_start(callback: CallbackQuery, state: FSMContext, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    await state.set_state(AdminServiceStates.searching)
    await callback.message.answer(t(lang, "services_search_prompt"), reply_markup=cancel_kb(lang))
    await safe_callback_answer(callback)


@router.message(AdminServiceStates.searching, F.text)
async def admin_services_search_query(message: Message, state: FSMContext, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    query = message.text.strip()
    async with async_session_factory() as session:
        services = await ServiceRepository(session).search_by_name(query)
    await state.clear()
    if not services:
        await message.answer(t(lang, "services_search_no_results"))
        return
    await message.answer(
        t(lang, "services_search_button"),
        reply_markup=admin_service_search_results_kb(services, lang),
    )


@router.callback_query(F.data == "svc:disabled")
async def admin_disabled_services_list(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    await _show_disabled_services(callback, lang)
    await safe_callback_answer(callback)


@router.callback_query(F.data.regexp(r"^svc:disabled:view:\d+$"))
async def admin_disabled_service_detail(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    service_id = int(callback.data.rsplit(":", 1)[1])
    async with async_session_factory() as session:
        service = await ServiceRepository(session).get_by_id(service_id)
    if not service or service.archived_at is not None or service.is_active:
        await safe_callback_answer(callback, t(lang, "service_not_found"), show_alert=True)
        return
    if await _show_service_detail(callback, service_id, lang):
        await safe_callback_answer(callback)


@router.callback_query(F.data == "svc:back")
async def admin_services_back_to_panel(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    await callback.message.delete()
    await show_admin_panel(callback.message, lang)
    await safe_callback_answer(callback)


@router.callback_query(F.data == "svc:archive")
async def admin_archived_services_list(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    async with async_session_factory() as session:
        services = await ServiceRepository(session).list_archived_services()
    body = t(lang, "archived_services_intro")
    if not services:
        body = f"{body}\n\n{t(lang, 'archive_empty')}"
    await safe_edit_text(callback.message,
        f"{t(lang, 'services_archive_title')}\n\n{body}",
        reply_markup=admin_archived_services_kb(services, lang),
    )
    await safe_callback_answer(callback)


@router.callback_query(F.data.startswith("svc:arch:view:"))
async def admin_archived_service_detail(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    service_id = int(callback.data.rsplit(":", 1)[1])
    async with async_session_factory() as session:
        repo = ServiceRepository(session)
        service = await repo.get_by_id(service_id)
        bookings_count = await repo.count_bookings_for_service(service_id) if service else 0
    if not service or service.archived_at is None:
        await safe_callback_answer(callback, t(lang, "service_not_found"), show_alert=True)
        return
    await safe_edit_text(callback.message,
        _format_archived_service_detail(service, bookings_count, lang),
        reply_markup=archived_service_detail_kb(service_id, lang),
    )
    await safe_callback_answer(callback)


@router.callback_query(F.data.startswith("svc:arch:restore:"))
async def admin_restore_service(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    service_id = int(callback.data.rsplit(":", 1)[1])
    async with async_session_factory() as session:
        service = await ServiceRepository(session).restore_service(service_id)
        await session.commit()
    if not service:
        await safe_callback_answer(callback, t(lang, "service_not_found"), show_alert=True)
        return
    await safe_callback_answer(callback, t(lang, "service_restored"))
    await _show_admin_services(callback, lang)


@router.callback_query(F.data.regexp(r"^svc:arch:delete:\d+$"))
async def admin_permanent_delete_prompt(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    service_id = int(callback.data.rsplit(":", 1)[1])
    async with async_session_factory() as session:
        repo = ServiceRepository(session)
        service = await repo.get_by_id(service_id)
        bookings_count = await repo.count_bookings_for_service(service_id) if service else 0
    if not service or service.archived_at is None:
        await safe_callback_answer(callback, t(lang, "service_not_found"), show_alert=True)
        return
    if bookings_count > 0:
        await safe_callback_answer(callback, t(lang, "delete_permanently_blocked_has_bookings"), show_alert=True)
        return
    await safe_edit_text(callback.message,
        t(lang, "delete_permanently_confirm"),
        reply_markup=permanent_delete_confirm_kb(service_id, lang),
    )
    await safe_callback_answer(callback)


@router.callback_query(F.data.startswith("svc:arch:delete_confirm:"))
async def admin_permanent_delete_confirmed(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    service_id = int(callback.data.rsplit(":", 1)[1])
    async with async_session_factory() as session:
        result = await ServiceRepository(session).permanently_delete_service_if_safe(service_id)
        await session.commit()
    if result == "not_found":
        await safe_callback_answer(callback, t(lang, "service_not_found"), show_alert=True)
        return
    if result == "blocked":
        await safe_callback_answer(callback, t(lang, "delete_permanently_blocked_has_bookings"), show_alert=True)
        return
    await safe_callback_answer(callback, t(lang, "delete_permanently_success"))
    await admin_archived_services_list(callback, is_admin, lang)


@router.callback_query(F.data == "adm_svc:add")
async def admin_service_add(callback: CallbackQuery, state: FSMContext, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    await state.update_data(flow_origin="admin")
    await state.set_state(AdminServiceStates.name)
    await callback.message.answer(t(lang, "enter_service_name"), reply_markup=cancel_kb(lang))
    await safe_callback_answer(callback)


@router.message(AdminServiceStates.name, F.text)
async def admin_service_name(message: Message, state: FSMContext, lang: str) -> None:
    await state.update_data(name=message.text.strip())
    await state.set_state(AdminServiceStates.description)
    await message.answer(t(lang, "enter_description"))


async def _proceed_after_service_type(message: Message, state: FSMContext, lang: str, service_type: str) -> None:
    await state.update_data(service_type=service_type)
    if service_type == SERVICE_TYPE_ORDER:
        await state.set_state(AdminServiceStates.price)
        await message.answer(t(lang, "enter_price"), reply_markup=cancel_kb(lang))
        return
    await state.set_state(AdminServiceStates.duration)
    await message.answer(_duration_prompt(lang), reply_markup=service_duration_kb(lang))


@router.message(AdminServiceStates.description, F.text)
async def admin_service_description(message: Message, state: FSMContext, lang: str) -> None:
    desc = None if message.text.strip() == "-" else message.text.strip()
    await state.update_data(description=desc)
    async with async_session_factory() as session:
        modes = await load_service_modes(session)
    if modes.booking_enabled and modes.order_enabled:
        await state.set_state(AdminServiceStates.choosing_type)
        await message.answer(
            f"{t(lang, 'service_type_choose_title')}\n\n{t(lang, 'service_type_choose_intro')}",
            reply_markup=service_type_choose_kb(lang),
        )
        return
    svc_type = default_service_type_for_modes(modes)
    await _proceed_after_service_type(message, state, lang, svc_type)


@router.callback_query(AdminServiceStates.choosing_type, F.data.startswith("svc:type:"))
async def admin_service_type_pick(callback: CallbackQuery, state: FSMContext, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    service_type = callback.data.removeprefix("svc:type:")
    if service_type not in (SERVICE_TYPE_BOOKING, SERVICE_TYPE_ORDER):
        await safe_callback_answer(callback, t(lang, "not_found"), show_alert=True)
        return
    await safe_callback_answer(callback)
    await _proceed_after_service_type(callback.message, state, lang, service_type)


@router.callback_query(AdminServiceStates.duration, F.data.startswith("svc:dur:"))
async def admin_service_duration_pick(callback: CallbackQuery, state: FSMContext, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    value = callback.data.removeprefix("svc:dur:")
    if value == "manual":
        await state.set_state(AdminServiceStates.duration_manual)
        await callback.message.answer(t(lang, "enter_duration_manual"), reply_markup=cancel_kb(lang))
        await safe_callback_answer(callback)
        return
    if not value.isdigit():
        await safe_callback_answer(callback, t(lang, "not_found"), show_alert=True)
        return
    await _apply_service_duration(int(value), state, lang, callback.message)
    await safe_callback_answer(callback)


@router.message(AdminServiceStates.duration_manual, F.text)
async def admin_service_duration_manual(message: Message, state: FSMContext, lang: str) -> None:
    if not _is_valid_duration(message.text.strip()):
        await message.answer(t(lang, "svc_duration_invalid"))
        return
    await _apply_service_duration(int(message.text.strip()), state, lang, message)


@router.callback_query(AdminServiceStates.buffer, F.data.startswith("svc:buf:"))
async def admin_service_buffer_pick(callback: CallbackQuery, state: FSMContext, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    value = callback.data.removeprefix("svc:buf:")
    if value == "manual":
        await state.set_state(AdminServiceStates.buffer_manual)
        await callback.message.answer(t(lang, "enter_buffer_manual"), reply_markup=cancel_kb(lang))
        await safe_callback_answer(callback)
        return
    if not value.isdigit():
        await safe_callback_answer(callback, t(lang, "not_found"), show_alert=True)
        return
    await _apply_service_buffer(int(value), state, lang, callback.message)
    await safe_callback_answer(callback)


@router.message(AdminServiceStates.buffer_manual, F.text)
async def admin_service_buffer_manual(message: Message, state: FSMContext, lang: str) -> None:
    if not _is_valid_buffer(message.text.strip()):
        await message.answer(t(lang, "invalid_buffer_minutes"))
        return
    await _apply_service_buffer(int(message.text.strip()), state, lang, message)


@router.message(AdminServiceStates.price, F.text)
async def admin_service_price(message: Message, state: FSMContext, lang: str) -> None:
    if not message.text.isdigit():
        await message.answer(t(lang, "enter_number"))
        return
    data = await state.get_data()
    service_type = data.get("service_type", SERVICE_TYPE_BOOKING)
    duration = data.get("duration", 60) if service_type == SERVICE_TYPE_BOOKING else 60
    buffer_m = data.get("buffer_after_minutes", 0) if service_type == SERVICE_TYPE_BOOKING else 0
    async with async_session_factory() as session:
        service = await ServiceRepository(session).create(
            name=data["name"],
            description=data.get("description"),
            duration_minutes=duration,
            buffer_after_minutes=buffer_m,
            price=int(message.text),
            service_type=service_type,
        )
        await session.commit()
        kwargs = await menu_mode_kwargs(session)
    await state.clear()
    await message.answer(t(lang, "service_created", name=service.name), reply_markup=admin_menu(lang, **kwargs))


@router.callback_query(F.data.regexp(r"^adm_svc:\d+$"))
async def admin_service_detail(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    service_id = int(callback.data.split(":")[-1])
    if await _show_service_detail(callback, service_id, lang):
        await safe_callback_answer(callback)


@router.callback_query(F.data.regexp(r"^svc:chtype:menu:\d+$"))
async def admin_service_type_change_menu(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    service_id = int(callback.data.rsplit(":", 1)[1])
    async with async_session_factory() as session:
        modes = await load_service_modes(session)
        service = await ServiceRepository(session).get_by_id(service_id)
    if not service or not (modes.booking_enabled and modes.order_enabled):
        await safe_callback_answer(callback, t(lang, "not_found"), show_alert=True)
        return
    await safe_edit_text(
        callback.message,
        f"{t(lang, 'service_type_choose_title')}\n\n{t(lang, 'service_type_change_warning')}",
        reply_markup=service_type_change_kb(service_id, lang),
    )
    await safe_callback_answer(callback)


@router.callback_query(F.data.regexp(r"^svc:chtype:(booking|order):\d+$"))
async def admin_service_type_change_apply(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    parts = callback.data.split(":")
    new_type = parts[2]
    service_id = int(parts[3])
    async with async_session_factory() as session:
        service = await ServiceRepository(session).get_by_id(service_id)
        if not service:
            await safe_callback_answer(callback, t(lang, "not_found"), show_alert=True)
            return
        if service.service_type != new_type:
            service.service_type = new_type
            await session.commit()
        text, kb = await build_admin_service_detail(session, service, lang)
    await safe_callback_answer(callback, t(lang, "service_type_changed"))
    await safe_edit_text(callback.message, text, reply_markup=kb)


@router.callback_query(F.data.startswith("adm_svc_loc:"))
async def admin_service_toggle_location(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    service_id = int(callback.data.split(":", 1)[1])
    async with async_session_factory() as session:
        service = await ServiceRepository(session).get_by_id(service_id)
        if not service:
            await safe_callback_answer(callback, t(lang, "service_not_found"), show_alert=True)
            return
        if service.service_type == SERVICE_TYPE_ORDER:
            await safe_callback_answer(callback, t(lang, "not_found"), show_alert=True)
            return
        service.requires_location = not service.requires_location
        await session.commit()
        text, kb = await build_admin_service_detail(session, service, lang)
    msg = t(lang, "location_request_enabled" if service.requires_location else "location_request_disabled")
    await safe_callback_answer(callback, msg)
    await safe_edit_text(callback.message,text, reply_markup=kb)


@router.callback_query(F.data.startswith("adm_svc_comment:"))
async def admin_service_toggle_comment(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    service_id = int(callback.data.split(":", 1)[1])
    async with async_session_factory() as session:
        service = await ServiceRepository(session).get_by_id(service_id)
        if not service:
            await safe_callback_answer(callback, t(lang, "service_not_found"), show_alert=True)
            return
        if service.service_type == SERVICE_TYPE_ORDER:
            await safe_callback_answer(callback, t(lang, "not_found"), show_alert=True)
            return
        service.ask_client_comment = not service.ask_client_comment
        await session.commit()
        text, kb = await build_admin_service_detail(session, service, lang)
    msg = t(lang, "client_comment_enabled" if service.ask_client_comment else "client_comment_disabled")
    await safe_callback_answer(callback, msg)
    await safe_edit_text(callback.message,text, reply_markup=kb)


@router.callback_query(F.data.regexp(r"^svc:disable:\d+$"))
async def admin_disable_service(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    service_id = int(callback.data.rsplit(":", 1)[1])
    async with async_session_factory() as session:
        service = await ServiceRepository(session).get_by_id(service_id)
        if not service or service.archived_at is not None:
            await safe_callback_answer(callback, t(lang, "service_not_found"), show_alert=True)
            return
        service.is_active = False
        await session.commit()
    await safe_callback_answer(callback, t(lang, "service_disabled_success"))
    await _show_admin_services(callback, lang)


@router.callback_query(F.data.regexp(r"^svc:enable:\d+$"))
async def admin_enable_service(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    service_id = int(callback.data.rsplit(":", 1)[1])
    async with async_session_factory() as session:
        service = await ServiceRepository(session).get_by_id(service_id)
        if not service or service.archived_at is not None:
            await safe_callback_answer(callback, t(lang, "service_not_found"), show_alert=True)
            return
        service.is_active = True
        await session.commit()
    await safe_callback_answer(callback, t(lang, "service_enabled_success"))
    await _show_disabled_services(callback, lang)


@router.callback_query(F.data.regexp(r"^svc:move_arch:\d+$"))
async def admin_move_service_to_archive(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    service_id = int(callback.data.rsplit(":", 1)[1])
    async with async_session_factory() as session:
        repo = ServiceRepository(session)
        service = await repo.get_by_id(service_id)
        if not service or service.archived_at is not None:
            await safe_callback_answer(callback, t(lang, "service_not_found"), show_alert=True)
            return
        await repo.archive_service(service)
        await session.commit()
    await safe_callback_answer(callback, t(lang, "service_archived"))
    await _show_disabled_services(callback, lang)


@router.callback_query(F.data.regexp(r"^adm_svc_toggle:\d+$"))
async def admin_service_toggle(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    service_id = int(callback.data.split(":")[-1])
    async with async_session_factory() as session:
        service = await ServiceRepository(session).get_by_id(service_id)
        if not service:
            await safe_callback_answer(callback, t(lang, "service_not_found"), show_alert=True)
            return
        was_active = service.is_active
        service.is_active = not service.is_active
        await session.commit()
    msg = t(lang, "service_disabled_success" if was_active else "service_enabled_success")
    await safe_callback_answer(callback, msg)
    if was_active:
        await _show_admin_services(callback, lang)
    else:
        await _show_disabled_services(callback, lang)


@router.callback_query(F.data.regexp(r"^adm_svc_del:\d+$"))
async def admin_service_delete_confirm(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    service_id = int(callback.data.split(":", 1)[1])
    async with async_session_factory() as session:
        service = await ServiceRepository(session).get_by_id(service_id)
    if not service:
        await safe_callback_answer(callback, t(lang, "service_not_found"), show_alert=True)
        return
    await safe_edit_text(callback.message,
        t(lang, "service_delete_confirm"),
        reply_markup=admin_service_delete_confirm_kb(service_id, lang),
    )
    await safe_callback_answer(callback)


@router.callback_query(F.data.startswith("adm_svc_del_no:"))
async def admin_service_delete_cancel(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    service_id = int(callback.data.split(":", 1)[1])
    async with async_session_factory() as session:
        service = await ServiceRepository(session).get_by_id(service_id)
        if not service:
            await safe_callback_answer(callback, t(lang, "service_not_found"), show_alert=True)
            return
        text, kb = await build_admin_service_detail(session, service, lang)
    await safe_edit_text(callback.message,text, reply_markup=kb)
    await safe_callback_answer(callback, t(lang, "service_delete_cancelled"))


@router.callback_query(F.data.startswith("adm_svc_del_yes:"))
async def admin_service_delete_confirmed(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    service_id = int(callback.data.split(":", 1)[1])
    async with async_session_factory() as session:
        repo = ServiceRepository(session)
        result = await repo.safe_delete_service(service_id)
        await session.commit()
    if result == "not_found":
        await safe_callback_answer(callback, t(lang, "service_not_found"), show_alert=True)
        return
    if result == "archived":
        msg = t(lang, "service_has_bookings_archived")
    else:
        msg = t(lang, "service_deleted")
    await safe_callback_answer(callback, msg)
    await admin_services_list(callback, is_admin, lang)


@router.callback_query(F.data.startswith("adm_svc_edit:"))
async def admin_service_edit(callback: CallbackQuery, state: FSMContext, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    _, field, sid = callback.data.split(":")
    service_id = int(sid)
    async with async_session_factory() as session:
        service = await ServiceRepository(session).get_by_id(service_id)
        if not service:
            await safe_callback_answer(callback, t(lang, "service_not_found"), show_alert=True)
            return
        if field in ("dur", "buf") and service.service_type == SERVICE_TYPE_ORDER:
            await safe_callback_answer(callback, t(lang, "not_found"), show_alert=True)
            return
    await state.update_data(edit_service_id=service_id, edit_field=field, flow_origin="admin")
    if field == "dur":
        await state.set_state(AdminServiceStates.duration)
        await callback.message.answer(_duration_prompt(lang), reply_markup=service_duration_kb(lang))
        await safe_callback_answer(callback)
        return
    if field == "buf":
        await state.set_state(AdminServiceStates.buffer)
        await callback.message.answer(_buffer_prompt(lang), reply_markup=service_buffer_kb(lang))
        await safe_callback_answer(callback)
        return
    await state.set_state(AdminServiceStates.editing_field)
    prompts = {
        "name": t(lang, "enter_new_name"),
        "desc": t(lang, "enter_new_description"),
        "price": t(lang, "enter_new_price"),
    }
    await callback.message.answer(prompts.get(field, t(lang, "enter_value")), reply_markup=cancel_kb(lang))
    await safe_callback_answer(callback)


@router.message(AdminServiceStates.editing_field, F.text)
async def admin_service_edit_value(message: Message, state: FSMContext, lang: str) -> None:
    data = await state.get_data()
    field = data["edit_field"]
    service_id = data["edit_service_id"]
    async with async_session_factory() as session:
        service = await ServiceRepository(session).get_by_id(service_id)
        if not service:
            await message.answer(t(lang, "service_not_found"))
            await state.clear()
            return
        if field == "name":
            service.name = message.text.strip()
        elif field == "desc":
            service.description = message.text.strip()
        elif field == "price":
            if not message.text.strip().isdigit():
                await message.answer(t(lang, "enter_number"), reply_markup=cancel_kb(lang))
                return
            service.price = int(message.text.strip())
        await session.commit()
        text, kb = await build_admin_service_detail(session, service, lang)
    await state.clear()
    await message.answer(t(lang, "updated"))
    await message.answer(text, reply_markup=kb)


@router.callback_query(F.data.startswith("adm_confirm:"))
async def admin_confirm_booking(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return

    await safe_callback_answer(callback)
    booking_id = int(callback.data.rsplit(":", 1)[1])
    t_total = time.perf_counter()
    t_db = 0.0
    try:
        t0 = time.perf_counter()
        async with async_session_factory() as session:
            booking = await BookingService(session).confirm_booking(booking_id)
            service = await ServiceRepository(session).get_by_id(booking.service_id)
            client = await session.get(Client, booking.client_id)
        t_db = time.perf_counter() - t0
    except ValueError:
        await safe_edit_text(callback.message, t(lang, "not_found"))
        return
    t0 = time.perf_counter()
    await safe_edit_text(
        callback.message,
        f"{t(lang, 'booking_confirmed_admin')}\n{format_booking(booking, service, lang, admin_view=True)}",
    )
    t_ui = time.perf_counter() - t0
    t_notify = 0.0
    if client:
        client_lang = client.language or get_settings().default_language
        try:
            t0 = time.perf_counter()
            await callback.bot.send_message(
                client.telegram_id,
                f"{t(client_lang, 'booking_confirmed_client')}\n{format_booking(booking, service, client_lang, show_location_comment=True)}",
            )
            t_notify = time.perf_counter() - t0
        except Exception:
            pass
    schedule_calendar_auth_admin_notify(callback.bot)
    log_action_timing(
        "admin confirm booking",
        booking_id=booking_id,
        db=t_db,
        ui=t_ui,
        notify=t_notify,
        total=time.perf_counter() - t_total,
    )


@router.callback_query(F.data.startswith("adm_cancel:"))
async def admin_cancel_booking(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return

    await safe_callback_answer(callback)
    booking_id = int(callback.data.split(":", 1)[1])

    async with async_session_factory() as session:
        booking = await BookingRepository(session).get_by_id(booking_id)
        if not booking or booking.status == BookingStatus.CANCELLED:
            await show_bookings_hub(
                callback,
                lang,
                prefix=t(lang, "booking_already_cancelled_or_missing"),
            )
            return
        service = await ServiceRepository(session).get_by_id(booking.service_id)
        try:
            await BookingService(session).cancel_booking(booking_id)
        except ValueError:
            await show_bookings_hub(
                callback,
                lang,
                prefix=t(lang, "booking_already_cancelled_or_missing"),
            )
            return
        except Exception:
            logger.exception("Admin cancel failed for booking_id=%s", booking_id)
            await edit_or_send(callback, t(lang, "error_generic"))
            return
        booking.status = BookingStatus.CANCELLED

    if service:
        await notify_client_booking_cancelled_by_admin(callback.bot, booking, service)

    await show_bookings_hub(
        callback,
        lang,
        prefix=t(lang, "booking_cancelled_admin", id=str(booking_id)),
    )


@router.callback_query(F.data.startswith("adm_msg:"))
async def admin_message_client(callback: CallbackQuery, state: FSMContext, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    booking_id = int(callback.data.split(":", 1)[1])
    await state.update_data(msg_booking_id=booking_id, flow_origin="admin")
    await state.set_state(AdminMessageStates.entering_message)
    await callback.message.answer(t(lang, "enter_message_client"), reply_markup=cancel_kb(lang))
    await safe_callback_answer(callback)


@router.message(AdminMessageStates.entering_message, F.text)
async def admin_send_message(message: Message, state: FSMContext, bot: Bot, lang: str) -> None:
    data = await state.get_data()
    if data.get("msg_order_id"):
        return
    client = None
    async with async_session_factory() as session:
        if data.get("msg_client_id"):
            client = await session.get(Client, data["msg_client_id"])
        elif data.get("msg_booking_id"):
            booking = await BookingRepository(session).get_by_id(data["msg_booking_id"])
            client = await session.get(Client, booking.client_id) if booking else None
        else:
            booking = None
            client = None
    if not client:
        await state.clear()
        await message.answer(t(lang, "not_found"), reply_markup=await mode_aware_admin_menu(lang))
        return
    client_lang = client.language or get_settings().default_language
    try:
        await bot.send_message(
            client.telegram_id,
            t(client_lang, "message_from_admin", text=message.text),
        )
    except Exception:
        await state.clear()
        await message.answer(t(lang, "message_send_failed"), reply_markup=await mode_aware_admin_menu(lang))
        return
    await state.clear()
    await message.answer(t(lang, "message_sent"), reply_markup=await mode_aware_admin_menu(lang))


@router.message(F.text.in_(ADMIN_CALENDAR_TEXTS))
async def admin_calendar_settings(message: Message, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    from app.bot.settings_ui import send_calendar_screen

    await send_calendar_screen(message, lang)
