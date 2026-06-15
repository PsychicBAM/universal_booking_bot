from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.i18n import t


def schedule_main_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "schedule_configure_wh"),
                    callback_data="wh:list",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "schedule_block_dates"),
                    callback_data="unav:main",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "schedule_quick_actions"),
                    callback_data="sch:quick",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "schedule_closures_list"),
                    callback_data="unav:items",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "schedule_back_admin"),
                    callback_data="sch:back",
                )
            ],
        ]
    )


def schedule_quick_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "wh_quick_presets"), callback_data="wh:presets")],
            [InlineKeyboardButton(text=t(lang, "unav_tomorrow"), callback_data="unav:tomorrow")],
            [InlineKeyboardButton(text=t(lang, "unav_next7"), callback_data="unav:next7")],
            [InlineKeyboardButton(text=t(lang, "wh_week_off"), callback_data="wh:week_off")],
            [InlineKeyboardButton(text=t(lang, "wh_back_schedule"), callback_data="sch:main")],
        ]
    )
