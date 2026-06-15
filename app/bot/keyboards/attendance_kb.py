from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.i18n import t
from app.services.confirmation_text_service import ConfirmationTextConfig, resolve_confirmation_text


def attendance_yes_no_kb(
    booking_id: int,
    lang: str,
    config: ConfirmationTextConfig,
) -> InlineKeyboardMarkup:
    from app.services.confirmation_text_service import build_booking_confirmation_keyboard

    return build_booking_confirmation_keyboard(booking_id, lang, config)


def attendance_action_kb(booking_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "attendance_reschedule_button"),
                    callback_data=f"att:res:{booking_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "attendance_cancel_button"),
                    callback_data=f"att:cancel:{booking_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "attendance_reason_button"),
                    callback_data=f"att:reason:{booking_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "attendance_keep_button"),
                    callback_data=f"att:keep:{booking_id}",
                )
            ],
        ]
    )


def attendance_action_prompt_text(lang: str, config: ConfirmationTextConfig) -> str:
    return resolve_confirmation_text(config, lang, "no_action_prompt")
