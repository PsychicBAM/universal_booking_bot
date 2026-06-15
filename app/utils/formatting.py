from datetime import date, datetime, time
from html import escape

from app.bot.i18n import format_buffer, format_duration, status_label, t
from app.models import Booking, Service


def format_date(d: date) -> str:
    return d.strftime("%d.%m.%Y")


def format_time(dt: datetime) -> str:
    return dt.strftime("%H:%M")


def format_datetime(dt: datetime) -> str:
    return dt.strftime("%d.%m.%Y %H:%M")


def _service_location_lines(booking: Booking, lang: str) -> list[str]:
    if not booking.service_location_title:
        return []
    lines = [t(lang, "service_location_label", title=escape(booking.service_location_title))]
    if booking.service_location_address:
        lines.append(t(lang, "address_label", address=escape(booking.service_location_address)))
    return lines


def _location_comment_lines(
    booking: Booking,
    service: Service | None,
    lang: str,
    *,
    admin_view: bool = False,
) -> list[str]:
    lines: list[str] = []
    show_address = bool(booking.location_text) or bool(service and service.requires_location)
    if show_address:
        location = escape(booking.location_text) if booking.location_text else t(lang, "not_provided")
        lines.append(t(lang, "client_address_label", location=location))

    show_comment = bool(booking.client_comment) or bool(service and service.ask_client_comment)
    if show_comment:
        if booking.client_comment:
            comment = escape(booking.client_comment)
        elif service and service.ask_client_comment:
            comment = t(lang, "comment_not_provided")
        else:
            comment = escape(booking.client_comment) if booking.client_comment else t(lang, "not_provided")
        lines.append(t(lang, "service_comment_label", comment=comment))
    return lines


def format_service(service: Service, lang: str = "ru") -> str:
    price = t(lang, "price_label", price=f"{service.price} ₽") if service.price else t(lang, "price_free")
    desc = escape(service.description) if service.description else ""
    lines = [
        f"<b>{escape(service.name)}</b>",
        t(lang, "duration_label", duration=format_duration(lang, service.duration_minutes)),
    ]
    if service.buffer_after_minutes:
        lines.append(t(lang, "buffer_client_note"))
    lines.extend([price, desc])
    return "\n".join(line for line in lines if line).strip()


def format_service_admin(
    service: Service,
    lang: str = "ru",
    *,
    photos_count: int = 0,
    videos_count: int = 0,
    locations_count: int = 0,
) -> str:
    active = t(lang, "yes") if service.is_active else t(lang, "no")
    price = f"{service.price} ₽" if service.price else t(lang, "price_free")
    desc = escape(service.description) if service.description else ""
    location_status = t(lang, "label_enabled") if service.requires_location else t(lang, "label_disabled")
    comment_status = (
        t(lang, "label_enabled") if service.ask_client_comment else t(lang, "label_disabled")
    )
    media_status = t(lang, "media_enabled") if service.show_media_to_clients else t(lang, "media_disabled")
    return (
        f"<b>{escape(service.name)}</b>\n"
        f"{t(lang, 'duration_label', duration=format_duration(lang, service.duration_minutes))}\n"
        f"{t(lang, 'buffer_after_service', buffer=format_buffer(lang, service.buffer_after_minutes))}\n"
        f"{t(lang, 'service_requires_location', status=location_status)}\n"
        f"{t(lang, 'service_comment_setting', status=comment_status)}\n"
        f"{t(lang, 'service_locations_count', count=str(locations_count))}\n"
        f"{t(lang, 'photos_count', count=str(photos_count))}\n"
        f"{t(lang, 'videos_count', count=str(videos_count))}\n"
        f"{t(lang, 'client_media_display', status=media_status)}\n"
        f"{t(lang, 'price_label', price=price)}\n"
        f"{t(lang, 'active_label', value=active)}\n"
        f"{desc}"
    ).strip()


def format_booking(
    booking: Booking,
    service: Service | None = None,
    lang: str = "ru",
    *,
    admin_view: bool = False,
    show_location_comment: bool = False,
    client_username: str | None = None,
) -> str:
    service_name = escape(service.name) if service else f"Service #{booking.service_id}"
    status = status_label(lang, booking.status.value)
    lines = [
        f"📋 {service_name}",
        t(lang, "booking_id_label", id=str(booking.id)),
        f"📅 {format_datetime(booking.start_at)}",
        f"👤 {escape(booking.client_name)}",
        f"📞 {escape(booking.client_phone or t(lang, 'booking_phone_not_provided'))}",
    ]
    if admin_view:
        tg = f"@{client_username}" if client_username else t(lang, "not_provided")
        lines.insert(3, t(lang, "admin_booking_telegram_line", username=tg))
    lines.extend(_service_location_lines(booking, lang))
    if show_location_comment or admin_view:
        lines.extend(_location_comment_lines(booking, service, lang, admin_view=admin_view))
    from app.services.attendance_service import (
        format_attendance_admin_line,
        format_attendance_client_line,
    )

    attendance_line = (
        format_attendance_admin_line(booking, lang)
        if admin_view
        else format_attendance_client_line(booking, lang)
    )
    if attendance_line:
        lines.append(attendance_line)
    lines.append(t(lang, "booking_status_line", status=status))
    return "\n".join(lines)


def format_booking_short(booking: Booking, lang: str = "ru") -> str:
    status = status_label(lang, booking.status.value)
    return f"{format_datetime(booking.start_at)} — {escape(booking.client_name)} ({status})"


def format_client_booking_detail(booking: Booking, service: Service, lang: str = "ru") -> str:
    service_name = escape(service.name) if service else f"#{booking.service_id}"
    status = status_label(lang, booking.status.value)
    if booking.service_location_title:
        service_location = escape(booking.service_location_title)
        if booking.service_location_address:
            service_location += f"\n{t(lang, 'address_label', address=escape(booking.service_location_address))}"
    else:
        service_location = t(lang, "not_provided")
    lines = [
        f"{t(lang, 'my_booking_detail_title')}\n",
        f"{t(lang, 'label_service')}: {service_name}",
        f"{t(lang, 'label_datetime')}: {format_datetime(booking.start_at)}",
        f"{t(lang, 'my_booking_service_location')}: {service_location}",
    ]
    if booking.location_text or service.requires_location:
        client_address = escape(booking.location_text) if booking.location_text else t(lang, "not_provided")
        lines.append(f"{t(lang, 'my_booking_client_address')}: {client_address}")
    if booking.client_comment or service.ask_client_comment:
        comment = (
            escape(booking.client_comment)
            if booking.client_comment
            else t(lang, "comment_not_provided")
        )
        lines.append(f"{t(lang, 'my_booking_comment')}: {comment}")
    from app.services.attendance_service import format_attendance_client_line

    attendance_line = format_attendance_client_line(booking, lang)
    if attendance_line:
        lines.append(attendance_line)
    lines.append(t(lang, "booking_status_line", status=status))
    return "\n".join(lines)


def parse_time(text: str) -> time | None:
    text = text.strip()
    for fmt in ("%H:%M", "%H.%M"):
        try:
            return datetime.strptime(text, fmt).time()
        except ValueError:
            continue
    return None


def parse_date(text: str) -> date | None:
    text = text.strip()
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None
