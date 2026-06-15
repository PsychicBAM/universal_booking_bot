import re

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.i18n import t
from app.bot.utils.callbacks import safe_callback_answer
from app.bot.keyboards import ADMIN_SETTINGS_TEXTS, admin_menu, cancel_kb
from app.bot.keyboards.settings_kb import (
    reminder_admin_presets_kb,
    reminder_client1_presets_kb,
    reminder_client2_presets_kb,
    settings_advanced_kb,
    settings_advanced_keys_kb,
    test_admin_presets_kb,
    test_client_presets_kb,
)
from app.bot.settings_ui import (
    edit_to_advanced,
    edit_to_calendar,
    edit_to_contact,
    edit_to_enabled_languages,
    edit_to_language,
    edit_to_reminders,
    edit_to_settings_main,
    edit_to_test_mode,
    send_settings_main,
)
from app.services.bot_settings_service import load_bot_settings_snapshot
from app.services.calendar_service import CalendarService
from app.services.language_service import effective_lang, save_enabled_languages
from app.bot.states import AdminSettingsStates
from app.config import get_settings
from app.database.session import async_session_factory
from app.repositories import ClientRepository, SettingsRepository

router = Router()

MAX_REMINDER_MINUTES = 10080
USERNAME_RE = re.compile(r"^@?[A-Za-z0-9_]{5,32}$")


async def _save_setting(key: str, value: str) -> None:
    async with async_session_factory() as session:
        await SettingsRepository(session).set(key, value)
        await session.commit()


async def _toggle_bool_setting(key: str, default: str = "false") -> bool:
    async with async_session_factory() as session:
        repo = SettingsRepository(session)
        current = await repo.get(key, default)
        new_val = "false" if (current or default).lower() in ("true", "1", "yes", "on") else "true"
        await repo.set(key, new_val)
        await session.commit()
        return new_val == "true"


