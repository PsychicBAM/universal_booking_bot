from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.i18n import t
from app.bot.keyboards.booking_time_kb import dates_kb, time_grid_kb, time_periods_kb
from app.bot.utils.time_periods import Period
from app.models import ServiceLocation
from app.utils.datetime_utils import slot_to_callback


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
    return dates_kb(
        dates,
        lang,
        date_cb=lambda d: f"my:res:date:{booking_id}:{d.isoformat()}",
        back_cb=f"my:view:{booking_id}",
        cancel_cb=f"my:view:{booking_id}",
        back_label_key="reschedule_back_to_booking",
    )


def reschedule_time_periods_kb(
    booking_id: int,
    available_periods: list[Period],
    lang: str = "ru",
) -> InlineKeyboardMarkup:
    return time_periods_kb(
        available_periods,
        lang,
        period_cb=lambda period: f"my:res:period:{booking_id}:{period}",
        back_cb=f"my:res:back:dates:{booking_id}",
        cancel_cb=f"my:view:{booking_id}",
    )


def reschedule_time_grid_kb(booking_id: int, slots: list, lang: str = "ru") -> InlineKeyboardMarkup:
    return time_grid_kb(
        slots,
        lang,
        time_cb=lambda slot: f"my:res:time:{booking_id}:{slot_to_callback(slot)}",
        back_cb=f"my:res:back:periods:{booking_id}",
        cancel_cb=f"my:view:{booking_id}",
    )


def reschedule_confirm_kb(booking_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "confirm_reschedule_btn"),
                    callback_data=f"my:res:confirm:{booking_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "booking_back_to_time"),
                    callback_data=f"my:res:back:time:{booking_id}",
                )
            ],
            [InlineKeyboardButton(text=t(lang, "cancel"), callback_data=f"my:view:{booking_id}")],
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
