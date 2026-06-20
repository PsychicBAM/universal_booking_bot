import logging

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import ServiceOrder, ServiceOrderStatus
from app.repositories import ClientRepository, ServiceOrderRepository, ServiceRepository
from app.services.language_service import get_user_language
from app.utils.formatting import format_datetime, format_order_admin, format_order_client

logger = logging.getLogger(__name__)


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
    return await ServiceOrderRepository(session).count_by_status()


async def update_order_status(session: AsyncSession, order_id: int, status: str) -> ServiceOrder | None:
    return await ServiceOrderRepository(session).update_status(order_id, status)


async def add_admin_note(session: AsyncSession, order_id: int, note: str | None) -> ServiceOrder | None:
    return await ServiceOrderRepository(session).set_admin_note(order_id, note)


async def cancel_order(session: AsyncSession, order_id: int) -> ServiceOrder | None:
    return await ServiceOrderRepository(session).update_status(
        order_id, ServiceOrderStatus.CANCELLED.value
    )


async def notify_admins_new_order(bot: Bot, order: ServiceOrder) -> None:
    settings = get_settings()
    from app.database.session import async_session_factory

    async with async_session_factory() as session:
        service = await ServiceRepository(session).get_by_id(order.service_id)

    for admin_id in settings.admin_ids:
        admin_lang = await get_user_language(admin_id)
        text = format_order_admin(order, service, admin_lang, title_key="order_new_admin_title")
        from app.bot.keyboards.orders_kb import admin_new_order_kb

        try:
            await bot.send_message(
                admin_id,
                text,
                reply_markup=admin_new_order_kb(order.id, admin_lang),
            )
        except Exception:
            logger.exception("Failed to notify admin %s about order %s", admin_id, order.id)


async def notify_client_order_status(bot: Bot, order: ServiceOrder, *, lang: str | None = None) -> None:
    from app.database.session import async_session_factory

    async with async_session_factory() as session:
        from sqlalchemy import select
        from app.models import Client

        client = await session.get(Client, order.client_id)
        service = await ServiceRepository(session).get_by_id(order.service_id)
    if not client:
        return
    client_lang = lang or client.language or get_settings().default_language
    from app.bot.i18n import t

    text = (
        f"{t(client_lang, 'order_detail_title')}\n\n"
        f"{format_order_client(order, service, client_lang)}"
    )
    try:
        await bot.send_message(client.telegram_id, text)
    except Exception:
        logger.exception("Failed to notify client about order %s status", order.id)