@router.message(F.text.in_(ADMIN_SETTINGS_TEXTS))
async def open_settings(message: Message, state: FSMContext, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    await state.clear()
    await send_settings_main(message, lang, message.from_user.id)


@router.callback_query(F.data.startswith("set:") & ~F.data.startswith("set:start:"))
async def settings_callbacks(callback: CallbackQuery, state: FSMContext, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return

    data = callback.data
    parts = data.split(":")

    if data == "set:back:admin":
        await state.clear()
        await callback.message.delete()
        await callback.message.answer(t(lang, "admin_panel"), reply_markup=admin_menu(lang))
        await safe_callback_answer(callback)
        return

    if data == "set:back:main":
        await state.clear()
        await edit_to_settings_main(callback, lang)
        await safe_callback_answer(callback)
        return

    if data == "set:ac:toggle":
        enabled = await _toggle_bool_setting("auto_confirm")
        msg_key = "auto_confirm_enabled_msg" if enabled else "auto_confirm_disabled_msg"
        await safe_callback_answer(callback, t(lang, msg_key))
        await edit_to_settings_main(callback, lang)
        return

    if data == "set:rm:open":
        await edit_to_reminders(callback, lang)
        await safe_callback_answer(callback)
        return

    if data == "set:rm:toggle":
        await _toggle_bool_setting("reminders_enabled", "true")
        await edit_to_reminders(callback, lang)
        await safe_callback_answer(callback, t(lang, "settings_time_saved"))
        return

    if data == "set:rm:c1":
        await callback.message.edit_text(
            t(lang, "settings_reminder_client1_btn"),
            reply_markup=reminder_client1_presets_kb(lang),
        )
        await safe_callback_answer(callback)
        return

    if data == "set:rm:c2":
        await callback.message.edit_text(
            t(lang, "settings_reminder_client2_btn"),
            reply_markup=reminder_client2_presets_kb(lang),
        )
        await safe_callback_answer(callback)
        return

    if data == "set:rm:adm":
        await callback.message.edit_text(
            t(lang, "settings_reminder_admin_btn"),
            reply_markup=reminder_admin_presets_kb(lang),
        )
        await safe_callback_answer(callback)
        return

    if data.startswith("set:rm:c1:") and parts[-1].isdigit():
        await _save_setting("client_reminder_1_minutes", parts[-1])
        await safe_callback_answer(callback, t(lang, "settings_time_saved"))
        await edit_to_reminders(callback, lang)
        return

    if data.startswith("set:rm:c2:") and parts[-1].isdigit():
        await _save_setting("client_reminder_2_minutes", parts[-1])
        await safe_callback_answer(callback, t(lang, "settings_time_saved"))
        await edit_to_reminders(callback, lang)
        return

    if data.startswith("set:rm:adm:") and parts[-1].isdigit():
        await _save_setting("admin_reminder_minutes", parts[-1])
        await safe_callback_answer(callback, t(lang, "settings_time_saved"))
        await edit_to_reminders(callback, lang)
        return

    if data == "set:rm:c1:manual":
        await _start_minutes_input(state, "client_reminder_1_minutes")
        await callback.message.answer(t(lang, "settings_enter_minutes_prompt"), reply_markup=cancel_kb(lang))
        await safe_callback_answer(callback)
        return

    if data == "set:rm:c2:manual":
        await _start_minutes_input(state, "client_reminder_2_minutes")
        await callback.message.answer(t(lang, "settings_enter_minutes_prompt"), reply_markup=cancel_kb(lang))
        await safe_callback_answer(callback)
        return

    if data == "set:rm:adm:manual":
        await _start_minutes_input(state, "admin_reminder_minutes")
        await callback.message.answer(t(lang, "settings_enter_minutes_prompt"), reply_markup=cancel_kb(lang))
        await safe_callback_answer(callback)
        return

    if data == "set:rm:test:open":
        await edit_to_test_mode(callback, lang)
        await safe_callback_answer(callback)
        return

    if data == "set:rm:test:toggle":
        await _toggle_bool_setting("reminder_test_mode")
        await edit_to_test_mode(callback, lang)
        await safe_callback_answer(callback, t(lang, "settings_time_saved"))
        return

    if data == "set:rm:test:cl:menu":
        await callback.message.edit_text(
            t(lang, "settings_test_client_section"),
            reply_markup=test_client_presets_kb(lang),
        )
        await safe_callback_answer(callback)
        return

    if data == "set:rm:test:ad:menu":
        await callback.message.edit_text(
            t(lang, "settings_test_admin_section"),
            reply_markup=test_admin_presets_kb(lang),
        )
        await safe_callback_answer(callback)
        return

    if data.startswith("set:rm:test:cl:") and parts[-1].isdigit():
        await _save_setting("test_client_reminder_minutes", parts[-1])
        await safe_callback_answer(callback, t(lang, "settings_time_saved"))
        await edit_to_test_mode(callback, lang)
        return

    if data.startswith("set:rm:test:ad:") and parts[-1].isdigit():
        await _save_setting("test_admin_reminder_minutes", parts[-1])
        await safe_callback_answer(callback, t(lang, "settings_time_saved"))
        await edit_to_test_mode(callback, lang)
        return

    if data == "set:enabled:open":
        await edit_to_enabled_languages(callback, lang)
        await safe_callback_answer(callback)
        return

    if data in ("set:enabled:ru", "set:enabled:en", "set:enabled:both"):
        mode = {"set:enabled:ru": "ru", "set:enabled:en": "en", "set:enabled:both": "ru,en"}[data]
        async with async_session_factory() as session:
            enabled = await save_enabled_languages(session, mode)
            await session.commit()
        forced_lang = effective_lang(lang, enabled, enabled[0])
        await safe_callback_answer(callback, t(forced_lang, "enabled_languages_saved"))
        await edit_to_enabled_languages(callback, forced_lang)
        return

    if data == "set:lang:open":
        await edit_to_language(callback, lang)
        await safe_callback_answer(callback)
        return

    if data in ("set:lang:ru", "set:lang:en"):
        new_lang = parts[-1]
        async with async_session_factory() as session:
            snapshot = await load_bot_settings_snapshot(session, callback.from_user.id)
            if new_lang not in snapshot.enabled_languages:
                await safe_callback_answer(callback, t(lang, "unsupported_language"), show_alert=True)
                return
            await ClientRepository(session).set_language(callback.from_user.id, new_lang)
            await session.commit()
        await safe_callback_answer(callback)
        await callback.message.answer(t(new_lang, "language_set"), reply_markup=admin_menu(new_lang))
        await edit_to_settings_main(callback, new_lang)
        return

    if data == "set:contact:open":
        await edit_to_contact(callback, lang)
        await safe_callback_answer(callback)
        return

    if data == "set:contact:edit":
        await state.update_data(flow_origin="admin")
        await state.set_state(AdminSettingsStates.entering_contact)
        await callback.message.answer(t(lang, "settings_contact_prompt"), reply_markup=cancel_kb(lang))
        await safe_callback_answer(callback)
        return

    if data == "set:contact:clear":
        await _save_setting("contact_admin_username", "")
        await safe_callback_answer(callback, t(lang, "settings_contact_cleared"))
        await edit_to_contact(callback, lang)
        return

    if data == "set:adv:open":
        await edit_to_advanced(callback, lang)
        await safe_callback_answer(callback)
        return

    if data == "set:cal:open":
        await edit_to_calendar(callback, lang)
        await safe_callback_answer(callback)
        return

    if data == "set:cal:noop":
        await safe_callback_answer(callback, t(lang, "settings_calendar_env_note"), show_alert=True)
        return

    if data == "set:cal:toggle":
        settings = get_settings()
        if not settings.google_calendar_enabled:
            await safe_callback_answer(callback, t(lang, "settings_calendar_env_note"), show_alert=True)
            return
        await safe_callback_answer(callback)
        async with async_session_factory() as session:
            repo = SettingsRepository(session)
            cal = await repo.get_calendar_settings()
            new_val = not cal.google_calendar_enabled
            await repo.set_calendar_enabled(new_val)
            await session.commit()
        msg_key = "calendar_enabled_msg" if new_val else "calendar_disabled_msg"
        await callback.message.answer(t(lang, msg_key))
        await edit_to_calendar(callback, lang)
        return

    if data == "set:cal:test":
        await safe_callback_answer(callback)
        status_msg = await callback.message.answer(t(lang, "calendar_test_checking"))
        async with async_session_factory() as session:
            result = await CalendarService(session).test_connection()
        if result.message_key == "calendar_test_missing_credentials":
            text = t(lang, result.message_key, missing=", ".join(result.missing))
        elif result.detail:
            text = t(lang, result.message_key, detail=result.detail)
        else:
            text = t(lang, result.message_key)
        try:
            await status_msg.edit_text(text)
        except Exception:
            await callback.message.answer(text)
        return

    if data == "set:adv:keys":
        await callback.message.edit_text(
            f"{t(lang, 'settings_advanced_keys_title')}\n\n{t(lang, 'settings_advanced_keys_list')}",
            reply_markup=settings_advanced_keys_kb(lang),
        )
        await safe_callback_answer(callback)
        return

    if data == "set:adv:manual":
        await state.update_data(flow_origin="admin")
        await state.set_state(AdminSettingsStates.entering_value)
        await callback.message.answer(t(lang, "settings_advanced_manual_prompt"))
        await safe_callback_answer(callback)
        return

    await safe_callback_answer(callback)


async def _start_minutes_input(state: FSMContext, field_key: str) -> None:
    await state.update_data(flow_origin="admin", settings_field=field_key)
    await state.set_state(AdminSettingsStates.entering_reminder_minutes)


@router.message(AdminSettingsStates.entering_reminder_minutes, F.text)
async def save_reminder_minutes(message: Message, state: FSMContext, lang: str) -> None:
    text = message.text.strip()
    if not text.isdigit():
        await message.answer(t(lang, "settings_invalid_minutes"))
        return
    minutes = int(text)
    if minutes <= 0 or minutes > MAX_REMINDER_MINUTES:
        await message.answer(t(lang, "settings_invalid_minutes"))
        return

    data = await state.get_data()
    field_key = data.get("settings_field", "client_reminder_1_minutes")
    await _save_setting(field_key, str(minutes))
    await state.clear()
    await message.answer(t(lang, "settings_time_saved"))
    await send_settings_main(message, lang, message.from_user.id)


@router.message(AdminSettingsStates.entering_contact, F.text)
async def save_contact(message: Message, state: FSMContext, lang: str) -> None:
    text = message.text.strip()
    if text in ("-", ""):
        await message.answer(t(lang, "settings_contact_invalid"))
        return
    username = text.lstrip("@")
    if not USERNAME_RE.match(text if text.startswith("@") else f"@{username}"):
        await message.answer(t(lang, "settings_contact_invalid"))
        return
    await _save_setting("contact_admin_username", username)
    await state.clear()
    await message.answer(t(lang, "settings_contact_saved"))
    await send_settings_main(message, lang, message.from_user.id)


@router.message(AdminSettingsStates.entering_value, F.text)
async def save_advanced_setting(message: Message, state: FSMContext, lang: str) -> None:
    if "=" not in message.text:
        await message.answer(t(lang, "invalid_format"))
        return
    key, value = message.text.split("=", 1)
    async with async_session_factory() as session:
        await SettingsRepository(session).set(key.strip(), value.strip())
        await session.commit()
    await state.clear()
    await message.answer(t(lang, "settings_saved", key=key.strip()))
    await send_settings_main(message, lang, message.from_user.id)
