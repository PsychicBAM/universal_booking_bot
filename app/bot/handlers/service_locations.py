from html import escape

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.utils.callbacks import safe_callback_answer
from app.bot.utils.telegram_ui import safe_edit_text

from app.bot.i18n import t
from app.bot.keyboards import SKIP_TEXTS, cancel_kb, skip_cancel_kb
from app.bot.keyboards.service_location_kb import (
    location_delete_confirm_kb,
    location_detail_kb,
    locations_list_kb,
)
from app.bot.states import AdminServiceLocationStates
from app.database.session import async_session_factory
from app.models import SERVICE_TYPE_ORDER
from app.repositories import ServiceLocationRepository, ServiceRepository
from app.services.service_media_service import build_admin_service_detail

router = Router()


def _locations_list_text(lang: str, locations_count: int) -> str:
    text = f"{t(lang, 'service_locations')}\n{t(lang, 'service_locations_intro')}"
    if locations_count == 0:
        text += f"\n\n{t(lang, 'no_locations')}"
    return text


def _location_detail_text(lang: str, location) -> str:
    address = escape(location.address_text) if location.address_text else t(lang, "not_provided")
    description = escape(location.description) if location.description else t(lang, "not_provided")
    status = t(lang, "location_active") if location.is_active else t(lang, "location_hidden_status")
    return (
        f"{t(lang, 'location_detail')}\n"
        f"{t(lang, 'location_name_label', title=escape(location.title))}\n"
        f"{t(lang, 'location_address_label', address=address)}\n"
        f"{t(lang, 'location_description_label', description=description)}\n"
        f"{t(lang, 'location_status_label', status=status)}"
    )


async def show_locations_list(event: Message | CallbackQuery, service_id: int, lang: str) -> None:
    async with async_session_factory() as session:
        service = await ServiceRepository(session).get_by_id(service_id)
        if not service:
            text = t(lang, "not_found")
            if isinstance(event, CallbackQuery):
                await safe_callback_answer(event, text, show_alert=True)
            else:
                await event.answer(text)
            return
        if service.service_type == SERVICE_TYPE_ORDER:
            text = t(lang, "not_found")
            if isinstance(event, CallbackQuery):
                await safe_callback_answer(event, text, show_alert=True)
            else:
                await event.answer(text)
            return
        locations = await ServiceLocationRepository(session).list_for_service(service_id)
    text = _locations_list_text(lang, len(locations))
    keyboard = locations_list_kb(service_id, locations, lang)
    if isinstance(event, CallbackQuery):
        await safe_edit_text(event.message,text, reply_markup=keyboard)
        await safe_callback_answer(event)
    else:
        await event.answer(text, reply_markup=keyboard)


async def show_location_detail(event: Message | CallbackQuery, location_id: int, lang: str) -> None:
    async with async_session_factory() as session:
        location = await ServiceLocationRepository(session).get_by_id(location_id)
        if not location:
            if isinstance(event, CallbackQuery):
                await safe_callback_answer(event, t(lang, "not_found"), show_alert=True)
            else:
                await event.answer(t(lang, "not_found"))
            return
    text = _location_detail_text(lang, location)
    keyboard = location_detail_kb(location.id, location.service_id, location.is_active, lang)
    if isinstance(event, CallbackQuery):
        await safe_edit_text(event.message,text, reply_markup=keyboard)
        await safe_callback_answer(event)
    else:
        await event.answer(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("loc:view:"))
