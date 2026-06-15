from app.models import Service


def is_service_bookable(service: Service | None) -> bool:
    return bool(service and service.is_active and service.archived_at is None)


def service_detail_source(service: Service) -> str:
    if service.archived_at is not None:
        return "archived"
    return "disabled" if not service.is_active else "active"


def client_service_unavailable_key(service: Service | None) -> str:
    if service and service.archived_at is None and not service.is_active:
        return "service_unavailable_booking"
    return "not_found"
