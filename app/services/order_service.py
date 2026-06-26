import logging

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import OrderMessage, ServiceOrder, ServiceOrderStatus
from app.repositories import ClientRepository, OrderMessageRepository, ServiceOrderRepository, ServiceRepository
from app.services.language_service import get_user_language, resolve_client_lang_for_client
from app.utils.formatting import (
    format_order_accepted_client_notification,
    format_order_admin,
    format_order_client,
    format_order_declined_client_notification,
    format_order_message_history,
    format_order_new_message_admin_notification,
    format_order_new_message_client_notification,
)

logger = logging.getLogger(__name__)

ORDER_MESSAGE_SENDER_CLIENT = "client"
ORDER_MESSAGE_SENDER_ADMIN = "admin"
ORDER_MESSAGE_SENDER_SYSTEM = "system"

ORDER_HISTORY_LIMIT = 20


async def create_order(
    session: AsyncSession,
    *,
    service_id: int,
    telegram_id: int,
    client_name: str | None,
    client_phone: str | None,
    client_username: str | None,
    details: str | None,
) -> ServiceOrder:
    client_repo = ClientRepository(session)
    client = await client_repo.get_by_telegram_id(telegram_id)
    if not client:
        client = await client_repo.get_or_create(telegram_id)
    order = await ServiceOrderRepository(session).create(
        service_id=service_id,
        client_id=client.id,
        client_name=client_name,
        client_phone=client_phone,
        client_username=client_username,
        details=details,
    )
    if details and details.strip():
        await OrderMessageRepository(session).create(
            order_id=order.id,
            sender_type=ORDER_MESSAGE_SENDER_CLIENT,
            message_text=details.strip(),
            sender_telegram_id=telegram_id,
        )
    await session.flush()
    return order


async def get_order(session: AsyncSession, order_id: int) -> ServiceOrder | None:
    return await ServiceOrderRepository(session).get_by_id(order_id)


async def list_orders(
    session: AsyncSession,
    *,
    status: str | None = None,
    page: int = 0,
    limit: int = 10,
) -> tuple[list[ServiceOrder], int]:
    return await ServiceOrderRepository(session).list_by_status(status, page=page, limit=limit)


async def order_status_counts(session: AsyncSession) -> dict[str, int]:
    counts = await ServiceOrderRepository(session).count_by_status()
    in_progress_total = counts.get(ServiceOrderStatus.ACCEPTED.value, 0) + counts.get(
        ServiceOrderStatus.IN_PROGRESS.value, 0
    )
    counts["in_progress"] = in_progress_total
    return counts


async def update_order_status(session: AsyncSession, order_id: int, status: str) -> ServiceOrder | None:
    order = await ServiceOrderRepository(session).update_status(order_id, status)
    if order:
        await _maybe_add_status_system_message(session, order, status)
    return order


async def accept_order(
    session: AsyncSession,
    order_id: int,
    *,
    admin_telegram_id: int | None = None,
) -> ServiceOrder | None:
    order = await ServiceOrderRepository(session).accept_order(
        order_id,
        admin_telegram_id=admin_telegram_id,
    )
    if order:
        await _maybe_add_status_system_message(session, order, ServiceOrderStatus.ACCEPTED.value)
    return order


async def decline_order(
    session: AsyncSession,
    order_id: int,
    reason: str,
    *,
    admin_telegram_id: int | None = None,
) -> ServiceOrder | None:
    order = await ServiceOrderRepository(session).decline_order(
        order_id,
        reason,
        admin_telegram_id=admin_telegram_id,
    )
    if order:
        await add_order_message(
            session,
            order_id=order.id,
            sender_type=ORDER_MESSAGE_SENDER_ADMIN,
            message_text=reason,
            sender_telegram_id=admin_telegram_id,
        )
        await _maybe_add_status_system_message(session, order, ServiceOrderStatus.DECLINED.value)
    return order


async def add_admin_note(session: AsyncSession, order_id: int, note: str | None) -> ServiceOrder | None:
    return await ServiceOrderRepository(session).set_admin_note(order_id, note)


async def cancel_order(session: AsyncSession, order_id: int) -> ServiceOrder | None:
    order = await ServiceOrderRepository(session).update_status(
        order_id, ServiceOrderStatus.CANCELLED.value
    )
    if order:
        await _maybe_add_status_system_message(session, order, ServiceOrderStatus.CANCELLED.value)
    return order


