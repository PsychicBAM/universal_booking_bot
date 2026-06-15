from __future__ import annotations

import re
from dataclasses import dataclass

from aiogram.types import User
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.i18n import t
from app.repositories import SettingsRepository

PHONE_PATTERN = re.compile(r"^[\d\s+\-()]+$")
MAX_CLIENT_NAME_LEN = 100
MAX_PHONE_LEN = 30

CLIENT_DATA_SETTING_KEYS = (
    "client_use_telegram_name",
    "client_confirm_telegram_name",
    "client_phone_request_contact",
    "client_phone_manual_input",
    "client_phone_required",
    "client_fast_reuse_saved_data",
)


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class ClientDataSettings:
    use_telegram_name: bool
    confirm_telegram_name: bool
    phone_request_contact: bool
    phone_manual_input: bool
    phone_required: bool
    fast_reuse_saved_data: bool


def build_telegram_full_name(user: User | None) -> str | None:
    if not user:
        return None
    parts = [p for p in (user.first_name, user.last_name) if p]
    if not parts:
        return None
    full = " ".join(parts).strip()
    return full[:MAX_CLIENT_NAME_LEN] if full else None


def is_valid_phone_config(settings: ClientDataSettings) -> bool:
    if settings.phone_required:
        return settings.phone_request_contact or settings.phone_manual_input
    return True


def validate_client_name(name: str) -> bool:
    stripped = (name or "").strip()
    return bool(stripped) and len(stripped) <= MAX_CLIENT_NAME_LEN


def validate_manual_phone(phone: str, *, required: bool) -> bool:
    stripped = (phone or "").strip()
    if not stripped:
        return not required
    if len(stripped) > MAX_PHONE_LEN:
        return False
    return bool(PHONE_PATTERN.match(stripped))


async def load_client_data_settings(session: AsyncSession) -> ClientDataSettings:
    repo = SettingsRepository(session)
    return ClientDataSettings(
        use_telegram_name=_parse_bool(await repo.get("client_use_telegram_name"), True),
        confirm_telegram_name=_parse_bool(await repo.get("client_confirm_telegram_name"), True),
        phone_request_contact=_parse_bool(await repo.get("client_phone_request_contact"), True),
        phone_manual_input=_parse_bool(await repo.get("client_phone_manual_input"), True),
        phone_required=_parse_bool(await repo.get("client_phone_required"), True),
        fast_reuse_saved_data=_parse_bool(await repo.get("client_fast_reuse_saved_data"), True),
    )


async def save_client_data_settings(session: AsyncSession, settings: ClientDataSettings) -> None:
    repo = SettingsRepository(session)
    mapping = {
        "client_use_telegram_name": settings.use_telegram_name,
        "client_confirm_telegram_name": settings.confirm_telegram_name,
        "client_phone_request_contact": settings.phone_request_contact,
        "client_phone_manual_input": settings.phone_manual_input,
        "client_phone_required": settings.phone_required,
        "client_fast_reuse_saved_data": settings.fast_reuse_saved_data,
    }
    for key, value in mapping.items():
        await repo.set(key, "true" if value else "false")


def format_client_data_settings_summary(settings: ClientDataSettings, lang: str) -> str:
    def on_off(enabled: bool) -> str:
        return t(lang, "label_enabled") if enabled else t(lang, "label_disabled")

    def yes_no(enabled: bool) -> str:
        return t(lang, "yes") if enabled else t(lang, "no")

    return "\n".join(
        [
            t(lang, "client_data_settings_title"),
            "",
            t(lang, "client_data_settings_intro"),
            "",
            t(lang, "client_use_telegram_name", value=on_off(settings.use_telegram_name)),
            t(lang, "client_confirm_telegram_name", value=on_off(settings.confirm_telegram_name)),
            t(lang, "client_phone_request_contact", value=on_off(settings.phone_request_contact)),
            t(lang, "client_phone_manual_input", value=on_off(settings.phone_manual_input)),
            t(lang, "client_phone_required", value=yes_no(settings.phone_required)),
            t(lang, "client_fast_reuse_saved_data", value=on_off(settings.fast_reuse_saved_data)),
        ]
    )


