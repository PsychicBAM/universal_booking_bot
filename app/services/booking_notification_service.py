from __future__ import annotations

import logging

from aiogram import Bot

from app.config import get_settings
from app.models import Booking, Service
from app.services.language_service import get_user_language
from app.utils.formatting import format_client_cancelled_admin_notification

logger = logging.getLogger(__name__)


async def notify_admins_client_cancelled(
    bot: Bot,
    booking: Booking,
    service: Service | None,
    *,
    lang: str = "ru",
) -> None:
    settings = get_settings()
    if not settings.admin_ids:
        return

    from app.database.session import async_session_factory
    from app.models import Client

    async with async_session_factory() as session:
        client = await session.get(Client, booking.client_id)
        username = client.username if client else None

    for admin_id in settings.admin_ids:
        admin_lang = await get_user_language(admin_id)
        text = format_client_cancelled_admin_notification(
            booking,
            service,
            admin_lang,
            client_username=username,
        )
        try:
            await bot.send_message(admin_id, text)
        except Exception:
            logger.warning(
                "Failed to notify admin %s about client cancellation booking_id=%s",
                admin_id,
                booking.id,
                exc_info=True,
            )
