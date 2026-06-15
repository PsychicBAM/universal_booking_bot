"""Internal support messages between clients and admins."""

from __future__ import annotations

import logging

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.i18n import t
from app.bot.keyboards.support_kb import support_admin_kb
from app.config import get_settings
from app.models import Booking, SupportMessage, SupportMessageStatus
from app.repositories import BookingRepository, SettingsRepository, SupportMessageRepository
from app.utils.formatting import format_datetime

logger = logging.getLogger(__name__)

MAX_SUPPORT_MESSAGE_LEN = 3000

SUPPORT_TOPICS = ("booking", "reschedule", "cancel", "payment", "other")
BOOKING_PICK_TOPICS = frozenset({"reschedule", "cancel"})


def validate_support_text(text: str) -> str | None:
    """Return i18n error key or None if valid."""
    if not text or not text.strip():
        return "support_empty_error"
    if len(text) > MAX_SUPPORT_MESSAGE_LEN:
        return "support_too_long"
    return None


def topic_label(lang: str, topic: str | None) -> str:
    if not topic or topic not in SUPPORT_TOPICS:
        return t(lang, "support_topic_other")
    return t(lang, f"support_topic_{topic}")


def status_label(lang: str, status: SupportMessageStatus) -> str:
    if status == SupportMessageStatus.OPEN:
        return t(lang, "support_status_open")
    if status == SupportMessageStatus.REPLIED:
        return t(lang, "support_status_replied")
    return t(lang, "support_status_closed")


def format_request_list_label(request: SupportMessage, lang: str) -> str:
    return f"#{request.id} [{status_label(lang, request.status)}] {topic_label(lang, request.topic)}"


async def resolve_contact_username(session: AsyncSession) -> str | None:
    settings = get_settings()
    if settings.contact_admin_username:
        return settings.contact_admin_username.lstrip("@")
    stored = await SettingsRepository(session).get("contact_admin_username")
    if stored and stored.strip():
        return stored.strip().lstrip("@")
    return None


async def get_user_language(session: AsyncSession, telegram_id: int) -> str:
    from app.services.language_service import get_user_language as lookup_user_language

    return await lookup_user_language(telegram_id)


def format_username_display(lang: str, username: str | None) -> str:
    if username:
        return f"@{username.lstrip('@')}"
    return t(lang, "support_username_not_provided")


def format_booking_line(lang: str, booking: Booking | None) -> str:
    if not booking:
        return ""
    return t(
        lang,
        "support_booking_line",
        booking_id=str(booking.id),
        date_time=format_datetime(booking.start_at),
    )


def format_admin_notification(
    support_msg: SupportMessage, lang: str, booking: Booking | None = None
) -> str:
    booking_line = format_booking_line(lang, booking)
    parts = [
        t(
            lang,
            "support_admin_new_request",
            topic=topic_label(lang, support_msg.topic),
            client_name=support_msg.client_name,
            telegram_id=str(support_msg.client_telegram_id),
            username=format_username_display(lang, support_msg.client_username),
            text=support_msg.message_text,
        )
    ]
    if booking_line:
        parts.append(booking_line)
    return "\n".join(parts)


def format_request_detail(support_msg: SupportMessage, lang: str, booking: Booking | None = None) -> str:
    lines = [
        t(lang, "support_request_detail", request_id=str(support_msg.id)),
        f"{t(lang, 'support_detail_topic')}: {topic_label(lang, support_msg.topic)}",
        f"{t(lang, 'support_detail_status')}: {status_label(lang, support_msg.status)}",
        "",
        f"{t(lang, 'support_detail_message')}:",
        support_msg.message_text,
    ]
    if booking:
        lines.extend(["", format_booking_line(lang, booking)])
    if support_msg.admin_reply_text:
        lines.extend(
            [
                "",
                f"{t(lang, 'support_detail_admin_reply')}:",
                support_msg.admin_reply_text,
            ]
        )
    return "\n".join(lines)


def format_message_prompt(lang: str, topic: str) -> str:
    return f"{topic_label(lang, topic)}\n\n{t(lang, 'support_message_prompt')}"


async def notify_admins_new_support(
    bot: Bot, session: AsyncSession, support_msg: SupportMessage
) -> bool:
    admin_ids = get_settings().admin_ids
    if not admin_ids:
        return False

    booking = None
    if support_msg.booking_id:
        booking = await BookingRepository(session).get_by_id(support_msg.booking_id)

    sent_any = False
    for admin_id in admin_ids:
        admin_lang = await get_user_language(session, admin_id)
        text = format_admin_notification(support_msg, admin_lang, booking)
        kb = support_admin_kb(support_msg.id, support_msg.client_username, admin_lang)
        try:
            await bot.send_message(admin_id, text, reply_markup=kb)
            sent_any = True
        except Exception:
            logger.exception(
                "Failed to notify admin_id=%s about support_message_id=%s",
                admin_id,
                support_msg.id,
            )
    return sent_any


async def create_support_message(
    session: AsyncSession,
    *,
    client_telegram_id: int,
    client_name: str,
    client_username: str | None,
    message_text: str,
    topic: str | None = None,
    booking_id: int | None = None,
) -> SupportMessage:
    repo = SupportMessageRepository(session)
    return await repo.create(
        client_telegram_id=client_telegram_id,
        client_name=client_name,
        client_username=client_username,
        message_text=message_text.strip(),
        topic=topic,
        booking_id=booking_id,
    )