async def location_view(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    location_id = int(callback.data.split(":")[-1])
    await show_location_detail(callback, location_id, lang)


@router.callback_query(F.data.startswith("loc:list:"))
async def locations_list(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    service_id = int(callback.data.split(":")[-1])
    await show_locations_list(callback, service_id, lang)


@router.callback_query(F.data.startswith("loc:back:"))
async def locations_back_to_service(callback: CallbackQuery, is_admin: bool, lang: str, state: FSMContext) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    await state.clear()
    service_id = int(callback.data.split(":")[-1])
    async with async_session_factory() as session:
        service = await ServiceRepository(session).get_by_id(service_id)
        if not service:
            await safe_callback_answer(callback, t(lang, "not_found"), show_alert=True)
            return
        text, kb = await build_admin_service_detail(session, service, lang)
    await safe_edit_text(callback.message,text, reply_markup=kb)
    await safe_callback_answer(callback)


@router.callback_query(F.data.startswith("loc:add:"))
async def start_add_location(callback: CallbackQuery, is_admin: bool, lang: str, state: FSMContext) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    service_id = int(callback.data.split(":")[-1])
    await state.update_data(flow_origin="admin", location_service_id=service_id, location_draft={})
    await state.set_state(AdminServiceLocationStates.entering_location_title)
    await safe_callback_answer(callback)
    await callback.message.answer(t(lang, "location_name_prompt"), reply_markup=cancel_kb(lang))


@router.message(AdminServiceLocationStates.entering_location_title, F.text)
async def receive_location_title(message: Message, is_admin: bool, lang: str, state: FSMContext) -> None:
    if not is_admin:
        return
    title = message.text.strip()
    if not title:
        await message.answer(t(lang, "location_name_prompt"), reply_markup=cancel_kb(lang))
        return
    data = await state.get_data()
    draft = dict(data.get("location_draft") or {})
    draft["title"] = title
    await state.update_data(location_draft=draft)
    await state.set_state(AdminServiceLocationStates.entering_location_address)
    await message.answer(t(lang, "location_address_prompt"), reply_markup=skip_cancel_kb(lang))


@router.message(AdminServiceLocationStates.entering_location_address, F.text.in_(SKIP_TEXTS))
async def skip_location_address(message: Message, is_admin: bool, lang: str, state: FSMContext) -> None:
    if not is_admin:
        return
    data = await state.get_data()
    draft = dict(data.get("location_draft") or {})
    draft["address_text"] = None
    await state.update_data(location_draft=draft)
    await state.set_state(AdminServiceLocationStates.entering_location_description)
    await message.answer(t(lang, "location_description_prompt"), reply_markup=skip_cancel_kb(lang))


@router.message(AdminServiceLocationStates.entering_location_address, F.text)
async def receive_location_address(message: Message, is_admin: bool, lang: str, state: FSMContext) -> None:
    if not is_admin:
        return
    data = await state.get_data()
    draft = dict(data.get("location_draft") or {})
    draft["address_text"] = message.text.strip() or None
    await state.update_data(location_draft=draft)
    await state.set_state(AdminServiceLocationStates.entering_location_description)
    await message.answer(t(lang, "location_description_prompt"), reply_markup=skip_cancel_kb(lang))


async def _save_new_location(message: Message, state: FSMContext, lang: str, description: str | None) -> None:
    data = await state.get_data()
    service_id = data.get("location_service_id")
    draft = dict(data.get("location_draft") or {})
    if not service_id or not draft.get("title"):
        await state.clear()
        return
    async with async_session_factory() as session:
        await ServiceLocationRepository(session).create(
            service_id,
            draft["title"],
            address_text=draft.get("address_text"),
            description=description,
        )
        await session.commit()
    await state.clear()
    await message.answer(t(lang, "location_saved"))
    await show_locations_list(message, service_id, lang)


@router.message(AdminServiceLocationStates.entering_location_description, F.text.in_(SKIP_TEXTS))
async def skip_location_description(message: Message, is_admin: bool, lang: str, state: FSMContext) -> None:
    if not is_admin:
        return
    await _save_new_location(message, state, lang, None)


@router.message(AdminServiceLocationStates.entering_location_description, F.text)
async def receive_location_description(message: Message, is_admin: bool, lang: str, state: FSMContext) -> None:
    if not is_admin:
        return
    description = message.text.strip() or None
    await _save_new_location(message, state, lang, description)


@router.callback_query(F.data.startswith("loc:list:"))
async def location_hide(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    location_id = int(callback.data.split(":")[-1])
    async with async_session_factory() as session:
        repo = ServiceLocationRepository(session)
        location = await repo.get_by_id(location_id)
        if not location:
            await safe_callback_answer(callback, t(lang, "not_found"), show_alert=True)
            return
        await repo.hide(location)
        await session.commit()
    await safe_callback_answer(callback, t(lang, "location_hidden"))
    await show_location_detail(callback, location_id, lang)


@router.callback_query(F.data.startswith("loc:show:"))
async def location_show(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    location_id = int(callback.data.split(":")[-1])
    async with async_session_factory() as session:
        repo = ServiceLocationRepository(session)
        location = await repo.get_by_id(location_id)
        if not location:
            await safe_callback_answer(callback, t(lang, "not_found"), show_alert=True)
            return
        await repo.show(location)
        await session.commit()
    await safe_callback_answer(callback, t(lang, "location_restored"))
    await show_location_detail(callback, location_id, lang)


@router.callback_query(F.data.startswith("loc:del:"))
async def location_delete_prompt(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    location_id = int(callback.data.split(":")[-1])
    async with async_session_factory() as session:
        location = await ServiceLocationRepository(session).get_by_id(location_id)
        if not location:
            await safe_callback_answer(callback, t(lang, "not_found"), show_alert=True)
            return
    await safe_edit_text(callback.message,
        t(lang, "location_delete_confirm"),
        reply_markup=location_delete_confirm_kb(location_id, lang),
    )
    await safe_callback_answer(callback)


@router.callback_query(F.data.startswith("loc:del_confirm:"))
async def location_delete_confirm(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    location_id = int(callback.data.split(":")[-1])
    async with async_session_factory() as session:
        repo = ServiceLocationRepository(session)
        location = await repo.get_by_id(location_id)
        if not location:
            await safe_callback_answer(callback, t(lang, "not_found"), show_alert=True)
            return
        service_id = location.service_id
        result = await repo.safe_delete(location_id)
        await session.commit()
    if result == "hidden":
        msg = t(lang, "location_hidden_has_bookings")
    elif result == "deleted":
        msg = t(lang, "location_deleted")
    else:
        await safe_callback_answer(callback, t(lang, "not_found"), show_alert=True)
        return
    await safe_callback_answer(callback, msg)
    await show_locations_list(callback, service_id, lang)


@router.callback_query(F.data.startswith("loc:edit:name:"))
async def start_edit_location_name(callback: CallbackQuery, is_admin: bool, lang: str, state: FSMContext) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    location_id = int(callback.data.split(":")[-1])
    async with async_session_factory() as session:
        location = await ServiceLocationRepository(session).get_by_id(location_id)
        if not location:
            await safe_callback_answer(callback, t(lang, "not_found"), show_alert=True)
            return
        service_id = location.service_id
    await state.update_data(flow_origin="admin", editing_location_id=location_id, location_service_id=service_id)
    await state.set_state(AdminServiceLocationStates.editing_location_title)
    await safe_callback_answer(callback)
    await callback.message.answer(t(lang, "location_name_prompt"), reply_markup=cancel_kb(lang))


@router.callback_query(F.data.startswith("loc:edit:addr:"))
async def start_edit_location_address(callback: CallbackQuery, is_admin: bool, lang: str, state: FSMContext) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    location_id = int(callback.data.split(":")[-1])
    async with async_session_factory() as session:
        location = await ServiceLocationRepository(session).get_by_id(location_id)
        if not location:
            await safe_callback_answer(callback, t(lang, "not_found"), show_alert=True)
            return
        service_id = location.service_id
    await state.update_data(flow_origin="admin", editing_location_id=location_id, location_service_id=service_id)
    await state.set_state(AdminServiceLocationStates.editing_location_address)
    await safe_callback_answer(callback)
    await callback.message.answer(t(lang, "location_address_prompt"), reply_markup=skip_cancel_kb(lang))


@router.callback_query(F.data.startswith("loc:edit:desc:"))
async def start_edit_location_description(callback: CallbackQuery, is_admin: bool, lang: str, state: FSMContext) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    location_id = int(callback.data.split(":")[-1])
    async with async_session_factory() as session:
        location = await ServiceLocationRepository(session).get_by_id(location_id)
        if not location:
            await safe_callback_answer(callback, t(lang, "not_found"), show_alert=True)
            return
        service_id = location.service_id
    await state.update_data(flow_origin="admin", editing_location_id=location_id, location_service_id=service_id)
    await state.set_state(AdminServiceLocationStates.editing_location_description)
    await safe_callback_answer(callback)
    await callback.message.answer(t(lang, "location_description_prompt"), reply_markup=skip_cancel_kb(lang))


@router.message(AdminServiceLocationStates.editing_location_title, F.text)
async def edit_location_title(message: Message, is_admin: bool, lang: str, state: FSMContext) -> None:
    if not is_admin:
        return
    title = message.text.strip()
    if not title:
        await message.answer(t(lang, "location_name_prompt"), reply_markup=cancel_kb(lang))
        return
    data = await state.get_data()
    location_id = data.get("editing_location_id")
    if not location_id:
        await state.clear()
        return
    async with async_session_factory() as session:
        location = await ServiceLocationRepository(session).get_by_id(location_id)
        if not location:
            await state.clear()
            await message.answer(t(lang, "not_found"))
            return
        location.title = title
        service_id = location.service_id
        await session.commit()
    await state.clear()
    await message.answer(t(lang, "updated"))
    await show_locations_list(message, service_id, lang)


@router.message(AdminServiceLocationStates.editing_location_address, F.text.in_(SKIP_TEXTS))
async def edit_location_address_skip(message: Message, is_admin: bool, lang: str, state: FSMContext) -> None:
    if not is_admin:
        return
    data = await state.get_data()
    location_id = data.get("editing_location_id")
    if not location_id:
        await state.clear()
        return
    async with async_session_factory() as session:
        location = await ServiceLocationRepository(session).get_by_id(location_id)
        if not location:
            await state.clear()
            await message.answer(t(lang, "not_found"))
            return
        location.address_text = None
        await session.commit()
    await state.clear()
    await message.answer(t(lang, "updated"))
    await show_location_detail(message, location_id, lang)


@router.message(AdminServiceLocationStates.editing_location_address, F.text)
async def edit_location_address(message: Message, is_admin: bool, lang: str, state: FSMContext) -> None:
    if not is_admin:
        return
    data = await state.get_data()
    location_id = data.get("editing_location_id")
    if not location_id:
        await state.clear()
        return
    async with async_session_factory() as session:
        location = await ServiceLocationRepository(session).get_by_id(location_id)
        if not location:
            await state.clear()
            await message.answer(t(lang, "not_found"))
            return
        location.address_text = message.text.strip() or None
        await session.commit()
    await state.clear()
    await message.answer(t(lang, "updated"))
    await show_location_detail(message, location_id, lang)


@router.message(AdminServiceLocationStates.editing_location_description, F.text.in_(SKIP_TEXTS))
async def edit_location_description_skip(message: Message, is_admin: bool, lang: str, state: FSMContext) -> None:
    if not is_admin:
        return
    data = await state.get_data()
    location_id = data.get("editing_location_id")
    if not location_id:
        await state.clear()
        return
    async with async_session_factory() as session:
        location = await ServiceLocationRepository(session).get_by_id(location_id)
        if not location:
            await state.clear()
            await message.answer(t(lang, "not_found"))
            return
        location.description = None
        await session.commit()
    await state.clear()
    await message.answer(t(lang, "updated"))
    await show_location_detail(message, location_id, lang)


@router.message(AdminServiceLocationStates.editing_location_description, F.text)
async def edit_location_description(message: Message, is_admin: bool, lang: str, state: FSMContext) -> None:
    if not is_admin:
        return
    data = await state.get_data()
    location_id = data.get("editing_location_id")
    if not location_id:
        await state.clear()
        return
    async with async_session_factory() as session:
        location = await ServiceLocationRepository(session).get_by_id(location_id)
        if not location:
            await state.clear()
            await message.answer(t(lang, "not_found"))
            return
        location.description = message.text.strip() or None
        await session.commit()
    await state.clear()
    await message.answer(t(lang, "updated"))
    await show_location_detail(message, location_id, lang)
