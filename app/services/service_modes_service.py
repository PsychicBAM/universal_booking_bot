from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import SettingsRepository


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class ServiceModes:
    booking_enabled: bool
    order_enabled: bool


async def load_service_modes(session: AsyncSession) -> ServiceModes:
    repo = SettingsRepository(session)
    booking = _parse_bool(await repo.get("booking_mode_enabled"), True)
    order = _parse_bool(await repo.get("order_mode_enabled"), False)
    return ServiceModes(booking_enabled=booking, order_enabled=order)


async def save_booking_mode(session: AsyncSession, enabled: bool) -> str | None:
    modes = await load_service_modes(session)
    if not enabled and not modes.order_enabled:
        return "cannot_disable_all"
    await SettingsRepository(session).set("booking_mode_enabled", "true" if enabled else "false")
    return None


async def save_order_mode(session: AsyncSession, enabled: bool) -> str | None:
    modes = await load_service_modes(session)
    if not enabled and not modes.booking_enabled:
        return "cannot_disable_all"
    await SettingsRepository(session).set("order_mode_enabled", "true" if enabled else "false")
    return None


def default_service_type_for_modes(modes: ServiceModes) -> str:
    from app.models import SERVICE_TYPE_BOOKING, SERVICE_TYPE_ORDER

    if modes.booking_enabled and not modes.order_enabled:
        return SERVICE_TYPE_BOOKING
    if modes.order_enabled and not modes.booking_enabled:
        return SERVICE_TYPE_ORDER
    return SERVICE_TYPE_BOOKING
