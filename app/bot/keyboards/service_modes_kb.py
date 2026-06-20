from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.i18n import t
from app.services.service_modes_service import ServiceModes


def service_modes_kb(modes: ServiceModes, lang: str) -> InlineKeyboardMarkup:
    booking_btn = (
        t(lang, "service_mode_booking_on")
        if modes.booking_enabled
        else t(lang, "service_mode_booking_off")
    )
    order_btn = (
        t(lang, "service_mode_order_on")
        if modes.order_enabled
        else t(lang, "service_mode_order_off")
    )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=booking_btn, callback_data="set:modes:booking:toggle")],
            [InlineKeyboardButton(text=order_btn, callback_data="set:modes:order:toggle")],
            [InlineKeyboardButton(text=t(lang, "settings_back_settings_btn"), callback_data="set:back:main")],
        ]
    )
