from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.i18n import t
from app.bot.utils.attendance_helpers import attendance_admin_label_indicator
from app.models import Booking
from app.utils.datetime_utils import to_local_naive

DEFAULT_FILTER = "7d"


def _list_cb(filter_key: str, page: int) -> str:
    return f"adm_att:list:{filter_key}:{page}"


def _view_cb(booking_id: int, back: str) -> str:
    return f"adm_att:view:{booking_id}:{back}"


def _parse_back_to_list_cb(back: str) -> str:
    if not back.startswith("list:"):
        return _list_cb(DEFAULT_FILTER, 0)
    parts = back.removeprefix("list:").split(":")
    filt = parts[0] if parts else DEFAULT_FILTER
    page = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
    return _list_cb(filt, page)


def admin_attendance_filters_kb(filter_key: str, lang: str = "ru") -> list[list[InlineKeyboardButton]]:
    filters = (
        ("today", "admin_attendance_filter_today"),
        ("tomorrow", "admin_attendance_filter_tomorrow"),
        ("7d", "admin_attendance_filter_7d"),
        ("all", "admin_attendance_filter_all"),
        ("noresp", "admin_attendance_filter_no_response"),
    )
    row1: list[InlineKeyboardButton] = []
    row2: list[InlineKeyboardButton] = []
    for idx, (key, label_key) in enumerate(filters):
        prefix = "• " if key == filter_key else ""
        btn = InlineKeyboardButton(
            text=f"{prefix}{t(lang, label_key)}",
            callback_data=_list_cb(key, 0),
        )
        (row1 if idx < 3 else row2).append(btn)
    return [row1, row2]


def admin_attendance_list_kb(
    bookings: list[Booking],
    filter_key: str,
    page: int,
    total_pages: int,
    lang: str = "ru",
) -> InlineKeyboardMarkup:
    rows = admin_attendance_filters_kb(filter_key, lang)
    for booking in bookings:
        start = to_local_naive(booking.start_at)
        indicator = attendance_admin_label_indicator(booking)
        label = (
            f"{indicator} #{booking.id} {start.strftime('%d.%m')} "
            f"{start.strftime('%H:%M')} — {booking.client_name}"
        )
        rows.append(
            [
                InlineKeyboardButton(
                    text=label,
                    callback_data=_view_cb(booking.id, f"list:{filter_key}:{page}"),
                )
            ]
        )
    if total_pages > 1:
        nav: list[InlineKeyboardButton] = []
        if page > 0:
            nav.append(
                InlineKeyboardButton(
                    text=t(lang, "pagination_prev"),
                    callback_data=_list_cb(filter_key, page - 1),
                )
            )
        if page < total_pages - 1:
            nav.append(
                InlineKeyboardButton(
                    text=t(lang, "pagination_next"),
                    callback_data=_list_cb(filter_key, page + 1),
                )
            )
        if nav:
            rows.append(nav)
    rows.append([InlineKeyboardButton(text=t(lang, "back"), callback_data="adm_bookings:list")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_attendance_detail_kb(
    booking_id: int,
    back: str,
    lang: str = "ru",
) -> InlineKeyboardMarkup:
    if back.startswith("list:"):
        back_cb = _parse_back_to_list_cb(back)
        back_label = t(lang, "admin_attendance_back_to_list")
    else:
        back_cb = f"adm_booking:{booking_id}"
        back_label = t(lang, "back")
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "admin_attendance_send_question"),
                    callback_data=f"adm_att:send:{booking_id}:{back}",
                )
            ],
            [InlineKeyboardButton(text=t(lang, "message_client_btn"), callback_data=f"adm_msg:{booking_id}")],
            [InlineKeyboardButton(text=back_label, callback_data=back_cb)],
        ]
    )


def admin_attendance_resend_confirm_kb(booking_id: int, back: str, lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "admin_attendance_resend_yes"),
                    callback_data=f"adm_att:sendok:{booking_id}:{back}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "admin_attendance_resend_no"),
                    callback_data=_view_cb(booking_id, back),
                )
            ],
        ]
    )
