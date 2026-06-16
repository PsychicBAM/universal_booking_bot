from __future__ import annotations

from datetime import timedelta

from app.bot.i18n import t
from app.bot.utils.attendance_helpers import (
    ATTENDANCE_CANNOT_ATTEND,
    ATTENDANCE_CONFIRMED,
    ATTENDANCE_REASON_PROVIDED,
)
from app.models import Booking, BookingStatus, Client, Service
from app.utils.datetime_utils import now_local, to_local_naive

ADMIN_NAME_MAX_LEN = 28
CLIENT_SERVICE_NAME_MAX_LEN = 24

_EN_MONTH_ABBR = (
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)


def truncate_display_name(name: str, max_len: int = ADMIN_NAME_MAX_LEN) -> str:
    name = (name or "").strip()
    if len(name) <= max_len:
        return name
    if max_len < 2:
        return name[:max_len]
    return name[: max_len - 1].rstrip() + "…"


def resolve_booking_display_name(booking: Booking, client: Client | None = None) -> str:
    if booking.client_name and booking.client_name.strip():
        return booking.client_name.strip()
    if client is not None:
        if client.full_name and client.full_name.strip():
            return client.full_name.strip()
        if client.name and client.name.strip():
            return client.name.strip()
        if client.username and client.username.strip():
            return f"@{client.username.strip()}"
        return str(client.telegram_id)
    return str(booking.client_id)


def format_admin_booking_datetime_label(start_at, lang: str) -> str:
    start = to_local_naive(start_at)
    today = now_local().date()
    booking_date = start.date()
    time_part = start.strftime("%H:%M")
    if booking_date == today:
        return f"{t(lang, 'date_today')} {time_part}"
    if booking_date == today + timedelta(days=1):
        return f"{t(lang, 'date_tomorrow')} {time_part}"
    if lang == "en":
        date_part = f"{booking_date.day} {_EN_MONTH_ABBR[booking_date.month - 1]}"
    else:
        date_part = start.strftime("%d.%m")
    return f"{date_part} {time_part}"


def admin_booking_list_icon(booking: Booking, *, section: str | None = None) -> str:
    if section == "cancelled" or booking.status == BookingStatus.CANCELLED:
        return "❌"
    if section == "pending_admin" or (
        section is None and booking.status == BookingStatus.PENDING
    ):
        return "🕓"
    if section == "confirmed_bookings":
        return "✅"
    if section == "waiting_client_response":
        return "❔"
    if section == "needs_change":
        return "⚠️"
    if section in ("history", "past"):
        if booking.attendance_status in (ATTENDANCE_CANNOT_ATTEND, ATTENDANCE_REASON_PROVIDED):
            return "⚠️"
        if booking.attendance_status == ATTENDANCE_CONFIRMED:
            return "✅"
        return "📜"
    if booking.status == BookingStatus.CONFIRMED:
        if booking.attendance_status in (ATTENDANCE_CANNOT_ATTEND, ATTENDANCE_REASON_PROVIDED):
            return "⚠️"
        if booking.attendance_status == ATTENDANCE_CONFIRMED:
            return "✅"
        return "❔"
    if booking.status == BookingStatus.PENDING:
        return "🕓"
    return "❔"


def format_admin_booking_button(
    booking: Booking,
    lang: str,
    *,
    section: str | None = None,
    client: Client | None = None,
) -> str:
    icon = admin_booking_list_icon(booking, section=section)
    dt_label = format_admin_booking_datetime_label(booking.start_at, lang)
    name = truncate_display_name(resolve_booking_display_name(booking, client))
    return f"{icon} {dt_label} · {name}"


def resolve_client_service_name(
    service: Service | None,
    lang: str,
    *,
    service_name: str | None = None,
) -> str:
    raw = service_name
    if raw is None and service is not None and service.name and service.name.strip():
        raw = service.name.strip()
    if not raw:
        return t(lang, "client_booking_service_fallback")
    return truncate_display_name(raw, CLIENT_SERVICE_NAME_MAX_LEN)


def format_client_booking_button(
    booking: Booking,
    lang: str,
    *,
    service: Service | None = None,
    service_name: str | None = None,
) -> str:
    name = resolve_client_service_name(service, lang, service_name=service_name)
    dt_label = format_admin_booking_datetime_label(booking.start_at, lang)
    return f"📅 {dt_label} · {name}"
