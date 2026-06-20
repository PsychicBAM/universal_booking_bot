from sqlalchemy.ext.asyncio import AsyncSession

from app.services.service_modes_service import ServiceModes, load_service_modes


async def menu_mode_kwargs(session: AsyncSession) -> dict[str, bool]:
    modes = await load_service_modes(session)
    return {
        "booking_enabled": modes.booking_enabled,
        "order_enabled": modes.order_enabled,
    }


async def load_modes(session: AsyncSession) -> ServiceModes:
    return await load_service_modes(session)
