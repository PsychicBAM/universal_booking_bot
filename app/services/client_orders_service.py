from __future__ import annotations

from dataclasses import dataclass

from app.models import ServiceOrder, ServiceOrderStatus

CLIENT_ACTIVE_STATUSES = frozenset(
    {
        ServiceOrderStatus.NEW.value,
        ServiceOrderStatus.ACCEPTED.value,
        ServiceOrderStatus.IN_PROGRESS.value,
    }
)
CLIENT_HISTORY_STATUSES = frozenset(
    {
        ServiceOrderStatus.COMPLETED.value,
        ServiceOrderStatus.CANCELLED.value,
        ServiceOrderStatus.DECLINED.value,
    }
)
_ACTIVE_STATUS_ORDER = {
    ServiceOrderStatus.NEW.value: 0,
    ServiceOrderStatus.ACCEPTED.value: 1,
    ServiceOrderStatus.IN_PROGRESS.value: 2,
}


@dataclass
class ClientOrdersHubCounts:
    active_count: int
    history_count: int
    new_count: int
    accepted_count: int
    in_progress_count: int
    completed_count: int
    cancelled_count: int
    declined_count: int


def split_client_orders(orders: list[ServiceOrder]) -> tuple[list[ServiceOrder], list[ServiceOrder]]:
    active = [order for order in orders if order.status in CLIENT_ACTIVE_STATUSES]
    history = [order for order in orders if order.status in CLIENT_HISTORY_STATUSES]
    return active, history


def sort_active_client_orders(orders: list[ServiceOrder]) -> list[ServiceOrder]:
    return sorted(
        orders,
        key=lambda order: (
            _ACTIVE_STATUS_ORDER.get(order.status, 99),
            -order.created_at.timestamp() if order.created_at else 0,
        ),
    )


def sort_history_client_orders(orders: list[ServiceOrder]) -> list[ServiceOrder]:
    return sorted(
        orders,
        key=lambda order: -(order.created_at.timestamp() if order.created_at else 0),
    )


def compute_client_orders_hub_counts(orders: list[ServiceOrder]) -> ClientOrdersHubCounts:
    active, history = split_client_orders(orders)
    return ClientOrdersHubCounts(
        active_count=len(active),
        history_count=len(history),
        new_count=sum(1 for order in active if order.status == ServiceOrderStatus.NEW.value),
        accepted_count=sum(1 for order in active if order.status == ServiceOrderStatus.ACCEPTED.value),
        in_progress_count=sum(1 for order in active if order.status == ServiceOrderStatus.IN_PROGRESS.value),
        completed_count=sum(1 for order in history if order.status == ServiceOrderStatus.COMPLETED.value),
        cancelled_count=sum(1 for order in history if order.status == ServiceOrderStatus.CANCELLED.value),
        declined_count=sum(1 for order in history if order.status == ServiceOrderStatus.DECLINED.value),
    )


def resolve_client_order_section(section: str | None, order: ServiceOrder) -> str:
    if section in ("active", "history"):
        return section
    if order.status in CLIENT_ACTIVE_STATUSES:
        return "active"
    if order.status in CLIENT_HISTORY_STATUSES:
        return "history"
    return "hub"
