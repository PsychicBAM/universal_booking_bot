from app.models import Service


def is_service_bookable(service: Service | None) -> bool:
    return bool(service and service.is_active and service.archived_at is None)
