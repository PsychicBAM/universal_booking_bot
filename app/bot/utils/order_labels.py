from app.bot.i18n import t
from app.models import ServiceOrder, ServiceOrderStatus
from app.utils.datetime_utils import to_local_naive


def _status_emoji(status: str) -> str:
    return {
        ServiceOrderStatus.NEW.value: "🆕",
        ServiceOrderStatus.IN_PROGRESS.value: "🔄",
        ServiceOrderStatus.COMPLETED.value: "✅",
        ServiceOrderStatus.CANCELLED.value: "❌",
    }.get(status, "📝")


def format_client_order_button(order: ServiceOrder, lang: str, *, service_name: str | None = None) -> str:
    dt = to_local_naive(order.created_at)
    date_s = dt.strftime("%d.%m")
    name = service_name or t(lang, "order_service_fallback")
    return f"{_status_emoji(order.status)} {date_s} · {name}"


def format_admin_order_button(order: ServiceOrder, lang: str, *, service_name: str | None = None) -> str:
    return format_client_order_button(order, lang, service_name=service_name)
