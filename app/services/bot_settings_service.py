from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.repositories import ClientRepository, SettingsRepository
from app.services.language_service import (
    effective_lang,
    get_effective_default_language,
    load_enabled_languages,
)
from app.services.reminder_settings import ReminderConfig, load_reminder_config


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class BotSettingsSnapshot:
    auto_confirm: bool
    reminders: ReminderConfig
    contact_admin_username: str | None
    admin_language: str
    enabled_languages: list[str]


async def load_bot_settings_snapshot(session: AsyncSession, telegram_id: int) -> BotSettingsSnapshot:
    settings = get_settings()
    repo = SettingsRepository(session)
    reminders = await load_reminder_config(session)

    auto_confirm = _parse_bool(await repo.get("auto_confirm"), False)
    contact = await repo.get("contact_admin_username")
    if not contact and settings.contact_admin_username:
        contact = settings.contact_admin_username

    client = await ClientRepository(session).get_by_telegram_id(telegram_id)
    enabled_languages = await load_enabled_languages(session)
    default_lang = await get_effective_default_language(session)
    user_lang = client.language if client and client.language else default_lang
    admin_language = effective_lang(user_lang, enabled_languages, default_lang)

    return BotSettingsSnapshot(
        auto_confirm=auto_confirm,
        reminders=reminders,
        contact_admin_username=contact or None,
        admin_language=admin_language,
        enabled_languages=enabled_languages,
    )
