from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.i18n import t
from app.models import Booking
from app.services.admin_bookings_service import (
    format_folder_booking_button,
    normalize_bookings_section,
)

_HUB_SECTIONS = (
    "upcoming",
    "pending_admin",
    "confirmed_bookings",
    "waiting_client_response",
    "needs_change",
    "history",
    "cancelled",
)


def _list_cb(section: str, page: int) -> str:
    return f"adm_book:list:{normalize_bookings_section(section)}:{page}"


def _view_cb(booking_id: int, section: str, page: int) -> str:
    return f"adm_book:view:{booking_id}:from:{normalize_bookings_section(section)}:{page}"


def admin_bookings_hub_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=t(lang, f"bookings_folder_{section}"), callback_data=_list_cb(section, 0))]
        for section in _HUB_SECTIONS
    ]
    rows.append(
        [InlineKeyboardButton(text=t(lang, "back_to_admin_panel"), callback_data="adm_book:admin_back")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_bookings_folder_kb(
    bookings: list[Booking],
    section: str,
    page: int,
    total_pages: int,
    lang: str = "ru",
) -> InlineKeyboardMarkup:
    section = normalize_bookings_section(section)
    rows: list[list[InlineKeyboardButton]] = []
    for booking in bookings:
        label = format_folder_booking_button(booking, section, lang)
        rows.append(
            [
                InlineKeyboardButton(
                    text=label,
                    callback_data=_view_cb(booking.id, section, page),
                )
            ]
        )
    if total_pages > 1:
        nav: list[InlineKeyboardButton] = []
        if page > 0:
            nav.append(
                InlineKeyboardButton(
                    text=t(lang, "pagination_prev"),
                    callback_data=_list_cb(section, page - 1),
                )
            )
        if page < total_pages - 1:
            nav.append(
                InlineKeyboardButton(
                    text=t(lang, "pagination_next"),
                    callback_data=_list_cb(section, page + 1),
                )
            )
        if nav:
            rows.append(nav)
    rows.append([InlineKeyboardButton(text=t(lang, "bookings_back_to_hub"), callback_data="adm_book:hub")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_booking_detail_kb(
    booking_id: int,
    status: str,
    section: str,
    page: int,
    lang: str = "ru",
    *,
    show_send_confirmation: bool = True,
) -> InlineKeyboardMarkup:
    section = normalize_bookings_section(section)
    back_cb = _list_cb(section, page)
    back = f"from:{section}:{page}"
    rows: list[list[InlineKeyboardButton]] = []
    if status == "pending":
        rows.append(
            [InlineKeyboardButton(text=t(lang, "confirm_booking_btn"), callback_data=f"adm_confirm:{booking_id}")]
        )
    if status in ("pending", "confirmed"):
        rows.append(
            [InlineKeyboardButton(text=t(lang, "cancel_booking_btn"), callback_data=f"adm_cancel:{booking_id}")]
        )
        rows.append(
            [InlineKeyboardButton(text=t(lang, "message_client_btn"), callback_data=f"adm_msg:{booking_id}")]
        )
        if status == "confirmed" and show_send_confirmation:
            rows.append(
                [
                    InlineKeyboardButton(
                        text=t(lang, "admin_attendance_send_question"),
                        callback_data=f"adm_att:send:{booking_id}:{back}",
                    )
                ]
            )
    rows.append([InlineKeyboardButton(text=t(lang, "back"), callback_data=back_cb)])
    return InlineKeyboardMarkup(inline_keyboard=rows)
