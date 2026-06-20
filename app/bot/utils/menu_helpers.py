from __future__ import annotations

from aiogram.types import Message, ReplyKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.i18n import t
from app.bot.keyboards import admin_menu
from app.database.session import async_session_factory
from app.services.service_modes_service import ServiceModes, load_service_modes


async def menu_mode_kwargs(session: AsyncSession) -> dict[str, bool]:
    modes = await load_service_modes(session)
    return {
        "booking_enabled": modes.booking_enabled,
        "order_enabled": modes.order_enabled,
    }


async def load_modes(session: AsyncSession) -> ServiceModes:
    return await load_service_modes(session)


async def mode_aware_admin_menu(
    lang: str,
    session: AsyncSession | None = None,
) -> ReplyKeyboardMarkup:
    if session is None:
        async with async_session_factory() as session:
            kwargs = await menu_mode_kwargs(session)
    else:
        kwargs = await menu_mode_kwargs(session)
    return admin_menu(lang, **kwargs)


async def show_admin_panel(
    message: Message,
    lang: str,
    *,
    session: AsyncSession | None = None,
) -> None:
    if session is None:
        async with async_session_factory() as session:
            keyboard = await mode_aware_admin_menu(lang, session)
    else:
        keyboard = await mode_aware_admin_menu(lang, session)
    await message.answer(t(lang, "admin_panel"), reply_markup=keyboard)
