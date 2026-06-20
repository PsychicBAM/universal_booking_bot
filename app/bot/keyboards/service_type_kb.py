from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.i18n import t
from app.models import SERVICE_TYPE_BOOKING, SERVICE_TYPE_ORDER, ServiceOrder


def service_type_choose_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "service_type_booking_btn"),
                    callback_data=f"svc:type:{SERVICE_TYPE_BOOKING}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "service_type_order_btn"),
                    callback_data=f"svc:type:{SERVICE_TYPE_ORDER}",
                )
            ],
        ]
    )


def service_type_change_kb(service_id: int, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "service_type_booking_btn"),
                    callback_data=f"svc:chtype:{SERVICE_TYPE_BOOKING}:{service_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "service_type_order_btn"),
                    callback_data=f"svc:chtype:{SERVICE_TYPE_ORDER}:{service_id}",
                )
            ],
            [InlineKeyboardButton(text=t(lang, "back"), callback_data=f"adm_svc:{service_id}")],
        ]
    )
