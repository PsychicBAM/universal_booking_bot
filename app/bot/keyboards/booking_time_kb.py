from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.i18n import t, weekday_name
from app.bot.utils.time_periods import PERIOD_ORDER, Period
from app.utils.datetime_utils import slot_to_callback
from app.utils.formatting import format_time


def _chunk(items: list, size: int) -> list[list]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def dates_kb(dates: list, lang: str = "ru", prefix: str = "date") -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(
            text=f"{d.strftime('%d.%m')} {weekday_name(lang, d.weekday(), short=True)}",
            callback_data=f"{prefix}:{d.isoformat()}",
        )
        for d in dates[:14]
    ]
    rows = _chunk(buttons, 3)
    rows.append(
        [InlineKeyboardButton(text=t(lang, "booking_back_to_service"), callback_data="bk:back:service")]
    )
    rows.append([InlineKeyboardButton(text=t(lang, "cancel"), callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def time_periods_kb(available_periods: list[Period], lang: str = "ru") -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for period in PERIOD_ORDER:
        if period in available_periods:
            rows.append(
                [
                    InlineKeyboardButton(
                        text=t(lang, f"booking_period_{period}"),
                        callback_data=f"bk:period:{period}",
                    )
                ]
            )
    rows.append(
        [InlineKeyboardButton(text=t(lang, "booking_back_to_dates"), callback_data="bk:back:dates")]
    )
    rows.append([InlineKeyboardButton(text=t(lang, "cancel"), callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def time_grid_kb(slots: list, lang: str = "ru", prefix: str = "time") -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(text=format_time(slot), callback_data=f"{prefix}:{slot_to_callback(slot)}")
        for slot in slots
    ]
    rows = _chunk(buttons, 3)
    rows.append(
        [InlineKeyboardButton(text=t(lang, "booking_back_to_periods"), callback_data="bk:back:periods")]
    )
    rows.append([InlineKeyboardButton(text=t(lang, "cancel"), callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
