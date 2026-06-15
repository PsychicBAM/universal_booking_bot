"""Customizable booking confirmation texts (stored in bot_settings with i18n fallbacks)."""

from __future__ import annotations

from dataclasses import dataclass

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.i18n import t
from app.models import Booking
from app.repositories import SettingsRepository
from app.services.reminder_settings import ReminderConfig
from app.bot.utils.attendance_helpers import ATTENDANCE_CONFIRMED, has_attendance_response

TITLE_MAX_LEN = 100
QUESTION_MAX_LEN = 500
BUTTON_MAX_LEN = 40
RESPONSE_MAX_LEN = 500

CONFIRM_FIELDS = (
    "title",
    "question",
    "yes_button",
    "no_button",
    "yes_response",
    "no_action_prompt",
    "yes_admin",
    "no_admin",
)

FIELD_MAX_LEN: dict[str, int] = {
    "title": TITLE_MAX_LEN,
    "question": QUESTION_MAX_LEN,
    "yes_button": BUTTON_MAX_LEN,
    "no_button": BUTTON_MAX_LEN,
    "yes_response": RESPONSE_MAX_LEN,
    "no_action_prompt": RESPONSE_MAX_LEN,
    "yes_admin": RESPONSE_MAX_LEN,
    "no_admin": RESPONSE_MAX_LEN,
}

FIELD_I18N_KEY: dict[str, str] = {
    "title": "attendance_reminder_title",
    "question": "attendance_prompt",
    "yes_button": "attendance_yes_button",
    "no_button": "attendance_no_button",
    "yes_response": "attendance_confirmed_client",
    "no_action_prompt": "attendance_action_prompt",
    "yes_admin": "attendance_confirmed_admin",
    "no_admin": "attendance_cannot_attend_admin",
}

SETTING_KEY: dict[tuple[str, str], str] = {
    (field, lang): f"confirm_{field}_{lang}"
    for field in CONFIRM_FIELDS
    for lang in ("ru", "en")
}


@dataclass(frozen=True)
class ConfirmationTextConfig:
    values: dict[str, str | None]

    def get_custom(self, field: str, lang: str) -> str | None:
        key = SETTING_KEY[(field, lang)]
        raw = self.values.get(key)
        if raw and raw.strip():
            return raw.strip()
        return None


def _location_block(booking: Booking, lang: str) -> str:
    if booking.service_location_title:
        block = t(lang, "attendance_reminder_service_location", title=booking.service_location_title)
        if booking.service_location_address:
            block += t(
                lang,
                "attendance_reminder_service_location_address",
                address=booking.service_location_address,
            )
        return block
    return ""


def _address_block(booking: Booking, lang: str) -> str:
    if booking.location_text:
        return t(lang, "attendance_reminder_client_address", address=booking.location_text)
    return ""


def _response_line(booking: Booking, lang: str) -> str:
    if not has_attendance_response(booking):
        return ""
    if booking.attendance_status == ATTENDANCE_CONFIRMED:
        return t(lang, "attendance_reminder_response_confirmed")
    return t(lang, "attendance_reminder_response_cannot")


def should_send_attendance_buttons(config: ReminderConfig, reminder_type: str) -> bool:
    if not config.attendance_confirmation_enabled:
        return False
    mode = config.attendance_confirmation_reminder
    if mode == "both":
        return True
    return mode == reminder_type


def _clean(value: str | None) -> str | None:
    if value and value.strip():
        return value.strip()
    return None


async def load_confirmation_text_config(session: AsyncSession) -> ConfirmationTextConfig:
    repo = SettingsRepository(session)
    values: dict[str, str | None] = {}
    for (field, lang), key in SETTING_KEY.items():
        _ = field
        values[key] = _clean(await repo.get(key))
    return ConfirmationTextConfig(values=values)


async def save_confirmation_text(
    session: AsyncSession,
    field: str,
    lang: str,
    text: str,
) -> None:
    key = SETTING_KEY[(field, lang)]
    await SettingsRepository(session).set(key, text.strip())


async def reset_confirmation_texts(session: AsyncSession, lang: str) -> None:
    repo = SettingsRepository(session)
    for field in CONFIRM_FIELDS:
        await repo.set(SETTING_KEY[(field, lang)], "")


def validate_confirmation_value(field: str, text: str) -> str | None:
    """Return i18n error key or None if valid."""
    stripped = text.strip()
    if not stripped:
        return "confirm_value_empty"
    max_len = FIELD_MAX_LEN.get(field, RESPONSE_MAX_LEN)
    if len(stripped) > max_len:
        return "confirm_value_too_long"
    return None


