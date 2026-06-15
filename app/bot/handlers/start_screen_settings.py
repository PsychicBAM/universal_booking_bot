import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.i18n import t
from app.bot.keyboards import cancel_kb
from app.bot.keyboards.start_screen_kb import start_screen_reset_confirm_kb
from app.bot.settings_ui import edit_to_start_screen, send_start_screen_menu
from app.bot.states import AdminStartScreenStates
from app.bot.utils.callbacks import safe_callback_answer
from app.database.session import async_session_factory
from app.services.start_screen_service import (
    START_TEXT_MAX_LEN,
    load_start_screen_config,
    reset_start_screen,
    save_start_photo,
    save_start_text,
    send_start_screen_preview,
    set_start_photo_enabled,
)

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "set:start:open")
async def open_start_screen_menu(callback: CallbackQuery, is_admin: bool, lang: str, state: FSMContext) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    logger.info(
        "Start screen menu opened: callback_data=%s user_id=%s lang=%s",
        callback.data,
        callback.from_user.id,
        lang,
    )
    await safe_callback_answer(callback)
    await state.clear()
    await edit_to_start_screen(callback, lang)


@router.callback_query(F.data == "set:start:edit:ru")
async def start_edit_ru(callback: CallbackQuery, is_admin: bool, lang: str, state: FSMContext) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    await state.update_data(flow_origin="admin_start_screen")
    await state.set_state(AdminStartScreenStates.entering_ru_text)
    await callback.message.answer(t(lang, "start_screen_prompt_ru"), reply_markup=cancel_kb(lang))
    await safe_callback_answer(callback)


@router.callback_query(F.data == "set:start:edit:en")
async def start_edit_en(callback: CallbackQuery, is_admin: bool, lang: str, state: FSMContext) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    await state.update_data(flow_origin="admin_start_screen")
    await state.set_state(AdminStartScreenStates.entering_en_text)
    await callback.message.answer(t(lang, "start_screen_prompt_en"), reply_markup=cancel_kb(lang))
    await safe_callback_answer(callback)


@router.callback_query(F.data == "set:start:photo:ru")
async def start_upload_photo_ru(callback: CallbackQuery, is_admin: bool, lang: str, state: FSMContext) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    await safe_callback_answer(callback)
    await state.update_data(flow_origin="admin_start_screen")
    await state.set_state(AdminStartScreenStates.uploading_photo_ru)
    await callback.message.answer(t(lang, "start_screen_prompt_photo_ru"), reply_markup=cancel_kb(lang))


@router.callback_query(F.data == "set:start:photo:en")
async def start_upload_photo_en(callback: CallbackQuery, is_admin: bool, lang: str, state: FSMContext) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    await safe_callback_answer(callback)
    await state.update_data(flow_origin="admin_start_screen")
    await state.set_state(AdminStartScreenStates.uploading_photo_en)
    await callback.message.answer(t(lang, "start_screen_prompt_photo_en"), reply_markup=cancel_kb(lang))


