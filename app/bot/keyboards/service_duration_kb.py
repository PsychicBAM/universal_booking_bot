from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.i18n import format_duration, t

SERVICE_DURATION_PRESETS = (15, 45, 60, 90, 120, 180)


def service_duration_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=format_duration(lang, minutes), callback_data=f"svc:dur:{minutes}")]
        for minutes in SERVICE_DURATION_PRESETS
    ]
    rows.append([InlineKeyboardButton(text=t(lang, "svc_duration_manual"), callback_data="svc:dur:manual")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
