from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.i18n import t
from app.models import Booking
from app.services.admin_bookings_service import (
    BookingDetailSource,
    booking_detail_action_flags,
    booking_detail_back_callback,
    build_booking_view_callback,
    encode_attendance_back,
    format_folder_booking_button,
    normalize_bookings_section,
)

_HUB_ACTIONS: tuple[tuple[str, str], ...] = (
    ("active", "bookings_all_active_button"),
    ("pending_admin", "bookings_pending_admin_button"),
    ("history", "bookings_folder_history"),
    ("cancelled", "bookings_folder_cancelled"),
)


def _list_cb(section: str, page: int) -> str:
    return f"adm_book:list:{normalize_bookings_section(section)}:{page}"


def _view_cb(booking_id: int, section: str, page: int) -> str:
    return build_booking_view_callback(
        booking_id,
        BookingDetailSource(section=normalize_bookings_section(section), page=page),
    )


def admin_bookings_hub_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=t(lang, button_key), callback_data=_list_cb(section, 0))]
        for section, button_key in _HUB_ACTIONS
    ]
    rows.append(
        [InlineKeyboardButton(text=t(lang, "bookings_search_button"), callback_data="adm_book:search")]
    )
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
    *,
    service_names: dict[int, str] | None = None,
) -> InlineKeyboardMarkup:
    section = normalize_bookings_section(section)
    service_names = service_names or {}
    rows: list[list[InlineKeyboardButton]] = []
    for booking in bookings:
        label = format_folder_booking_button(
            booking,
            section,
            lang,
            service_name=service_names.get(booking.service_id),
        )
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
    booking: Booking,
    source: BookingDetailSource,
    lang: str = "ru",
    *,
    show_send_confirmation: bool = True,
) -> InlineKeyboardMarkup:
    flags = booking_detail_action_flags(booking, show_send_confirmation=show_send_confirmation)
    back_cb = booking_detail_back_callback(source)
    back = encode_attendance_back(source)
    booking_id = booking.id
    rows: list[list[InlineKeyboardButton]] = []
    if flags["can_confirm"]:
        rows.append(
            [InlineKeyboardButton(text=t(lang, "confirm_booking_btn"), callback_data=f"adm_confirm:{booking_id}")]
        )
    if flags["can_cancel"]:
        rows.append(
            [InlineKeyboardButton(text=t(lang, "cancel_booking_btn"), callback_data=f"adm_cancel:{booking_id}")]
        )
    if flags["show_message"]:
        rows.append(
            [InlineKeyboardButton(text=t(lang, "message_client_btn"), callback_data=f"adm_msg:{booking_id}")]
        )
    if flags["can_send_confirmation"]:
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