async def add_order_message(
    session: AsyncSession,
    *,
    order_id: int,
    sender_type: str,
    message_text: str,
    sender_telegram_id: int | None = None,
) -> OrderMessage:
    return await OrderMessageRepository(session).create(
        order_id=order_id,
        sender_type=sender_type,
        message_text=message_text,
        sender_telegram_id=sender_telegram_id,
    )


async def list_order_messages(
    session: AsyncSession,
    order_id: int,
    *,
    limit: int = ORDER_HISTORY_LIMIT,
) -> list[OrderMessage]:
    return await OrderMessageRepository(session).list_for_order(order_id, limit=limit)


async def _maybe_add_status_system_message(
    session: AsyncSession,
    order: ServiceOrder,
    status: str,
) -> None:
    from app.bot.i18n import t

    key = f"order_system_status_{status}"
    text = t("ru", key)
    if text == key:
        return
    await add_order_message(
        session,
        order_id=order.id,
        sender_type=ORDER_MESSAGE_SENDER_SYSTEM,
        message_text=text,
    )


async def notify_admins_new_order(bot: Bot, order: ServiceOrder) -> None:
    settings = get_settings()
    from app.database.session import async_session_factory
    from app.bot.keyboards.orders_kb import admin_new_order_kb

    async with async_session_factory() as session:
        service = await ServiceRepository(session).get_by_id(order.service_id)

    for admin_id in settings.admin_ids:
        admin_lang = await get_user_language(admin_id)
        text = format_order_admin(order, service, admin_lang, title_key="order_new_admin_title")
        try:
            await bot.send_message(
                admin_id,
                text,
                reply_markup=admin_new_order_kb(order.id, admin_lang),
            )
        except Exception:
            logger.warning("Failed to notify admin %s about order %s", admin_id, order.id, exc_info=True)


async def notify_client_order_accepted(bot: Bot, order: ServiceOrder, service) -> None:
    from app.database.session import async_session_factory
    from app.models import Client

    async with async_session_factory() as session:
        client = await session.get(Client, order.client_id)
    if not client:
        return
    client_lang = await resolve_client_lang_for_client(client)
    text = format_order_accepted_client_notification(order, service, client_lang)
    try:
        await bot.send_message(client.telegram_id, text)
    except Exception:
        logger.warning("Failed to notify client about accepted order %s", order.id, exc_info=True)


async def notify_client_order_declined(bot: Bot, order: ServiceOrder, service) -> None:
    from app.database.session import async_session_factory
    from app.models import Client

    async with async_session_factory() as session:
        client = await session.get(Client, order.client_id)
    if not client:
        return
    client_lang = await resolve_client_lang_for_client(client)
    text = format_order_declined_client_notification(order, service, client_lang)
    try:
        await bot.send_message(client.telegram_id, text)
    except Exception:
        logger.warning("Failed to notify client about declined order %s", order.id, exc_info=True)


async def notify_admins_order_message(
    bot: Bot,
    order: ServiceOrder,
    service,
    message_text: str,
) -> None:
    settings = get_settings()
    from app.bot.keyboards.orders_kb import order_message_notify_admin_kb

    for admin_id in settings.admin_ids:
        admin_lang = await get_user_language(admin_id)
        text = format_order_new_message_admin_notification(order, service, message_text, admin_lang)
        try:
            await bot.send_message(
                admin_id,
                text,
                reply_markup=order_message_notify_admin_kb(order.id, admin_lang),
            )
        except Exception:
            logger.warning(
                "Failed to notify admin %s about order message %s",
                admin_id,
                order.id,
                exc_info=True,
            )


async def notify_client_order_message(
    bot: Bot,
    order: ServiceOrder,
    service,
    message_text: str,
) -> None:
    from app.database.session import async_session_factory
    from app.models import Client
    from app.bot.keyboards.orders_kb import order_message_notify_client_kb

    async with async_session_factory() as session:
        client = await session.get(Client, order.client_id)
    if not client:
        return
    client_lang = await resolve_client_lang_for_client(client)
    text = format_order_new_message_client_notification(order, service, message_text, client_lang)
    try:
        await bot.send_message(
            client.telegram_id,
            text,
            reply_markup=order_message_notify_client_kb(order.id, client_lang),
        )
    except Exception:
        logger.warning("Failed to notify client about order message %s", order.id, exc_info=True)


async def build_order_history_text(session: AsyncSession, order_id: int, lang: str) -> str:
    messages = await list_order_messages(session, order_id)
    return format_order_message_history(messages, lang)
