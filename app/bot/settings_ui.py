from aiogram.types import CallbackQuery, Message

from app.bot.i18n import format_duration, t
from app.bot.keyboards.settings_kb import (
    reminder_admin_presets_kb,
    reminder_client1_presets_kb,
    reminder_client2_presets_kb,
    settings_advanced_kb,
    settings_calendar_kb,
    settings_contact_kb,
    settings_enabled_languages_kb,
    settings_language_kb,
    settings_main_kb,
    settings_reminders_kb,
    settings_test_kb,
    test_admin_presets_kb,
    test_client_presets_kb,
)
from app.bot.keyboards.start_screen_kb import start_screen_menu_kb
from app.config import get_settings
from app.database.session import async_session_factory
from app.repositories import SettingsRepository
from app.services.bot_settings_service import BotSettingsSnapshot, load_bot_settings_snapshot
from app.services.language_service import enabled_languages_mode_label, parse_enabled_languages_value
from app.services.start_screen_service import (
    StartScreenConfig,
    format_photo_status_line,
    load_start_screen_config,
)


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
    snapshot = await get_snapshot(callback.from_user.id)
    await callback.message.edit_text(
        t(lang, "settings_language_title"),
        reply_markup=settings_language_kb(lang, snapshot.enabled_languages),
    )


async def edit_to_enabled_languages(callback: CallbackQuery, lang: str) -> None:
    snapshot = await get_snapshot(callback.from_user.id)
    await callback.message.edit_text(
        f"{t(lang, 'settings_enabled_languages_title')}\n\n"
        f"{t(lang, 'settings_enabled_languages_body', current=enabled_languages_mode_label(lang, snapshot.enabled_languages))}",
        reply_markup=settings_enabled_languages_kb(lang),
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


def format_start_screen_text(config: StartScreenConfig, lang: str, enabled_languages: list[str] | None = None) -> str:
    codes = parse_enabled_languages_value(",".join(enabled_languages or ["ru", "en"]))
    if len(codes) == 1:
        code = codes[0]
        text_status = t(
            lang,
            "start_screen_text_custom" if (config.has_custom_ru() if code == "ru" else config.has_custom_en()) else "start_screen_text_default",
        )
        photo_status = format_photo_status_line(config, code, lang)
        return t(lang, "start_screen_menu_body_single", text=text_status, photo=photo_status)
    ru_status = t(
        lang,
        "start_screen_text_custom" if config.has_custom_ru() else "start_screen_text_default",
    )
    en_status = t(
        lang,
        "start_screen_text_custom" if config.has_custom_en() else "start_screen_text_default",
    )
    photo_ru = format_photo_status_line(config, "ru", lang)
    photo_en = format_photo_status_line(config, "en", lang)
    return t(
        lang,
        "start_screen_menu_body",
        text_ru=ru_status,
        text_en=en_status,
        photo_ru=photo_ru,
        photo_en=photo_en,
    )


async def send_start_screen_menu(message: Message, lang: str) -> None:
    async with async_session_factory() as session:
        config = await load_start_screen_config(session)
        snapshot = await load_bot_settings_snapshot(session, message.from_user.id)
    await message.answer(
        f"{t(lang, 'start_screen_menu_title')}\n\n{format_start_screen_text(config, lang, snapshot.enabled_languages)}",
        reply_markup=start_screen_menu_kb(config, lang, snapshot.enabled_languages),
    )


async def edit_to_start_screen(callback: CallbackQuery, lang: str) -> None:
    async with async_session_factory() as session:
        config = await load_start_screen_config(session)
        snapshot = await load_bot_settings_snapshot(session, callback.from_user.id)
    await callback.message.edit_text(
        f"{t(lang, 'start_screen_menu_title')}\n\n{format_start_screen_text(config, lang, snapshot.enabled_languages)}",
        reply_markup=start_screen_menu_kb(config, lang, snapshot.enabled_languages),
    )

