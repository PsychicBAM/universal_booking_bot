from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.repositories import SettingsRepository


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def _parse_int(value: str | None, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value.strip())
    except ValueError:
        return default


@dataclass(frozen=True)
class ReminderConfig:
    enabled: bool
    test_mode: bool
    client_reminder_1_minutes: int
    client_reminder_2_minutes: int
    admin_reminder_minutes: int
    test_client_reminder_minutes: int
    test_admin_reminder_minutes: int


def reminder_config_from_settings(settings: Settings) -> ReminderConfig:
    return ReminderConfig(
        enabled=settings.reminders_enabled,
        test_mode=settings.reminder_test_mode,
        client_reminder_1_minutes=settings.client_reminder_1_minutes,
        client_reminder_2_minutes=settings.client_reminder_2_minutes,
        admin_reminder_minutes=settings.admin_reminder_minutes,
        test_client_reminder_minutes=settings.test_client_reminder_minutes,
        test_admin_reminder_minutes=settings.test_admin_reminder_minutes,
    )


async def load_reminder_config(session: AsyncSession) -> ReminderConfig:
    settings = get_settings()
    base = reminder_config_from_settings(settings)
    repo = SettingsRepository(session)

    db_enabled = await repo.get("reminders_enabled")
    db_test_mode = await repo.get("reminder_test_mode")
    db_r1 = await repo.get("client_reminder_1_minutes")
    db_r2 = await repo.get("client_reminder_2_minutes")
    db_admin = await repo.get("admin_reminder_minutes")
    db_test_client = await repo.get("test_client_reminder_minutes")
    db_test_admin = await repo.get("test_admin_reminder_minutes")

    return ReminderConfig(
        enabled=_parse_bool(db_enabled, base.enabled),
        test_mode=_parse_bool(db_test_mode, base.test_mode),
        client_reminder_1_minutes=_parse_int(db_r1, base.client_reminder_1_minutes),
        client_reminder_2_minutes=_parse_int(db_r2, base.client_reminder_2_minutes),
        admin_reminder_minutes=_parse_int(db_admin, base.admin_reminder_minutes),
        test_client_reminder_minutes=_parse_int(db_test_client, base.test_client_reminder_minutes),
        test_admin_reminder_minutes=_parse_int(db_test_admin, base.test_admin_reminder_minutes),
    )