def resolve_confirmation_text(
    config: ConfirmationTextConfig,
    lang: str,
    field: str,
    **fmt,
) -> str:
    custom = config.get_custom(field, lang)
    if custom:
        return _apply_placeholders(custom, **fmt)
    i18n_key = FIELD_I18N_KEY[field]
    return t(lang, i18n_key, **fmt)


def _apply_placeholders(text: str, **kwargs) -> str:
    if "{" not in text:
        return text
    try:
        return text.format(**kwargs)
    except (KeyError, ValueError):
        return text


def build_booking_confirmation_message(
    booking: Booking,
    service_name: str,
    date_time: str,
    lang: str,
    config: ConfirmationTextConfig,
    *,
    manual: bool = False,
    include_prompt: bool = True,
) -> str:
    intro_key = "attendance_manual_intro" if manual else "attendance_reminder_intro"
    lines = [
        resolve_confirmation_text(config, lang, "title"),
        t(lang, intro_key),
        t(lang, "attendance_reminder_service", service=service_name),
        t(lang, "attendance_reminder_datetime", date_time=date_time),
    ]
    loc = _location_block(booking, lang)
    if loc:
        lines.append(loc.strip())
    addr = _address_block(booking, lang)
    if addr:
        lines.append(addr.strip())
    response = _response_line(booking, lang)
    if response:
        lines.append(response.strip())
    elif include_prompt:
        lines.append(resolve_confirmation_text(config, lang, "question"))
    return "\n".join(lines)


def build_booking_confirmation_keyboard(
    booking_id: int,
    lang: str,
    config: ConfirmationTextConfig,
) -> InlineKeyboardMarkup:
    yes_label = resolve_confirmation_text(config, lang, "yes_button")
    no_label = resolve_confirmation_text(config, lang, "no_button")
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=yes_label,
                    callback_data=f"att:yes:{booking_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=no_label,
                    callback_data=f"att:no:{booking_id}",
                )
            ],
        ]
    )


def build_confirmation_preview_keyboard(lang: str, config: ConfirmationTextConfig) -> InlineKeyboardMarkup:
    yes_label = resolve_confirmation_text(config, lang, "yes_button")
    no_label = resolve_confirmation_text(config, lang, "no_button")
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=yes_label, callback_data="conf:noop")],
            [InlineKeyboardButton(text=no_label, callback_data="conf:noop")],
        ]
    )


def build_confirmation_preview_message(
    lang: str,
    config: ConfirmationTextConfig,
    *,
    manual: bool = False,
) -> str:
    sample_service = "Пример услуги" if lang == "ru" else "Sample service"
    sample_datetime = "01.01.2026 10:00"
    intro_key = "attendance_manual_intro" if manual else "attendance_reminder_intro"
    lines = [
        resolve_confirmation_text(config, lang, "title"),
        t(lang, intro_key),
        t(lang, "attendance_reminder_service", service=sample_service),
        t(lang, "attendance_reminder_datetime", date_time=sample_datetime),
        resolve_confirmation_text(config, lang, "question"),
    ]
    return "\n".join(lines)


def attendance_reminder_keyboard(
    booking: Booking,
    lang: str,
    config: ConfirmationTextConfig,
    reminder_config: ReminderConfig,
    reminder_type: str,
) -> InlineKeyboardMarkup | None:
    if has_attendance_response(booking):
        return None
    if not should_send_attendance_buttons(reminder_config, reminder_type):
        return None
    return build_booking_confirmation_keyboard(booking.id, lang, config)


def format_admin_confirmation_notification(
    config: ConfirmationTextConfig,
    lang: str,
    field: str,
    *,
    client_name: str,
    phone: str,
    service: str,
    date_time: str,
    reason: str | None = None,
) -> str:
    kwargs = {
        "client_name": client_name,
        "phone": phone,
        "service": service,
        "date_time": date_time,
    }
    if reason is not None:
        kwargs["reason"] = reason
    custom = config.get_custom(field, lang)
    if custom:
        return _apply_placeholders(custom, **kwargs)
    return t(lang, FIELD_I18N_KEY[field], **kwargs)


async def send_confirmation_preview(message: Message, lang: str, config: ConfirmationTextConfig) -> None:
    await message.answer(
        build_confirmation_preview_message(lang, config),
        reply_markup=build_confirmation_preview_keyboard(lang, config),
    )
