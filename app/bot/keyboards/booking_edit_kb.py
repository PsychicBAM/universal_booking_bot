from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.i18n import t
from app.models import ServiceLocation
from app.utils.datetime_utils import slot_to_callback
from app.utils.formatting import format_date


def client_booking_detail_kb(
    booking_id: int,
    lang: str = "ru",
    *,
    can_reschedule: bool = False,
    can_cancel: bool = False,
    can_change_location: bool = False,
    can_change_address: bool = False,
    can_change_comment: bool = False,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if can_reschedule:
        rows.append(
            [InlineKeyboardButton(text=t(lang, "reschedule_booking_btn"), callback_data=f"my:res:{booking_id}")]
        )
    if can_change_location:
        rows.append(
            [InlineKeyboardButton(text=t(lang, "change_location_btn"), callback_data=f"my:loc:{booking_id}")]
        )
    if can_change_address:
        rows.append(
            [InlineKeyboardButton(text=t(lang, "change_address_btn"), callback_data=f"my:addr:{booking_id}")]
        )
    if can_change_comment:
        rows.append(
            [InlineKeyboardButton(text=t(lang, "change_comment_btn"), callback_data=f"my:comment:{booking_id}")]
        )
    if can_cancel:
        rows.append(
            [InlineKeyboardButton(text=t(lang, "cancel_booking_btn"), callback_data=f"my:cancel:{booking_id}")]
        )
    rows.append(
        [InlineKeyboardButton(text=t(lang, "back_to_my_bookings"), callback_data="my_bookings")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def reschedule_dates_kb(booking_id: int, dates: list, lang: str = "ru") -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=format_date(d),
                callback_data=f"my:res:date:{booking_id}:{d.isoformat()}",
            )
        ]
        for d in dates
    ]
    rows.append(
        [InlineKeyboardButton(text=t(lang, "back"), callback_data=f"my:view:{booking_id}")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def reschedule_times_kb(booking_id: int, slots: list, lang: str = "ru") -> InlineKeyboardMarkup:
    from app.utils.formatting import format_time

    rows = [
        [
            InlineKeyboardButton(
                text=format_time(slot),
                callback_data=f"my:res:time:{booking_id}:{slot_to_callback(slot)}",
            )
        ]
        for slot in slots
    ]
    rows.append(
        [InlineKeyboardButton(text=t(lang, "back"), callback_data=f"my:res:{booking_id}")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def reschedule_confirm_kb(booking_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "confirm_reschedule_btn"),
                    callback_data=f"my:res:confirm:{booking_id}",
                ),
                InlineKeyboardButton(text=t(lang, "cancel"), callback_data=f"my:view:{booking_id}"),
            ]
        ]
    )


def edit_location_kb(
    booking_id: int, locations: list[ServiceLocation], lang: str = "ru"
) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=location.title,
                callback_data=f"my:loc:set:{booking_id}:{location.id}",
            )
        ]
        for location in locations
    ]
    rows.append(
        [InlineKeyboardButton(text=t(lang, "back"), callback_data=f"my:view:{booking_id}")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)
