"""Bot language mode: enabled languages, effective user language, and sync cache."""

from __future__ import annotations

from app.bot.i18n import t
from app.config import get_settings
from app.database.session import async_session_factory
from app.repositories import ClientRepository, SettingsRepository

VALID_LANG_CODES = frozenset({"ru", "en"})
DEFAULT_ENABLED = ("ru", "en")

_enabled_languages_cache: list[str] = list(DEFAULT_ENABLED)


def parse_enabled_languages_value(value: str | None) -> list[str]:
    if not value or not value.strip():
        return list(DEFAULT_ENABLED)
    parts = [part.strip() for part in value.split(",") if part.strip() in VALID_LANG_CODES]
    if not parts:
        return list(DEFAULT_ENABLED)
    # Preserve order ru, en
    ordered: list[str] = []
    for code in ("ru", "en"):
        if code in parts:
            ordered.append(code)
    return ordered or list(DEFAULT_ENABLED)


def parse_enabled_languages_list(values: list[str] | None) -> list[str]:
    if not values:
        return list(DEFAULT_ENABLED)
    return parse_enabled_languages_value(",".join(values))


def serialize_enabled_languages(codes: list[str]) -> str:
    normalized = parse_enabled_languages_value(",".join(codes))
    if normalized == ["ru"]:
        return "ru"
    if normalized == ["en"]:
        return "en"
    return "ru,en"


def effective_lang(user_lang: str | None, enabled_languages: list[str], default_lang: str) -> str:
    enabled = parse_enabled_languages_value(",".join(enabled_languages))
    if len(enabled) == 1:
        return enabled[0]
    if user_lang and user_lang in enabled:
        return user_lang
    if default_lang in enabled:
        return default_lang
    return enabled[0]


def is_language_switching_enabled(enabled_languages: list[str] | None = None) -> bool:
    enabled = enabled_languages if enabled_languages is not None else get_enabled_languages_sync()
    return len(parse_enabled_languages_value(",".join(enabled))) > 1


def enabled_languages_mode_label(lang: str, codes: list[str]) -> str:
    normalized = parse_enabled_languages_value(",".join(codes))
    if normalized == ["ru"]:
        return t(lang, "enabled_languages_mode_ru")
    if normalized == ["en"]:
        return t(lang, "enabled_languages_mode_en")
    return t(lang, "enabled_languages_mode_both")


def get_enabled_languages_sync() -> list[str]:
    return list(_enabled_languages_cache)


def set_enabled_languages_cache(codes: list[str]) -> None:
    global _enabled_languages_cache
    _enabled_languages_cache = parse_enabled_languages_value(",".join(codes))


async def load_enabled_languages(session) -> list[str]:
    repo = SettingsRepository(session)
    stored = await repo.get("enabled_languages")
    if stored:
        return parse_enabled_languages_value(stored)
    settings = get_settings()
    if settings.enabled_languages:
        return parse_enabled_languages_value(settings.enabled_languages)
    return parse_enabled_languages_list(settings.supported_languages)


async def get_effective_default_language(session) -> str:
    enabled = await load_enabled_languages(session)
    if len(enabled) == 1:
        return enabled[0]
    stored = await SettingsRepository(session).get("default_language")
    settings = get_settings()
    candidate = stored or settings.default_language
    return effective_lang(None, enabled, candidate)


async def refresh_enabled_languages_cache(session) -> list[str]:
    enabled = await load_enabled_languages(session)
    set_enabled_languages_cache(enabled)
    return enabled


async def save_enabled_languages(session, mode: str) -> list[str]:
    codes = parse_enabled_languages_value(mode)
    repo = SettingsRepository(session)
    await repo.set("enabled_languages", serialize_enabled_languages(codes))
    if len(codes) == 1:
        await repo.set("default_language", codes[0])
    set_enabled_languages_cache(codes)
    return codes


async def init_language_cache() -> None:
    async with async_session_factory() as session:
        await refresh_enabled_languages_cache(session)


async def get_user_language(telegram_id: int) -> str:
    settings = get_settings()
    async with async_session_factory() as session:
        enabled = await load_enabled_languages(session)
        default = await get_effective_default_language(session)
        client = await ClientRepository(session).get_by_telegram_id(telegram_id)
        return resolve_client_lang(
            client,
            enabled_languages=enabled,
            default_language=default or settings.default_language,
        )


def resolve_client_lang(
    client,
    *,
    enabled_languages: list[str] | None = None,
    default_language: str | None = None,
) -> str:
    """Pick language for proactive client messages (reminders, notifications).

    1. Use client.language only when it is a supported bot language.
    2. Otherwise use the configured default language.
    3. Never use Telegram language_code here.
    4. English is used only when it is the effective default / sole enabled language.
    """
    settings = get_settings()
    if enabled_languages is not None:
        enabled = parse_enabled_languages_value(",".join(enabled_languages))
    else:
        enabled = parse_enabled_languages_value(",".join(get_enabled_languages_sync()))
    default = default_language or settings.default_language
    user_lang: str | None = None
    if client and client.language:
        lang = str(client.language).strip()
        if lang in VALID_LANG_CODES and lang in enabled:
            user_lang = lang
    return effective_lang(user_lang, enabled, default)


async def resolve_client_lang_for_client(client) -> str:
    async with async_session_factory() as session:
        enabled = await load_enabled_languages(session)
        default = await get_effective_default_language(session)
    return resolve_client_lang(client, enabled_languages=enabled, default_language=default)