def format_client_data_preview(settings: ClientDataSettings, lang: str) -> str:
    lines = [t(lang, "client_data_preview_title"), ""]
    step = 1
    if settings.use_telegram_name:
        if settings.confirm_telegram_name:
            lines.append(t(lang, "client_data_preview_step_confirm_name", step=str(step)))
        else:
            lines.append(t(lang, "client_data_preview_step_auto_name", step=str(step)))
        step += 1
    else:
        lines.append(t(lang, "client_data_preview_step_manual_name", step=str(step)))
        step += 1

    if settings.phone_required:
        if settings.phone_request_contact and settings.phone_manual_input:
            lines.append(t(lang, "client_data_preview_step_phone_both", step=str(step)))
        elif settings.phone_request_contact:
            lines.append(t(lang, "client_data_preview_step_phone_contact", step=str(step)))
        elif settings.phone_manual_input:
            lines.append(t(lang, "client_data_preview_step_phone_manual", step=str(step)))
        else:
            lines.append(t(lang, "client_data_preview_step_phone_required_missing", step=str(step)))
    else:
        lines.append(t(lang, "client_data_preview_step_phone_optional", step=str(step)))
    step += 1
    if settings.fast_reuse_saved_data:
        lines.append(t(lang, "client_data_preview_step_fast_reuse", step=str(step)))
        step += 1
    lines.append(t(lang, "client_data_preview_step_confirm", step=str(step)))
    return "\n".join(lines)


def resolve_saved_client_name(
    client: Client | None,
    latest_booking: Booking | None,
    user: User | None,
    settings: ClientDataSettings,
) -> str | None:
    if client:
        if client.full_name and client.full_name.strip():
            return client.full_name.strip()[:MAX_CLIENT_NAME_LEN]
        parts = [p.strip() for p in (client.first_name, client.last_name) if p and p.strip()]
        if parts:
            return " ".join(parts)[:MAX_CLIENT_NAME_LEN]
        if client.name and client.name.strip():
            return client.name.strip()[:MAX_CLIENT_NAME_LEN]
    if latest_booking and latest_booking.client_name and latest_booking.client_name.strip():
        return latest_booking.client_name.strip()[:MAX_CLIENT_NAME_LEN]
    if settings.use_telegram_name:
        return build_telegram_full_name(user)
    return None


def resolve_saved_client_phone(client: Client | None, latest_booking: Booking | None) -> str | None:
    if client and client.phone and client.phone.strip():
        return client.phone.strip()
    if latest_booking and latest_booking.client_phone and latest_booking.client_phone.strip():
        return latest_booking.client_phone.strip()
    return None


def is_returning_client(client: Client | None, latest_booking: Booking | None) -> bool:
    return client is not None and latest_booking is not None


def can_fast_reuse_saved_data(
    client: Client | None,
    latest_booking: Booking | None,
    user: User | None,
    settings: ClientDataSettings,
) -> bool:
    if not settings.fast_reuse_saved_data or not is_returning_client(client, latest_booking):
        return False
    name = resolve_saved_client_name(client, latest_booking, user, settings)
    if not name:
        return False
    phone = resolve_saved_client_phone(client, latest_booking)
    if settings.phone_required and not phone:
        return False
    return True


def missing_client_data_fields(
    client: Client | None,
    latest_booking: Booking | None,
    user: User | None,
    settings: ClientDataSettings,
) -> tuple[bool, bool]:
    """Return (need_name, need_phone) for partial collection."""
    name = resolve_saved_client_name(client, latest_booking, user, settings)
    phone = resolve_saved_client_phone(client, latest_booking)
    need_name = not name
    need_phone = settings.phone_required and not phone
    return need_name, need_phone


def phone_source_label(lang: str, source: str | None) -> str:
    if source == "telegram_contact":
        return t(lang, "booking_phone_source_telegram")
    if source in ("manual", "imported"):
        return t(lang, "booking_phone_source_manual")
    return t(lang, "not_provided")
