from datetime import date, datetime, time
from html import escape

from app.bot.i18n import format_buffer, format_duration, status_label, t
from app.models import (
    PRICE_MODE_EXACT,
    PRICE_MODE_FROM,
    VALID_PRICE_MODES,
    Booking,
    BookingStatus,
    Service,
    ServiceOrder,
    ServiceOrderStatus,
)


def normalize_price_mode(service: Service | object) -> str:
    mode = getattr(service, "price_mode", None) or PRICE_MODE_EXACT
    key = str(mode).strip().lower()
    return key if key in VALID_PRICE_MODES else PRICE_MODE_EXACT


def format_service_price_amount(service: Service | object, lang: str = "ru") -> str:
    price = int(getattr(service, "price", 0) or 0)
    if not price:
        return t(lang, "price_free")
    amount = f"{price} ₽"
    if normalize_price_mode(service) == PRICE_MODE_FROM:
        return t(lang, "price_from_amount", amount=amount)
    return amount


def format_service_price(service: Service | object, lang: str = "ru") -> str:
    price = int(getattr(service, "price", 0) or 0)
    if not price:
        return t(lang, "price_free")
    return t(lang, "price_label", price=format_service_price_amount(service, lang))


def format_service_price_settings_text(service: Service, lang: str = "ru") -> str:
    mode = normalize_price_mode(service)
    type_line = (
        f"✅ {t(lang, 'price_mode_from')}"
        if mode == PRICE_MODE_FROM
        else f"✅ {t(lang, 'price_mode_exact')}"
    )
    return "\n".join(
        [
            t(lang, "price_settings_title"),
            "",
            t(lang, "price_current_label", price=format_service_price_amount(service, lang)),
            t(lang, "price_type_label"),
            type_line,
        ]
    )


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
    from app.models import SERVICE_TYPE_ORDER

    price = format_service_price(service, lang)
    desc = service.description or ""
    is_order = service.service_type == SERVICE_TYPE_ORDER
    icon = "📝" if is_order else "📋"
    lines = [f"{icon} {service.name}"]
    if not is_order:
        lines.append(t(lang, "duration_label", duration=format_duration(lang, service.duration_minutes)))
        if service.buffer_after_minutes:
            lines.append(t(lang, "buffer_client_note"))
    lines.append(price)
    if desc:
        if is_order:
            lines.append(f"{t(lang, 'order_details_label')}:\n{desc}")
        else:
            lines.append(desc)
    return "\n".join(line for line in lines if line).strip()


def format_service_admin(
    service: Service,
    lang: str = "ru",
    *,
    photos_count: int = 0,
    videos_count: int = 0,
    locations_count: int = 0,
) -> str:
    from app.models import SERVICE_TYPE_ORDER

    active = t(lang, "yes") if service.is_active else t(lang, "no")
    price = format_service_price(service, lang)
    desc = escape(service.description) if service.description else ""
    media_status = t(lang, "media_enabled") if service.show_media_to_clients else t(lang, "media_disabled")
    type_line = format_service_type_line(service, lang)

    if service.service_type == SERVICE_TYPE_ORDER:
        lines = [
            f"📝 {service.name}",
            type_line,
            f"{price}",
            f"{t(lang, 'client_media_display', status=media_status)}",
            f"{t(lang, 'active_label', value=active)}",
            f"{t(lang, 'photos_count', count=str(photos_count))}",
            f"{t(lang, 'videos_count', count=str(videos_count))}",
        ]
        if desc:
            lines.append(f"{t(lang, 'order_details_label')}:\n{desc}")
        return "\n".join(lines).strip()

    location_status = t(lang, "label_enabled") if service.requires_location else t(lang, "label_disabled")
    comment_status = (
        t(lang, "label_enabled") if service.ask_client_comment else t(lang, "label_disabled")
    )
    return (
        f"📋 {service.name}\n"
        f"{type_line}\n"
        f"{t(lang, 'duration_label', duration=format_duration(lang, service.duration_minutes))}\n"
        f"{t(lang, 'buffer_after_service', buffer=format_buffer(lang, service.buffer_after_minutes))}\n"
        f"{t(lang, 'service_requires_location', status=location_status)}\n"
        f"{t(lang, 'service_comment_setting', status=comment_status)}\n"
        f"{t(lang, 'service_locations_count', count=str(locations_count))}\n"
        f"{t(lang, 'photos_count', count=str(photos_count))}\n"
        f"{t(lang, 'videos_count', count=str(videos_count))}\n"
        f"{t(lang, 'client_media_display', status=media_status)}\n"
        f"{price}\n"
        f"{t(lang, 'active_label', value=active)}\n"
        f"{desc}"
    ).strip()


