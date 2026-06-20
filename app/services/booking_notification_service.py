from __future__ import annotations

import inspect
import logging
from collections.abc import Awaitable, Callable

from aiogram import Bot

from app.config import get_settings
from app.models import Booking, Service, ServiceOrder
from app.services.language_service import get_user_language
from app.utils.formatting import (
    format_booking_cancelled_by_admin_client_notification,
    format_booking_rescheduled_by_client_admin_notification,
    format_client_cancelled_admin_notification,
    format_order_cancelled_by_admin_client_notification,
    format_order_cancelled_by_client_admin_notification,
)

logger = logging.getLogger(__name__)

TextBuilder = Callable[[str], str | Awaitable[str]]


async def _load_client_username(client_id: int) -> str | None:
    from app.database.session import async_session_factory
    from app.models import Client

    async with async_session_factory() as session:
        client = await session.get(Client, client_id)
        return client.username if client else None


async def _resolve_text_builder(build_text: TextBuilder, lang: str) -> str:
    result = build_text(lang)
    if inspect.isawaitable(result):
        result = await result
    if not isinstance(result, str):
        raise TypeError(f"Notification builder must return str, got {type(result)!r}")
    return result


async def _notify_admins(bot: Bot, build_text: TextBuilder) -> None:
    settings = get_settings()
    if not settings.admin_ids:
        return
    for admin_id in settings.admin_ids:
        admin_lang = await get_user_language(admin_id)
        try:
            text = await _resolve_text_builder(build_text, admin_lang)
        except TypeError:
            logger.error(
                "Invalid admin notification text for admin_id=%s",
                admin_id,
                exc_info=True,
            )
            continue
        except Exception:
            logger.warning(
                "Failed to build admin notification for admin_id=%s",
                admin_id,
                exc_info=True,
            )
            continue
        try:
            await bot.send_message(admin_id, text)
        except Exception:
            logger.warning(
                "Failed to notify admin %s",
                admin_id,
                exc_info=True,
            )


async def notify_admins_client_cancelled(
    bot: Bot,
    booking: Booking,
    service: Service | None,
    *,
    lang: str = "ru",
) -> None:
    username = await _load_client_username(booking.client_id)

    def build_text(admin_lang: str) -> str:
        return format_client_cancelled_admin_notification(
            booking,
            service,
            admin_lang,
            client_username=username,
        )

    await _notify_admins(bot, build_text)


async def notify_admins_booking_rescheduled(
    bot: Bot,
    booking: Booking,
    service: Service | None,
    *,
    old_datetime: str,
    new_datetime: str,
) -> None:
    username = await _load_client_username(booking.client_id)

    def build_text(admin_lang: str) -> str:
        return format_booking_rescheduled_by_client_admin_notification(
            booking,
            service,
            admin_lang,
            old_datetime=old_datetime,
            new_datetime=new_datetime,
            client_username=username,
        )

    await _notify_admins(bot, build_text)


async def notify_client_booking_cancelled_by_admin(
    bot: Bot,
    booking: Booking,
    service: Service | None,
) -> None:
    from app.database.session import async_session_factory
    from app.models import Client

    async with async_session_factory() as session:
        client = await session.get(Client, booking.client_id)
    if not client:
        return
    client_lang = client.language or get_settings().default_language
    text = format_booking_cancelled_by_admin_client_notification(booking, service, client_lang)
    try:
        await bot.send_message(client.telegram_id, text)
    except Exception:
        logger.warning(
            "Failed to notify client about admin cancellation booking_id=%s",
            booking.id,
            exc_info=True,
        )


async def notify_admins_order_cancelled_by_client(
    bot: Bot,
    order: ServiceOrder,
    service: Service | None,
) -> None:
    def build_text(admin_lang: str) -> str:
        return format_order_cancelled_by_client_admin_notification(order, service, admin_lang)

    await _notify_admins(bot, build_text)


async def notify_client_order_cancelled_by_admin(
    bot: Bot,
    order: ServiceOrder,
    service: Service | None,
) -> None:
    from app.database.session import async_session_factory
    from app.models import Client

    async with async_session_factory() as session:
        client = await session.get(Client, order.client_id)
    if not client:
        return
    client_lang = client.language or get_settings().default_language
    text = format_order_cancelled_by_admin_client_notification(order, service, client_lang)
    try:
        await bot.send_message(client.telegram_id, text)
    except Exception:
        logger.warning(
            "Failed to notify client about admin order cancellation order_id=%s",
            order.id,
            exc_info=True,
        )
