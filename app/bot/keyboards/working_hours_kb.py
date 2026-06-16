from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.i18n import t
from app.services.working_hours_service import DAY_TIME_PRESETS


def working_hours_main_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=weekday_name(lang, day), callback_data=f"wh:day:{day}")]
        for day in range(7)
    ]
    rows.append([InlineKeyboardButton(text=t(lang, "wh_quick_presets"), callback_data="wh:presets")])
    rows.append([InlineKeyboardButton(text=t(lang, "wh_week_off"), callback_data="wh:week_off")])
    rows.append([InlineKeyboardButton(text=t(lang, "wh_back_schedule"), callback_data="sch:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def working_hours_day_kb(day: int, is_working: bool, lang: str = "ru") -> InlineKeyboardMarkup:
    toggle = t(lang, "wh_toggle_to_off") if is_working else t(lang, "wh_toggle_to_on")
    rows = [
        [InlineKeyboardButton(text=toggle, callback_data=f"wh:day:toggle:{day}")],
        [InlineKeyboardButton(text=t(lang, "wh_change_time"), callback_data=f"wh:day:time:{day}")],
    ]
    if is_working:
        rows.extend(
            [
                [InlineKeyboardButton(text=t(lang, "working_break_add"), callback_data=f"br:add:{day}")],
                [InlineKeyboardButton(text=t(lang, "working_break_edit"), callback_data=f"br:list:{day}")],
                [InlineKeyboardButton(text=t(lang, "working_break_delete"), callback_data=f"br:list:{day}")],
            ]
        )
    rows.append([InlineKeyboardButton(text=t(lang, "wh_back_schedule"), callback_data="wh:list")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def working_hours_time_presets_kb(day: int, lang: str = "ru") -> InlineKeyboardMarkup:
    rows = []
    for idx, (start, end) in enumerate(DAY_TIME_PRESETS):
        label = f"{start:%H:%M}–{end:%H:%M}"
        rows.append([InlineKeyboardButton(text=label, callback_data=f"wh:ds:{day}:{idx}")])
    rows.append([InlineKeyboardButton(text=t(lang, "wh_enter_manual"), callback_data=f"wh:day:manual:{day}")])
    rows.append([InlineKeyboardButton(text=t(lang, "wh_back_schedule"), callback_data=f"wh:day:{day}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def working_hours_presets_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "wh_preset_monfri_9_18"), callback_data="wh:preset:monfri_9_18")],
            [InlineKeyboardButton(text=t(lang, "wh_preset_monfri_10_19"), callback_data="wh:preset:monfri_10_19")],
            [InlineKeyboardButton(text=t(lang, "wh_preset_everyday_10_20"), callback_data="wh:preset:everyday_10_20")],
            [InlineKeyboardButton(text=t(lang, "wh_preset_satsun_off"), callback_data="wh:preset:satsun_off")],
            [InlineKeyboardButton(text=t(lang, "wh_preset_everyday_off"), callback_data="wh:preset:everyday_off")],
            [InlineKeyboardButton(text=t(lang, "wh_back_schedule"), callback_data="wh:list")],
        ]
    )


def working_hours_week_off_confirm_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "wh_week_off_confirm_yes"), callback_data="wh:week_off_confirm")],
            [InlineKeyboardButton(text=t(lang, "wh_week_off_confirm_no"), callback_data="wh:list")],
        ]
    )


def weekday_name(lang: str, day: int) -> str:
    from app.bot.i18n import weekday_name as i18n_weekday

    return i18n_weekday(lang, day)