@router.callback_query(F.data == "set:start:toggle_photo:ru")
async def start_toggle_photo_ru(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    await safe_callback_answer(callback)
    async with async_session_factory() as session:
        config = await load_start_screen_config(session)
        if not config.can_toggle_photo("ru"):
            await callback.message.answer(t(lang, "start_screen_upload_first_ru"))
            return
        await set_start_photo_enabled(session, "ru", not config.start_photo_enabled_ru)
        await session.commit()
    await edit_to_start_screen(callback, lang)


@router.callback_query(F.data == "set:start:toggle_photo:en")
async def start_toggle_photo_en(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    await safe_callback_answer(callback)
    async with async_session_factory() as session:
        config = await load_start_screen_config(session)
        if not config.can_toggle_photo("en"):
            await callback.message.answer(t(lang, "start_screen_upload_first_en"))
            return
        await set_start_photo_enabled(session, "en", not config.start_photo_enabled_en)
        await session.commit()
    await edit_to_start_screen(callback, lang)


@router.callback_query(F.data == "set:start:preview:ru")
async def start_preview_ru(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    await safe_callback_answer(callback)
    logger.info("Start screen preview RU: user_id=%s", callback.from_user.id)
    await send_start_screen_preview(
        callback.bot,
        callback.from_user.id,
        is_admin=is_admin,
        preview_lang="ru",
    )


@router.callback_query(F.data == "set:start:preview:en")
async def start_preview_en(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    await safe_callback_answer(callback)
    logger.info("Start screen preview EN: user_id=%s", callback.from_user.id)
    await send_start_screen_preview(
        callback.bot,
        callback.from_user.id,
        is_admin=is_admin,
        preview_lang="en",
    )


@router.callback_query(F.data == "set:start:reset")
async def start_reset_confirm(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    await safe_callback_answer(callback)
    await callback.message.edit_text(
        t(lang, "start_screen_reset_confirm"),
        reply_markup=start_screen_reset_confirm_kb(lang),
    )


@router.callback_query(F.data == "set:start:reset:yes")
async def start_reset_apply(callback: CallbackQuery, is_admin: bool, lang: str, state: FSMContext) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    await state.clear()
    async with async_session_factory() as session:
        await reset_start_screen(session)
        await session.commit()
    await safe_callback_answer(callback)
    await edit_to_start_screen(callback, lang)


@router.message(AdminStartScreenStates.entering_ru_text, F.text)
async def save_start_ru_text(message: Message, state: FSMContext, lang: str) -> None:
    text = message.text.strip()
    if not text:
        await message.answer(t(lang, "start_screen_text_empty"))
        return
    if len(text) > START_TEXT_MAX_LEN:
        await message.answer(t(lang, "start_screen_text_too_long"))
        return
    async with async_session_factory() as session:
        await save_start_text(session, "ru", text)
        await session.commit()
    await state.clear()
    await message.answer(t(lang, "settings_saved", key="start_text_ru"))
    await send_start_screen_menu(message, lang)


@router.message(AdminStartScreenStates.entering_en_text, F.text)
async def save_start_en_text(message: Message, state: FSMContext, lang: str) -> None:
    text = message.text.strip()
    if not text:
        await message.answer(t(lang, "start_screen_text_empty"))
        return
    if len(text) > START_TEXT_MAX_LEN:
        await message.answer(t(lang, "start_screen_text_too_long"))
        return
    async with async_session_factory() as session:
        await save_start_text(session, "en", text)
        await session.commit()
    await state.clear()
    await message.answer(t(lang, "settings_saved", key="start_text_en"))
    await send_start_screen_menu(message, lang)


@router.message(AdminStartScreenStates.uploading_photo_ru, F.photo)
async def save_start_photo_ru(message: Message, state: FSMContext, lang: str) -> None:
    file_id = message.photo[-1].file_id
    async with async_session_factory() as session:
        await save_start_photo(session, "ru", file_id)
        await session.commit()
    await state.clear()
    await message.answer(t(lang, "start_screen_photo_saved_ru"))
    await send_start_screen_menu(message, lang)


@router.message(AdminStartScreenStates.uploading_photo_ru)
async def start_photo_ru_wrong_type(message: Message, lang: str) -> None:
    await message.answer(t(lang, "start_screen_not_photo"))


@router.message(AdminStartScreenStates.uploading_photo_en, F.photo)
async def save_start_photo_en(message: Message, state: FSMContext, lang: str) -> None:
    file_id = message.photo[-1].file_id
    async with async_session_factory() as session:
        await save_start_photo(session, "en", file_id)
        await session.commit()
    await state.clear()
    await message.answer(t(lang, "start_screen_photo_saved_en"))
    await send_start_screen_menu(message, lang)


@router.message(AdminStartScreenStates.uploading_photo_en)
async def start_photo_en_wrong_type(message: Message, lang: str) -> None:
    await message.answer(t(lang, "start_screen_not_photo"))
