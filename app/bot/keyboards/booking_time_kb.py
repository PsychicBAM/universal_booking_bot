from collections.abc import Callable
from datetime import date, datetime

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.i18n import t, weekday_name
from app.bot.utils.time_periods import PERIOD_ORDER, Period
from app.utils.datetime_utils import slot_to_callback
from app.utils.formatting import format_time


def _chunk(items: list, size: int) -> list[list]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def dates_kb(
    dates: list,
    lang: str = "ru",
    *,
    date_cb: Callable[[date], str] | None = None,
    back_cb: str = "bk:back:service",
    cancel_cb: str = "cancel",
    back_label_key: str = "booking_back_to_service",
) -> InlineKeyboardMarkup:
    if date_cb is None:
        date_cb = lambda d: f"date:{d.isoformat()}"
    buttons = [
        InlineKeyboardButton(
            text=f"{d.strftime('%d.%m')} {weekday_name(lang, d.weekday(), short=True)}",
            callback_data=date_cb(d),
        )
        for d in dates[:14]
    ]
    rows = _chunk(buttons, 3)
    rows.append([InlineKeyboardButton(text=t(lang, back_label_key), callback_data=back_cb)])
    rows.append([InlineKeyboardButton(text=t(lang, "cancel"), callback_data=cancel_cb)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def time_periods_kb(
    available_periods: list[Period],
    lang: str = "ru",
    *,
    period_cb: Callable[[Period], str] | None = None,
    back_cb: str = "bk:back:dates",
    cancel_cb: str = "cancel",
) -> InlineKeyboardMarkup:
    if period_cb is None:
        period_cb = lambda period: f"bk:period:{period}"
    rows: list[list[InlineKeyboardButton]] = []
    for period in PERIOD_ORDER:
        if period in available_periods:
            rows.append(
                [
                    InlineKeyboardButton(
                        text=t(lang, f"booking_period_{period}"),
                        callback_data=period_cb(period),
                    )
                ]
            )
    rows.append([InlineKeyboardButton(text=t(lang, "booking_back_to_dates"), callback_data=back_cb)])
    rows.append([InlineKeyboardButton(text=t(lang, "cancel"), callback_data=cancel_cb)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def time_grid_kb(
    slots: list,
    lang: str = "ru",
    *,
    time_cb: Callable[[datetime], str] | None = None,
    back_cb: str = "bk:back:periods",
    cancel_cb: str = "cancel",
) -> InlineKeyboardMarkup:
    if time_cb is None:
        time_cb = lambda slot: f"time:{slot_to_callback(slot)}"
    buttons = [
        InlineKeyboardButton(text=format_time(slot), callback_data=time_cb(slot))
        for slot in slots
    ]
    rows = _chunk(buttons, 3)
    rows.append([InlineKeyboardButton(text=t(lang, "booking_back_to_periods"), callback_data=back_cb)])
    rows.append([InlineKeyboardButton(text=t(lang, "cancel"), callback_data=cancel_cb)])
    return InlineKeyboardMarkup(inline_keyboard=rows)
