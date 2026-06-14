from aiogram.types import CallbackQuery, Message

from app.bot.i18n import format_duration, t
from app.bot.keyboards.settings_kb import (
    reminder_admin_presets_kb,
    reminder_client1_presets_kb,
    reminder_client2_presets_kb,
    settings_advanced_kb,
    settings_calendar_kb,
    settings_contact_kb,
    settings_language_kb,
    settings_main_kb,
    settings_reminders_kb,
    settings_test_kb,
    test_admin_presets_kb,
    test_client_presets_kb,
)
from app.config import get_settings
from app.database.session import async_session_factory
from app.repositories import SettingsRepository
from app.services.bot_settings_service import BotSettingsSnapshot, load_bot_settings_snapshot


def _enabled_label(lang: str, enabled: bool) -> str:
    return t(lang, "label_enabled") if enabled else t(lang, "label_disabled")


def _language_display(lang: str) -> str:
    return t(lang, "lang_name_ru") if lang == "ru" else t(lang, "lang_name_en")


def _contact_display(lang: str, username: str | None) -> str:
    if not username:
        return t(lang, "settings_contact_not_set")
    return f"@{username.lstrip('@')}"


def format_settings_main_text(snapshot: BotSettingsSnapshot, lang: str) -> str:
    return t(
        lang,
        "settings_menu_body",
        auto_confirm=_enabled_label(lang, snapshot.auto_confirm),
        reminders=_enabled_label(lang, snapshot.reminders.enabled),
        language=_language_display(snapshot.admin_language),
        contact=_contact_display(lang, snapshot.contact_admin_username),
    )


def format_reminders_text(snapshot: BotSettingsSnapshot, lang: str) -> str:
    rm = snapshot.reminders
    return t(
        lang,
        "settings_reminders_body",
        status=_enabled_label(lang, rm.enabled),
        client1=format_duration(lang, rm.client_reminder_1_minutes),
        client2=format_duration(lang, rm.client_reminder_2_minutes),
        admin=format_duration(lang, rm.admin_reminder_minutes),
        test_mode=_enabled_label(lang, rm.test_mode),
    )


def format_test_mode_text(snapshot: BotSettingsSnapshot, lang: str) -> str:
    rm = snapshot.reminders
    return t(
        lang,
        "settings_test_body",
        status=_enabled_label(lang, rm.test_mode),
        client=format_duration(lang, rm.test_client_reminder_minutes),
        admin=format_duration(lang, rm.test_admin_reminder_minutes),
    )


def format_contact_text(snapshot: BotSettingsSnapshot, lang: str) -> str:
    return t(
        lang,
        "settings_contact_body",
        contact=_contact_display(lang, snapshot.contact_admin_username),
    )


async def get_snapshot(telegram_id: int) -> BotSettingsSnapshot:
    async with async_session_factory() as session:
        return await load_bot_settings_snapshot(session, telegram_id)


async def send_settings_main(message: Message, lang: str, telegram_id: int) -> None:
    snapshot = await get_snapshot(telegram_id)
    await message.answer(
        f"{t(lang, 'settings_menu_title')}\n\n{format_settings_main_text(snapshot, lang)}",
        reply_markup=settings_main_kb(snapshot, lang),
    )


async def send_settings_main_after_cancel(message: Message, lang: str, telegram_id: int) -> None:
    await send_settings_main(message, lang, telegram_id)


async def edit_to_settings_main(callback: CallbackQuery, lang: str) -> None:
    snapshot = await get_snapshot(callback.from_user.id)
    await callback.message.edit_text(
        f"{t(lang, 'settings_menu_title')}\n\n{format_settings_main_text(snapshot, lang)}",
        reply_markup=settings_main_kb(snapshot, lang),
    )


async def edit_to_reminders(callback: CallbackQuery, lang: str) -> None:
    snapshot = await get_snapshot(callback.from_user.id)
    await callback.message.edit_text(
        f"{t(lang, 'settings_reminders_title')}\n\n{format_reminders_text(snapshot, lang)}",
        reply_markup=settings_reminders_kb(snapshot, lang),
    )


async def edit_to_test_mode(callback: CallbackQuery, lang: str) -> None:
    snapshot = await get_snapshot(callback.from_user.id)
    await callback.message.edit_text(
        f"{t(lang, 'settings_test_title')}\n\n{format_test_mode_text(snapshot, lang)}",
        reply_markup=settings_test_kb(snapshot, lang),
    )


async def edit_to_contact(callback: CallbackQuery, lang: str) -> None:
    snapshot = await get_snapshot(callback.from_user.id)
    await callback.message.edit_text(
        f"{t(lang, 'settings_contact_title')}\n\n{format_contact_text(snapshot, lang)}",
        reply_markup=settings_contact_kb(lang),
    )


async def edit_to_language(callback: CallbackQuery, lang: str) -> None:
    await callback.message.edit_text(
        t(lang, "settings_language_title"),
        reply_markup=settings_language_kb(lang),
    )


async def edit_to_advanced(callback: CallbackQuery, lang: str) -> None:
    await callback.message.edit_text(
        f"{t(lang, 'settings_advanced_title')}\n\n{t(lang, 'settings_advanced_body')}",
        reply_markup=settings_advanced_kb(lang),
    )


async def _calendar_state(session) -> tuple[bool, bool, str]:
    settings = get_settings()
    cal = await SettingsRepository(session).get_calendar_settings()
    env_on = settings.google_calendar_enabled
    db_on = cal.google_calendar_enabled
    calendar_id = cal.google_calendar_id or settings.google_calendar_id or "primary"
    return env_on, db_on, calendar_id


def format_calendar_text(lang: str, env_on: bool, db_on: bool, calendar_id: str) -> str:
    effective = env_on and db_on
    body = t(
        lang,
        "settings_calendar_body",
        status=_enabled_label(lang, effective),
        calendar_id=calendar_id,
        sync=_enabled_label(lang, effective),
        env_status=_enabled_label(lang, env_on),
    )
    if not env_on:
        body = f"{body}\n\n{t(lang, 'settings_calendar_env_note')}"
    return body


async def edit_to_calendar(callback: CallbackQuery, lang: str) -> None:
    async with async_session_factory() as session:
        env_on, db_on, calendar_id = await _calendar_state(session)
    await callback.message.edit_text(
        f"{t(lang, 'settings_calendar_title')}\n\n{format_calendar_text(lang, env_on, db_on, calendar_id)}",
        reply_markup=settings_calendar_kb(lang, env_on, db_on),
    )


async def send_calendar_screen(message: Message, lang: str) -> None:
    async with async_session_factory() as session:
        env_on, db_on, calendar_id = await _calendar_state(session)
    await message.answer(
        f"{t(lang, 'settings_calendar_title')}\n\n{format_calendar_text(lang, env_on, db_on, calendar_id)}",
        reply_markup=settings_calendar_kb(lang, env_on, db_on),
    )

