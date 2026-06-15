from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.i18n import t
from app.bot.utils.booking_labels import format_admin_booking_button
from app.models import Booking
from app.services.admin_bookings_service import parse_attendance_back

DEFAULT_FILTER = "7d"


def _list_cb(filter_key: str, page: int) -> str:
    return f"adm_att:list:{filter_key}:{page}"


def _view_cb(booking_id: int, back: str) -> str:
    return f"adm_att:view:{booking_id}:{back}"


def _bookings_list_cb(section: str, page: int) -> str:
    return f"adm_book:list:{section}:{page}"


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
        rows.append(
            [
                InlineKeyboardButton(
                    text=format_admin_booking_button(booking, lang),
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
    rows.append([InlineKeyboardButton(text=t(lang, "bookings_back_to_hub"), callback_data="adm_book:hub")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_attendance_detail_kb(
    booking_id: int,
    back: str,
    lang: str = "ru",
) -> InlineKeyboardMarkup:
    section, page = parse_attendance_back(back)
    back_cb = _bookings_list_cb(section, page)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "admin_attendance_send_question"),
                    callback_data=f"adm_att:send:{booking_id}:{back}",
                )
            ],
            [InlineKeyboardButton(text=t(lang, "message_client_btn"), callback_data=f"adm_msg:{booking_id}")],
            [InlineKeyboardButton(text=t(lang, "back"), callback_data=back_cb)],
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