def _admin_booking_status_text(booking: Booking, lang: str) -> str:
    if booking.status == BookingStatus.CANCELLED:
        key = "booking_status_cancelled"
    elif booking.status == BookingStatus.PENDING:
        key = "booking_status_pending_admin"
    elif booking.status == BookingStatus.CONFIRMED:
        key = "booking_status_confirmed"
    else:
        return t(lang, "booking_status_line", status=status_label(lang, booking.status.value))
    return t(lang, "booking_status_label", status=t(lang, key))


def _client_response_text(booking: Booking, lang: str) -> str:
    from app.bot.utils.attendance_helpers import (
        ATTENDANCE_CANNOT_ATTEND,
        ATTENDANCE_CONFIRMED,
        ATTENDANCE_REASON_PROVIDED,
        has_attendance_response,
    )

    if booking.status != BookingStatus.CONFIRMED:
        return ""
    if not has_attendance_response(booking):
        key = "client_response_no_response"
    elif booking.attendance_status == ATTENDANCE_CONFIRMED:
        key = "client_response_confirmed"
    elif booking.attendance_status in (ATTENDANCE_CANNOT_ATTEND, ATTENDANCE_REASON_PROVIDED):
        key = "client_response_needs_change"
    else:
        key = "client_response_no_response"
    return t(lang, "client_response_label", response=t(lang, key))


def format_client_cancelled_admin_notification(
    booking: Booking,
    service: Service | None,
    lang: str,
    *,
    client_username: str | None = None,
) -> str:
    service_name = escape(service.name) if service else f"#{booking.service_id}"
    tg = f"@{client_username}" if client_username else t(lang, "not_provided")
    lines = [
        t(lang, "booking_cancelled_by_client_admin_title"),
        "",
        f"{t(lang, 'label_service')}: {service_name}",
        f"{t(lang, 'label_datetime')}: {format_datetime(booking.start_at)}",
        f"{t(lang, 'label_name')}: {escape(booking.client_name)}",
        t(lang, "admin_booking_telegram_line", username=tg),
        f"{t(lang, 'label_phone')}: {escape(booking.client_phone or t(lang, 'booking_phone_not_provided'))}",
    ]
    lines.extend(_service_location_lines(booking, lang))
    lines.extend(_location_comment_lines(booking, service, lang, admin_view=True))
    lines.append(
        t(lang, "booking_status_label", status=t(lang, "booking_cancelled_by_client_admin_status"))
    )
    return "\n".join(lines)


def format_booking_rescheduled_by_client_admin_notification(
    booking: Booking,
    service: Service | None,
    lang: str,
    *,
    old_datetime: str,
    new_datetime: str,
    client_username: str | None = None,
) -> str:
    service_name = escape(service.name) if service else f"#{booking.service_id}"
    tg = f"@{client_username}" if client_username else t(lang, "not_provided")
    phone = escape(booking.client_phone or t(lang, "booking_phone_not_provided"))
    return "\n".join(
        [
            t(lang, "booking_rescheduled_by_client_admin_title"),
            "",
            f"{t(lang, 'label_service')}: {service_name}",
            f"{t(lang, 'label_name')}: {escape(booking.client_name)}",
            t(lang, "admin_booking_telegram_line", username=tg),
            f"{t(lang, 'label_phone')}: {phone}",
            t(lang, "reschedule_was_line", datetime=old_datetime),
            t(lang, "reschedule_became_line", datetime=new_datetime),
        ]
    )


def format_booking_cancelled_by_admin_client_notification(
    booking: Booking,
    service: Service | None,
    lang: str,
) -> str:
    service_name = escape(service.name) if service else f"#{booking.service_id}"
    return "\n".join(
        [
            t(lang, "booking_cancelled_by_admin_client_title"),
            "",
            t(
                lang,
                "booking_cancelled_by_admin_client_body",
                service=service_name,
                datetime=format_datetime(booking.start_at),
            ),
        ]
    )


def format_order_cancelled_by_client_admin_notification(
    order: ServiceOrder,
    service: Service | None,
    lang: str,
) -> str:
    service_name = escape(service.name) if service else f"#{order.service_id}"
    tg = f"@{order.client_username}" if order.client_username else t(lang, "not_provided")
    phone = escape(order.client_phone) if order.client_phone else t(lang, "not_provided")
    lines = [
        t(lang, "order_cancelled_by_client_admin_title"),
        "",
        f"{t(lang, 'label_service')}: {service_name}",
        f"{t(lang, 'label_name')}: {escape(order.client_name or t(lang, 'not_provided'))}",
        t(lang, "admin_booking_telegram_line", username=tg),
        f"{t(lang, 'label_phone')}: {phone}",
    ]
    if order.details:
        lines.extend(["", t(lang, "order_details_label"), escape(order.details)])
    lines.extend(
        [
            "",
            t(
                lang,
                "booking_status_label",
                status=t(lang, "order_cancelled_by_client_admin_status"),
            ),
        ]
    )
    return "\n".join(lines)


