from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.i18n import t


def booking_confirm_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "confirm_booking_btn"), callback_data="confirm:yes")],
            [InlineKeyboardButton(text=t(lang, "booking_edit_details"), callback_data="bkdata:edit:menu")],
            [InlineKeyboardButton(text=t(lang, "booking_back_to_time"), callback_data="bk:back:time")],
            [InlineKeyboardButton(text=t(lang, "cancel"), callback_data="cancel")],
        ]
    )


def booking_edit_menu_kb(
    lang: str,
    *,
    requires_location: bool,
    ask_client_comment: bool,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(text=t(lang, "booking_edit_name"), callback_data="bkdata:edit:name")],
        [InlineKeyboardButton(text=t(lang, "booking_edit_phone"), callback_data="bkdata:edit:phone")],
    ]
    if requires_location:
        rows.append(
            [InlineKeyboardButton(text=t(lang, "booking_edit_address"), callback_data="bkdata:edit:location")]
        )
    if ask_client_comment:
        rows.append(
            [InlineKeyboardButton(text=t(lang, "booking_edit_comment"), callback_data="bkdata:edit:comment")]
        )
    rows.append(
        [InlineKeyboardButton(text=t(lang, "booking_back_to_confirm"), callback_data="bkdata:edit:back")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)
