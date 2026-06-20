"""Admin-configurable /start screen (text + optional Telegram photo file_id per language)."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.i18n import t
from app.bot.keyboards import main_menu
from app.config import get_settings
from app.database.session import async_session_factory
from app.repositories import SettingsRepository

logger = logging.getLogger(__name__)

START_TEXT_MAX_LEN = 1000
TELEGRAM_CAPTION_LIMIT = 1024

KEY_START_TEXT_RU = "start_text_ru"
KEY_START_TEXT_EN = "start_text_en"
KEY_START_PHOTO_FILE_ID_RU = "start_photo_file_id_ru"
KEY_START_PHOTO_FILE_ID_EN = "start_photo_file_id_en"
KEY_START_PHOTO_ENABLED_RU = "start_photo_enabled_ru"
KEY_START_PHOTO_ENABLED_EN = "start_photo_enabled_en"
# Legacy keys (fallback when language-specific photo is missing)
KEY_START_PHOTO_FILE_ID = "start_photo_file_id"
KEY_START_PHOTO_ENABLED = "start_photo_enabled"

DEFAULT_START_TEXT: dict[str, str] = {
    "ru": (
        "👋 Добро пожаловать в бот записи!\n"
        "Запишитесь на услугу, посмотрите свои записи или свяжитесь с администратором."
    ),
    "en": (
        "👋 Welcome to the booking bot!\n"
        "Book a service, view your bookings, or contact the admin."
    ),
}


@dataclass(frozen=True)
class StartScreenConfig:
    start_text_ru: str | None
    start_text_en: str | None
    start_photo_file_id_ru: str | None
    start_photo_file_id_en: str | None
    start_photo_enabled_ru: bool
    start_photo_enabled_en: bool
    start_photo_file_id: str | None
    start_photo_enabled: bool

    def has_custom_ru(self) -> bool:
        return bool(self.start_text_ru and self.start_text_ru.strip())

    def has_custom_en(self) -> bool:
        return bool(self.start_text_en and self.start_text_en.strip())

    def has_photo_ru(self) -> bool:
        return bool(self.start_photo_file_id_ru and self.start_photo_file_id_ru.strip())

    def has_photo_en(self) -> bool:
        return bool(self.start_photo_file_id_en and self.start_photo_file_id_en.strip())

    def has_legacy_photo(self) -> bool:
        return bool(self.start_photo_file_id and self.start_photo_file_id.strip())

    def can_toggle_photo(self, photo_lang: str) -> bool:
        if photo_lang == "ru":
            return self.has_photo_ru() or self.has_legacy_photo()
        return self.has_photo_en() or self.has_legacy_photo()


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def _clean(value: str | None) -> str | None:
    if value and value.strip():
        return value.strip()
    return None


async def load_start_screen_config(session: AsyncSession) -> StartScreenConfig:
    repo = SettingsRepository(session)
    return StartScreenConfig(
        start_text_ru=_clean(await repo.get(KEY_START_TEXT_RU)),
        start_text_en=_clean(await repo.get(KEY_START_TEXT_EN)),
        start_photo_file_id_ru=_clean(await repo.get(KEY_START_PHOTO_FILE_ID_RU)),
        start_photo_file_id_en=_clean(await repo.get(KEY_START_PHOTO_FILE_ID_EN)),
        start_photo_enabled_ru=_parse_bool(await repo.get(KEY_START_PHOTO_ENABLED_RU), False),
        start_photo_enabled_en=_parse_bool(await repo.get(KEY_START_PHOTO_ENABLED_EN), False),
        start_photo_file_id=_clean(await repo.get(KEY_START_PHOTO_FILE_ID)),
        start_photo_enabled=_parse_bool(await repo.get(KEY_START_PHOTO_ENABLED), False),
    )


async def save_start_text(session: AsyncSession, lang: str, text: str) -> None:
    key = KEY_START_TEXT_RU if lang == "ru" else KEY_START_TEXT_EN
    await SettingsRepository(session).set(key, text.strip())


async def save_start_photo(session: AsyncSession, photo_lang: str, file_id: str) -> None:
    repo = SettingsRepository(session)
    if photo_lang == "ru":
        await repo.set(KEY_START_PHOTO_FILE_ID_RU, file_id)
        await repo.set(KEY_START_PHOTO_ENABLED_RU, "true")
    else:
        await repo.set(KEY_START_PHOTO_FILE_ID_EN, file_id)
        await repo.set(KEY_START_PHOTO_ENABLED_EN, "true")


async def set_start_photo_enabled(session: AsyncSession, photo_lang: str, enabled: bool) -> None:
    key = KEY_START_PHOTO_ENABLED_RU if photo_lang == "ru" else KEY_START_PHOTO_ENABLED_EN
    await SettingsRepository(session).set(key, "true" if enabled else "false")


async def reset_start_screen(session: AsyncSession) -> None:
    repo = SettingsRepository(session)
    bool_keys = {
        KEY_START_PHOTO_ENABLED,
        KEY_START_PHOTO_ENABLED_RU,
        KEY_START_PHOTO_ENABLED_EN,
    }
    for key in (
        KEY_START_TEXT_RU,
        KEY_START_TEXT_EN,
        KEY_START_PHOTO_FILE_ID,
        KEY_START_PHOTO_FILE_ID_RU,
        KEY_START_PHOTO_FILE_ID_EN,
        KEY_START_PHOTO_ENABLED,
        KEY_START_PHOTO_ENABLED_RU,
        KEY_START_PHOTO_ENABLED_EN,
    ):
        if await repo.get(key) is not None:
            await repo.set(key, "false" if key in bool_keys else "")


def resolve_start_text(
    config: StartScreenConfig,
    lang: str,
    *,
    contact_username: str | None = None,
) -> str:
    settings = get_settings()
    custom = config.start_text_ru if lang == "ru" else config.start_text_en
    if custom:
        return custom
    text = DEFAULT_START_TEXT.get(lang) or DEFAULT_START_TEXT[settings.default_language]
    if not text:
        text = DEFAULT_START_TEXT["ru"]
    if contact_username:
        text = f"{text}{t(lang, 'support_line', username=contact_username.lstrip('@'))}"
    return text


def resolve_photo_for_lang(config: StartScreenConfig, lang: str) -> tuple[str | None, bool]:
    """Return (file_id, use_photo) for the given user/preview language."""
    if lang == "ru":
        file_id = config.start_photo_file_id_ru
        enabled = config.start_photo_enabled_ru
    else:
        file_id = config.start_photo_file_id_en
        enabled = config.start_photo_enabled_en

    file_id = _clean(file_id)
    if enabled and file_id:
        return file_id, True

    if config.start_photo_enabled and config.has_legacy_photo():
        return config.start_photo_file_id, True

    return None, False


def format_photo_status_line(config: StartScreenConfig, photo_lang: str, ui_lang: str) -> str:
    if photo_lang == "ru":
        has_photo = config.has_photo_ru()
        enabled = config.start_photo_enabled_ru
    else:
        has_photo = config.has_photo_en()
        enabled = config.start_photo_enabled_en
    photo = t(ui_lang, "start_screen_photo_set" if has_photo else "start_screen_photo_not_set")
    display = t(ui_lang, "label_enabled" if enabled else "label_disabled")
    return f"{photo}, {display}"


async def _send_start_payload(
    *,
    bot: Bot | None,
    message: Message | None,
    chat_id: int,
    is_admin: bool,
    screen_lang: str,
    config: StartScreenConfig,
    contact_username: str | None,
) -> None:
    text = resolve_start_text(config, screen_lang, contact_username=contact_username)
    from app.bot.utils.menu_helpers import menu_mode_kwargs

    async with async_session_factory() as session:
        kwargs = await menu_mode_kwargs(session)
    keyboard = main_menu(is_admin, screen_lang, **kwargs)
    file_id, use_photo = resolve_photo_for_lang(config, screen_lang)

    if not use_photo or not file_id:
        if message is not None:
            await message.answer(text, reply_markup=keyboard)
        else:
            assert bot is not None
            await bot.send_message(chat_id, text, reply_markup=keyboard)
        return

    if len(text) <= TELEGRAM_CAPTION_LIMIT:
        try:
            if message is not None:
                await message.answer_photo(file_id, caption=text, reply_markup=keyboard)
            else:
                assert bot is not None
                await bot.send_photo(chat_id, file_id, caption=text, reply_markup=keyboard)
            return
        except TelegramBadRequest as exc:
            logger.warning(
                "Start screen photo+caption failed (lang=%s), falling back: %s",
                screen_lang,
                exc,
            )

    try:
        short = text[:TELEGRAM_CAPTION_LIMIT] if len(text) > TELEGRAM_CAPTION_LIMIT else text
        if message is not None:
            await message.answer_photo(file_id, caption=short if short else None)
        else:
            assert bot is not None
            await bot.send_photo(chat_id, file_id, caption=short if short else None)
    except TelegramBadRequest as exc:
        logger.warning(
            "Start screen photo invalid (lang=%s, file_id), text only: %s",
            screen_lang,
            exc,
        )
        if message is not None:
            await message.answer(text, reply_markup=keyboard)
        else:
            assert bot is not None
            await bot.send_message(chat_id, text, reply_markup=keyboard)
        return

    if message is not None:
        await message.answer(text, reply_markup=keyboard)
    else:
        assert bot is not None
        await bot.send_message(chat_id, text, reply_markup=keyboard)


async def deliver_start_screen(
    message: Message,
    *,
    is_admin: bool,
    lang: str,
    config: StartScreenConfig | None = None,
    contact_username: str | None = None,
) -> None:
    from app.database.session import async_session_factory

    if config is None or contact_username is None:
        async with async_session_factory() as session:
            if config is None:
                config = await load_start_screen_config(session)
            if contact_username is None:
                contact = await SettingsRepository(session).get("contact_admin_username")
                settings = get_settings()
                contact_username = contact or settings.contact_admin_username or None

    await _send_start_payload(
        bot=None,
        message=message,
        chat_id=message.chat.id,
        is_admin=is_admin,
        screen_lang=lang,
        config=config,
        contact_username=contact_username,
    )


async def send_start_screen_preview(
    bot: Bot,
    chat_id: int,
    *,
    is_admin: bool,
    preview_lang: str,
) -> None:
    from app.database.session import async_session_factory

    async with async_session_factory() as session:
        config = await load_start_screen_config(session)
        contact = await SettingsRepository(session).get("contact_admin_username")
        settings = get_settings()
        contact_username = contact or settings.contact_admin_username or None

    await _send_start_payload(
        bot=bot,
        message=None,
        chat_id=chat_id,
        is_admin=is_admin,
        screen_lang=preview_lang,
        config=config,
        contact_username=contact_username,
    )
