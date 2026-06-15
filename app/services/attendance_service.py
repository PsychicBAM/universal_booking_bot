from __future__ import annotations

import logging
from datetime import datetime, timezone

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.i18n import t
from app.config import get_settings
from app.models import Booking, BookingStatus, Client
from app.repositories import ClientRepository
from app.services.confirmation_text_service import (
    ConfirmationTextConfig,
    attendance_reminder_keyboard as _attendance_reminder_keyboard,
    build_booking_confirmation_message,
    format_admin_confirmation_notification,
    should_send_attendance_buttons,
)
from app.services.language_service import get_user_language
from app.services.reminder_settings import ReminderConfig
from app.utils.datetime_utils import to_local_naive

from app.bot.utils.attendance_helpers import (
    ATTENDANCE_CANNOT_ATTEND,
    ATTENDANCE_CONFIRMED,
    ATTENDANCE_REASON_PROVIDED,
    has_attendance_response,
)

logger = logging.getLogger(__name__)


def format_attendance_reminder_text(
    booking: Booking,
    service_name: str,
    date_time: str,
    lang: str,
    config: ConfirmationTextConfig,
    *,
    include_prompt: bool = True,
) -> str:
    return build_booking_confirmation_message(
        booking,
        service_name,
        date_time,
        lang,
        config,
        manual=False,
        include_prompt=include_prompt,
    )


def attendance_reminder_keyboard(
    booking: Booking,
    lang: str,
    config: ConfirmationTextConfig,
    reminder_config: ReminderConfig,
    reminder_type: str,
) -> InlineKeyboardMarkup | None:
    return _attendance_reminder_keyboard(booking, lang, config, reminder_config, reminder_type)


def format_attendance_client_line(booking: Booking, lang: str) -> str | None:
    if not has_attendance_response(booking):
        return None
    if booking.attendance_status == ATTENDANCE_CONFIRMED:
        return t(lang, "attendance_client_response_confirmed")
    line = t(lang, "attendance_client_response_cannot")
    if booking.attendance_reason:
        line += "\n" + t(lang, "attendance_status_reason", reason=booking.attendance_reason)
    return line


def format_attendance_detail_line(booking: Booking, lang: str) -> str | None:
    if not has_attendance_response(booking):
        return None
    if booking.attendance_status == ATTENDANCE_CONFIRMED:
        return t(lang, "attendance_status_confirmed")
    line = t(lang, "attendance_status_cannot_attend")
    if booking.attendance_reason:
        line += "\n" + t(lang, "attendance_status_reason", reason=booking.attendance_reason)
    return line


def format_attendance_admin_line(booking: Booking, lang: str) -> str | None:
    return format_attendance_detail_line(booking, lang)


def is_booking_attendance_eligible(booking: Booking | None) -> bool:
    return bool(
        booking and booking.status in (BookingStatus.PENDING, BookingStatus.CONFIRMED)
    )


async def notify_admins_attendance(
    bot: Bot,
    booking: Booking,
    service_name: str,
    admin_field: str,
    config: ConfirmationTextConfig,
    *,
    reason: str | None = None,
) -> None:
    settings = get_settings()
    date_time = to_local_naive(booking.start_at).strftime("%d.%m.%Y %H:%M")
    phone = booking.client_phone or t(settings.default_language, "phone_not_provided")
    for admin_id in settings.admin_ids:
        admin_lang = await get_user_language(admin_id)
        if reason is not None:
            text = t(
                admin_lang,
                "attendance_reason_admin",
                client_name=booking.client_name,
                phone=phone,
                service=service_name,
                date_time=date_time,
                reason=reason,
            )
        else:
            text = format_admin_confirmation_notification(
                config,
                admin_lang,
                admin_field,
                client_name=booking.client_name,
                phone=phone,
                service=service_name,
                date_time=date_time,
            )
        try:
            await bot.send_message(admin_id, text)
        except Exception:
            logger.exception("Failed to notify admin %s about attendance", admin_id)


async def get_client_booking(
    session: AsyncSession,
    booking_id: int,
    telegram_id: int,
) -> tuple[Booking, Client] | None:
    from app.repositories import BookingRepository

    row = await BookingRepository(session).get_by_id(booking_id)
    client = await ClientRepository(session).get_by_telegram_id(telegram_id)
    if not row or not client or row.client_id != client.id:
        return None
    if not is_booking_attendance_eligible(row):
        return None
    return row, client


def mark_attendance_response(
    booking: Booking,
    status: str,
    *,
    reminder_type: str | None = None,
    reason: str | None = None,
) -> None:
    booking.attendance_status = status
    booking.attendance_responded_at = datetime.now(timezone.utc)
    if reminder_type:
        booking.attendance_reminder_type = reminder_type
    if reason is not None:
        booking.attendance_reason = reason
