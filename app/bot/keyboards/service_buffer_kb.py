from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.i18n import format_buffer, t

SERVICE_BUFFER_PRESETS = (0, 10, 15, 30, 45, 60, 90, 120)


def service_buffer_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=format_buffer(lang, minutes), callback_data=f"svc:buf:{minutes}")]
        for minutes in SERVICE_BUFFER_PRESETS
    ]
    rows.append([InlineKeyboardButton(text=t(lang, "svc_buffer_manual"), callback_data="svc:buf:manual")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
