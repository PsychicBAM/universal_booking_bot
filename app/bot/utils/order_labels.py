from app.bot.i18n import t
from app.models import ServiceOrder, ServiceOrderStatus
from app.utils.datetime_utils import to_local_naive

CLIENT_SERVICE_NAME_MAX_LEN = 22
CLIENT_DETAILS_PREVIEW_MAX_LEN = 20


def _status_emoji(status: str) -> str:
    return {
        ServiceOrderStatus.NEW.value: "🆕",
        ServiceOrderStatus.ACCEPTED.value: "✅",
        ServiceOrderStatus.IN_PROGRESS.value: "🔄",
        ServiceOrderStatus.COMPLETED.value: "✅",
        ServiceOrderStatus.CANCELLED.value: "❌",
        ServiceOrderStatus.DECLINED.value: "🚫",
    }.get(status, "📝")


def _truncate(text: str, max_len: int) -> str:
    text = (text or "").strip()
    if len(text) <= max_len:
        return text
    if max_len < 2:
        return text[:max_len]
    return text[: max_len - 1].rstrip() + "…"


def format_client_order_button(
    order: ServiceOrder,
    lang: str,
    *,
    service_name: str | None = None,
) -> str:
    dt = to_local_naive(order.created_at)
    date_s = dt.strftime("%d.%m")
    name = _truncate(service_name or t(lang, "order_service_fallback"), CLIENT_SERVICE_NAME_MAX_LEN)
    parts = [f"{_status_emoji(order.status)} {date_s}", name]
    if order.details and order.details.strip():
        preview = _truncate(order.details.strip(), CLIENT_DETAILS_PREVIEW_MAX_LEN)
        if preview:
            parts.append(preview)
    return " · ".join(parts)


def format_admin_order_button(order: ServiceOrder, lang: str, *, service_name: str | None = None) -> str:
    return format_client_order_button(order, lang, service_name=service_name)
