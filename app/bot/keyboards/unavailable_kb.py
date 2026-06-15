from datetime import date

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.i18n import t
from app.services.unavailable_service import (
    DATE_PICKER_OFFSETS,
    TIME_RANGE_PRESETS,
    UnavailableItem,
    date_from_offset,
)
from app.utils.formatting import format_date


def unavailable_main_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "unav_tomorrow"), callback_data="unav:tomorrow")],
            [InlineKeyboardButton(text=t(lang, "unav_next7"), callback_data="unav:next7")],
            [InlineKeyboardButton(text=t(lang, "unav_block_day"), callback_data="unav:day")],
            [InlineKeyboardButton(text=t(lang, "unav_block_time"), callback_data="unav:time")],
            [InlineKeyboardButton(text=t(lang, "unav_list"), callback_data="unav:items")],
            [InlineKeyboardButton(text=t(lang, "wh_back_schedule"), callback_data="sch:main")],
        ]
    )


def unavailable_confirm_kb(
    confirm_data: str,
    cancel_data: str,
    lang: str = "ru",
    *,
    yes_key: str = "unav_confirm_yes",
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, yes_key), callback_data=confirm_data)],
            [InlineKeyboardButton(text=t(lang, "unav_confirm_no"), callback_data=cancel_data)],
        ]
    )


def unavailable_date_picker_kb(back_data: str, lang: str = "ru") -> InlineKeyboardMarkup:
    rows = []
    for offset in DATE_PICKER_OFFSETS:
        rows.append(
            [
                InlineKeyboardButton(
                    text=_date_picker_label(lang, offset),
                    callback_data=f"unav:dp:{offset}",
                )
            ]
        )
    rows.append(
        [InlineKeyboardButton(text=t(lang, "unav_enter_date_manual"), callback_data="unav:dp:manual")]
    )
    rows.append([InlineKeyboardButton(text=t(lang, "back"), callback_data=back_data)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def unavailable_time_presets_kb(target_date: date, lang: str = "ru") -> InlineKeyboardMarkup:
    iso = target_date.isoformat()
    rows = []
    for idx, (start, end) in enumerate(TIME_RANGE_PRESETS):
        label = f"{start:%H:%M}–{end:%H:%M}"
        rows.append([InlineKeyboardButton(text=label, callback_data=f"unav:tr:{iso}:{idx}")])
    rows.append(
        [InlineKeyboardButton(text=t(lang, "unav_full_day"), callback_data=f"unav:tr:{iso}:fd")]
    )
    rows.append(
        [InlineKeyboardButton(text=t(lang, "unav_enter_time_manual"), callback_data=f"unav:tr:{iso}:manual")]
    )
    rows.append([InlineKeyboardButton(text=t(lang, "back"), callback_data="unav:time")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def unavailable_items_kb(items: list[UnavailableItem], lang: str = "ru") -> InlineKeyboardMarkup:
    rows = []
    for item in items[:20]:
        rows.append(
            [
                InlineKeyboardButton(
                    text=_item_button_label(item, lang),
                    callback_data=f"unav:del:{item.kind}:{item.id}",
                )
            ]
        )
    rows.append([InlineKeyboardButton(text=t(lang, "back"), callback_data="unav:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def unavailable_delete_confirm_kb(kind: str, item_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "unav_delete_yes"),
                    callback_data=f"unav:del_confirm:{kind}:{item_id}",
                )
            ],
            [InlineKeyboardButton(text=t(lang, "unav_confirm_no"), callback_data="unav:items")],
        ]
    )


def _date_picker_label(lang: str, offset: int) -> str:
    if offset == 0:
        return t(lang, "unav_date_today")
    if offset == 1:
        return t(lang, "unav_date_tomorrow")
    if offset == 2:
        return t(lang, "unav_date_after_tomorrow")
    return t(lang, "unav_date_plus", days=str(offset))


def _item_button_label(item: UnavailableItem, lang: str) -> str:
    date_s = format_date(item.target_date)
    if item.kind == "date":
        return t(lang, "unav_item_full_day_btn", date=date_s)
    return t(
        lang,
        "unav_item_time_btn",
        date=date_s,
        start=item.start_time.strftime("%H:%M"),
        end=item.end_time.strftime("%H:%M"),
    )
