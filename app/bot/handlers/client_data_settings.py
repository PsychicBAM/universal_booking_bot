from dataclasses import replace

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.bot.i18n import t
from app.bot.keyboards.client_data_settings_kb import client_data_preview_kb, client_data_settings_kb
from app.bot.utils.callbacks import safe_callback_answer
from app.bot.utils.telegram_ui import safe_edit_text
from app.database.session import async_session_factory
from app.services.client_data_service import (
    ClientDataSettings,
    format_client_data_preview,
    format_client_data_settings_summary,
    is_valid_phone_config,
    load_client_data_settings,
    save_client_data_settings,
)

router = Router()


async def _load() -> ClientDataSettings:
    async with async_session_factory() as session:
        return await load_client_data_settings(session)


async def _save(settings: ClientDataSettings) -> bool:
    if not is_valid_phone_config(settings):
        return False
    async with async_session_factory() as session:
        await save_client_data_settings(session, settings)
        await session.commit()
    return True


def _toggle(settings: ClientDataSettings, field: str) -> ClientDataSettings:
    mapping = {
        "use_name": "use_telegram_name",
        "confirm_name": "confirm_telegram_name",
        "contact": "phone_request_contact",
        "manual": "phone_manual_input",
        "required": "phone_required",
        "fast": "fast_reuse_saved_data",
    }
    attr = mapping[field]
    return replace(settings, **{attr: not getattr(settings, attr)})


async def show_client_data_settings(callback: CallbackQuery, lang: str) -> None:
    settings = await _load()
    text = format_client_data_settings_summary(settings, lang)
    await safe_edit_text(callback.message, text, reply_markup=client_data_settings_kb(settings, lang))


@router.callback_query(F.data == "set:cda:open")
async def client_data_open(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    await safe_callback_answer(callback)
    await show_client_data_settings(callback, lang)


@router.callback_query(F.data.startswith("set:cda:toggle:"))
async def client_data_toggle(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    field = callback.data.removeprefix("set:cda:toggle:")
    settings = await _load()
    new_settings = _toggle(settings, field)
    if not await _save(new_settings):
        await safe_callback_answer(callback, t(lang, "client_data_invalid_phone_config"), show_alert=True)
        return
    await safe_callback_answer(callback)
    await show_client_data_settings(callback, lang)


@router.callback_query(F.data == "set:cda:preview")
async def client_data_preview(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    settings = await _load()
    await safe_callback_answer(callback)
    text = format_client_data_preview(settings, lang)
    await safe_edit_text(callback.message, text, reply_markup=client_data_preview_kb(lang))