def format_order_cancelled_by_admin_client_notification(
    order: ServiceOrder,
    service: Service | None,
    lang: str,
) -> str:
    service_name = escape(service.name) if service else f"#{order.service_id}"
    return "\n".join(
        [
            t(lang, "order_cancelled_by_admin_client_title"),
            "",
            t(lang, "order_cancelled_by_admin_client_body", service=service_name),
        ]
    )


def format_booking(
    booking: Booking,
    service: Service | None = None,
    lang: str = "ru",
    *,
    admin_view: bool = False,
    show_location_comment: bool = False,
    client_username: str | None = None,
) -> str:
    service_name = escape(service.name) if service else t(lang, "client_booking_service_fallback")
    status = status_label(lang, booking.status.value)
    lines = [
        f"📋 {service_name}",
        f"📅 {format_datetime(booking.start_at)}",
        f"👤 {escape(booking.client_name)}",
        f"📞 {escape(booking.client_phone or t(lang, 'booking_phone_not_provided'))}",
    ]
    if admin_view:
        lines.insert(2, t(lang, "booking_id_label", id=str(booking.id)))
        tg = f"@{client_username}" if client_username else t(lang, "not_provided")
        lines.insert(4, t(lang, "admin_booking_telegram_line", username=tg))
    lines.extend(_service_location_lines(booking, lang))
    if show_location_comment or admin_view:
        lines.extend(_location_comment_lines(booking, service, lang, admin_view=admin_view))
    if admin_view:
        lines.append(_admin_booking_status_text(booking, lang))
        client_response = _client_response_text(booking, lang)
        if client_response:
            lines.append(client_response)
    else:
        from app.services.attendance_service import format_attendance_client_line

        attendance_line = format_attendance_client_line(booking, lang)
        if attendance_line:
            lines.append(attendance_line)
        lines.append(t(lang, "booking_status_line", status=status))
    return "\n".join(lines)


def format_booking_short(booking: Booking, lang: str = "ru") -> str:
    status = status_label(lang, booking.status.value)
    return f"{format_datetime(booking.start_at)} — {escape(booking.client_name)} ({status})"


def format_client_booking_detail(booking: Booking, service: Service, lang: str = "ru") -> str:
    service_name = (
        escape(service.name)
        if service and service.name
        else t(lang, "client_booking_service_fallback")
    )
    status = status_label(lang, booking.status.value)
    lines = [
        f"📋 {service_name}",
        f"📅 {format_datetime(booking.start_at)}",
    ]
    if booking.service_location_title:
        lines.append(
            f"📍 {t(lang, 'my_booking_service_location')}: {escape(booking.service_location_title)}"
        )
        if booking.service_location_address:
            lines.append(
                t(lang, "address_label", address=escape(booking.service_location_address))
            )
    if booking.location_text or (service and service.requires_location):
        client_address = escape(booking.location_text) if booking.location_text else t(lang, "not_provided")
        lines.append(f"📍 {t(lang, 'my_booking_client_address')}: {client_address}")
    if booking.client_comment or (service and service.ask_client_comment):
        comment = (
            escape(booking.client_comment)
            if booking.client_comment
            else t(lang, "comment_not_provided")
        )
        lines.append(f"💬 {t(lang, 'my_booking_comment')}: {comment}")
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


def _order_status_label(lang: str, status: str) -> str:
    from app.bot.i18n import t

    key = f"order_status_{status}"
    known = {
        "order_status_new",
        "order_status_accepted",
        "order_status_in_progress",
        "order_status_completed",
        "order_status_cancelled",
        "order_status_declined",
    }
    return t(lang, key) if key in known else status


