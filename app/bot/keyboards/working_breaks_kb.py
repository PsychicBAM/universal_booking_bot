from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.i18n import t, weekday_name
from app.models import WorkingBreak


def working_breaks_day_kb(weekday: int, breaks: list[WorkingBreak], lang: str) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for br in breaks:
        label = f"{br.start_time:%H:%M}–{br.end_time:%H:%M}"
        if br.title:
            label = f"{label} — {br.title}"
        rows.append([InlineKeyboardButton(text=label, callback_data=f"br:edit:{br.id}")])
    rows.append([InlineKeyboardButton(text=t(lang, "working_break_add"), callback_data=f"br:add:{weekday}")])
    rows.append(
        [InlineKeyboardButton(text=t(lang, "working_break_back_day"), callback_data=f"br:back:weekday:{weekday}")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def working_break_add_choice_kb(weekday: int, lang: str, *, show_preset: bool) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if show_preset:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t(lang, "working_break_lunch_preset"),
                    callback_data=f"br:preset:lunch:{weekday}",
                )
            ]
        )
    rows.append(
        [InlineKeyboardButton(text=t(lang, "working_break_manual"), callback_data=f"br:manual:{weekday}")]
    )
    rows.append(
        [InlineKeyboardButton(text=t(lang, "working_break_back_day"), callback_data=f"br:back:weekday:{weekday}")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def working_break_edit_kb(br: WorkingBreak, lang: str) -> InlineKeyboardMarkup:
    toggle_label = t(lang, "working_break_toggle_off") if br.is_active else t(lang, "working_break_toggle_on")
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "working_break_edit_time"), callback_data=f"br:edit_time:{br.id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "working_break_edit_title_btn"), callback_data=f"br:edit_title:{br.id}"
                )
            ],
            [InlineKeyboardButton(text=toggle_label, callback_data=f"br:toggle:{br.id}")],
            [InlineKeyboardButton(text=t(lang, "working_break_delete"), callback_data=f"br:delete:{br.id}")],
            [
                InlineKeyboardButton(
                    text=t(lang, "working_break_back_list"), callback_data=f"br:list:{br.weekday}"
                )
            ],
        ]
    )


def working_break_delete_confirm_kb(break_id: int, weekday: int, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "working_break_delete_yes"), callback_data=f"br:delete:yes:{break_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "working_break_delete_no"), callback_data=f"br:edit:{break_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "working_break_back_list"), callback_data=f"br:list:{weekday}"
                )
            ],
        ]
    )


def working_break_weekday_pick_kb(lang: str) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=weekday_name(lang, day), callback_data=f"br:pick_day:{day}")]
        for day in range(7)
    ]
    rows.append([InlineKeyboardButton(text=t(lang, "wh_back_schedule"), callback_data="wh:list")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def working_break_skip_title_kb(lang: str) -> InlineKeyboardMarkup:
    from app.bot.keyboards import skip_cancel_kb

    return skip_cancel_kb(lang)
