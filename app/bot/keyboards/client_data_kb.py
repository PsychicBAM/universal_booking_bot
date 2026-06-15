from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from app.bot.i18n import t


def confirm_telegram_name_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "booking_use_telegram_name_yes"),
                    callback_data="bkdata:name:yes",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "booking_enter_other_name"),
                    callback_data="bkdata:name:manual",
                )
            ],
        ]
    )


def saved_phone_kb(
    lang: str,
    *,
    request_contact_enabled: bool,
    manual_enabled: bool,
    phone_required: bool,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(
                text=t(lang, "booking_use_saved_phone"),
                callback_data="bkdata:phone:saved_yes",
            )
        ],
    ]
    if request_contact_enabled:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t(lang, "booking_share_phone"),
                    callback_data="bkdata:phone:contact",
                )
            ]
        )
    if manual_enabled:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t(lang, "booking_enter_phone_manual"),
                    callback_data="bkdata:phone:manual",
                )
            ]
        )
    if not phone_required:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t(lang, "booking_skip_phone"),
                    callback_data="bkdata:phone:skip",
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def phone_method_inline_kb(
    lang: str,
    *,
    request_contact_enabled: bool,
    manual_enabled: bool,
    phone_required: bool,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if request_contact_enabled:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t(lang, "booking_share_phone"),
                    callback_data="bkdata:phone:contact",
                )
            ]
        )
    if manual_enabled:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t(lang, "booking_enter_phone_manual"),
                    callback_data="bkdata:phone:manual",
                )
            ]
        )
    if not phone_required:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t(lang, "booking_skip_phone"),
                    callback_data="bkdata:phone:skip",
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def request_contact_reply_kb(
    lang: str,
    *,
    manual_enabled: bool,
    phone_required: bool,
) -> ReplyKeyboardMarkup:
    rows: list[list[KeyboardButton]] = [
        [KeyboardButton(text=t(lang, "booking_share_phone_button"), request_contact=True)],
    ]
    if manual_enabled:
        rows.append([KeyboardButton(text=t(lang, "booking_enter_phone_manual"))])
    if not phone_required:
        rows.append([KeyboardButton(text=t(lang, "booking_skip_phone"))])
    rows.append([KeyboardButton(text=t(lang, "cancel"))])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)