def format_order_admin(
    order: ServiceOrder,
    service: Service | None,
    lang: str,
    *,
    title_key: str = "order_detail_title",
) -> str:
    from app.bot.i18n import t

    service_name = escape(service.name) if service else f"#{order.service_id}"
    tg = f"@{order.client_username}" if order.client_username else t(lang, "not_provided")
    phone = escape(order.client_phone) if order.client_phone else t(lang, "not_provided")
    lines = [
        t(lang, title_key),
        "",
        f"{t(lang, 'label_service')}: {service_name}",
        f"{t(lang, 'label_name')}: {escape(order.client_name or t(lang, 'not_provided'))}",
        t(lang, "admin_booking_telegram_line", username=tg),
        f"{t(lang, 'label_phone')}: {phone}",
    ]
    if order.details:
        lines.extend(["", t(lang, "order_details_label"), escape(order.details)])
    lines.extend(
        [
            "",
            f"{t(lang, 'order_created_at')}: {format_datetime(order.created_at)}",
            f"{t(lang, 'booking_status_line', status=_order_status_label(lang, order.status))}",
        ]
    )
    if order.status == ServiceOrderStatus.DECLINED.value and order.decline_reason:
        lines.extend(["", t(lang, "order_decline_reason_label"), escape(order.decline_reason)])
    if order.admin_note:
        lines.extend(["", t(lang, "order_admin_note_label"), escape(order.admin_note)])
    return "\n".join(lines)


def format_order_client(order: ServiceOrder, service: Service | None, lang: str) -> str:
    from app.bot.i18n import t
    from app.models import ServiceOrderStatus

    service_name = escape(service.name) if service else f"#{order.service_id}"
    lines = [
        f"{t(lang, 'label_service')}: {service_name}",
        f"{t(lang, 'order_created_at')}: {format_datetime(order.created_at)}",
    ]
    if order.details:
        lines.append(f"{t(lang, 'order_details_label')}: {escape(order.details)}")
    lines.append(t(lang, "booking_status_line", status=_order_status_label(lang, order.status)))
    if order.status == ServiceOrderStatus.DECLINED.value and order.decline_reason:
        lines.extend(["", t(lang, "order_decline_reason_label"), escape(order.decline_reason)])
    return "\n".join(lines)


def format_order_accepted_client_notification(
    order: ServiceOrder,
    service: Service | None,
    lang: str,
) -> str:
    from app.bot.i18n import t

    service_name = escape(service.name) if service else f"#{order.service_id}"
    return "\n".join(
        [
            t(lang, "order_accepted_client"),
            "",
            f"{t(lang, 'label_service')}: {service_name}",
            "",
            t(lang, "order_accepted_client_body"),
        ]
    )


def format_order_declined_client_notification(
    order: ServiceOrder,
    service: Service | None,
    lang: str,
) -> str:
    from app.bot.i18n import t

    service_name = escape(service.name) if service else f"#{order.service_id}"
    lines = [
        t(lang, "order_declined_client"),
        "",
        f"{t(lang, 'label_service')}: {service_name}",
        "",
        t(lang, "order_decline_reason_label"),
        escape(order.decline_reason or ""),
    ]
    return "\n".join(lines)


def format_order_new_message_admin_notification(
    order: ServiceOrder,
    service: Service | None,
    message_text: str,
    lang: str,
) -> str:
    from app.bot.i18n import t

    service_name = escape(service.name) if service else f"#{order.service_id}"
    return "\n".join(
        [
            t(lang, "order_new_message_admin_title"),
            "",
            f"{t(lang, 'label_service')}: {service_name}",
            f"{t(lang, 'label_name')}: {escape(order.client_name or t(lang, 'not_provided'))}",
            f"{t(lang, 'booking_status_line', status=_order_status_label(lang, order.status))}",
            "",
            t(lang, "order_message_label"),
            escape(message_text),
        ]
    )


def format_order_new_message_client_notification(
    order: ServiceOrder,
    service: Service | None,
    message_text: str,
    lang: str,
) -> str:
    from app.bot.i18n import t

    service_name = escape(service.name) if service else f"#{order.service_id}"
    return "\n".join(
        [
            t(lang, "order_new_message_client_title"),
            "",
            f"{t(lang, 'label_service')}: {service_name}",
            "",
            escape(message_text),
        ]
    )


def format_order_message_history(messages, lang: str) -> str:
    from app.bot.i18n import t
    from app.utils.datetime_utils import to_local_naive

    lines = [t(lang, "order_history_title"), ""]
    if not messages:
        lines.append(t(lang, "order_history_empty"))
        return "\n".join(lines)
    for message in messages[-20:]:
        dt = to_local_naive(message.created_at).strftime("%d.%m %H:%M")
        if message.sender_type == "client":
            sender = t(lang, "order_history_sender_client")
        elif message.sender_type == "admin":
            sender = t(lang, "order_history_sender_admin")
        else:
            sender = t(lang, "order_history_sender_system")
        lines.append(f"{dt} {sender}:")
        lines.append(escape(message.message_text))
        lines.append("")
    return "\n".join(lines).rstrip()


def format_service_type_line(service: Service, lang: str) -> str:
    from app.bot.i18n import t
    from app.models import SERVICE_TYPE_ORDER

    key = "service_type_order" if service.service_type == SERVICE_TYPE_ORDER else "service_type_booking"
    return t(lang, key)

