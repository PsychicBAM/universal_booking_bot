from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.i18n import LANG_EN, LANG_RU, t
from app.services.language_service import parse_enabled_languages_value


def lang_codes(enabled_languages: list[str] | None) -> list[str]:
    return parse_enabled_languages_value(",".join(enabled_languages or ["ru", "en"]))


def confirmation_settings_main_kb(
    admin_lang: str,
    target_lang: str,
    *,
    multi_lang: bool,
) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=t(admin_lang, "confirm_group_main_text"),
                callback_data=f"conf:group:main:{target_lang}",
            )
        ],
        [
            InlineKeyboardButton(
                text=t(admin_lang, "confirm_group_responses"),
                callback_data=f"conf:group:responses:{target_lang}",
            )
        ],
        [
            InlineKeyboardButton(
                text=t(admin_lang, "confirm_preview_btn"),
                callback_data=f"conf:preview:{target_lang}",
            )
        ],
        [
            InlineKeyboardButton(
                text=t(admin_lang, "confirm_reset_btn"),
                callback_data=f"conf:reset:ask:{target_lang}",
            )
        ],
    ]
    if multi_lang:
        rows.append(
            [InlineKeyboardButton(text=t(admin_lang, "confirm_back"), callback_data="conf:back")]
        )
    else:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t(admin_lang, "settings_back_settings_btn"),
                    callback_data="set:back:main",
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirmation_language_select_kb(admin_lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=LANG_RU, callback_data="conf:lang:ru")],
            [InlineKeyboardButton(text=LANG_EN, callback_data="conf:lang:en")],
            [
                InlineKeyboardButton(
                    text=t(admin_lang, "confirm_preview_ru"),
                    callback_data="conf:preview:ru",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(admin_lang, "confirm_preview_en"),
                    callback_data="conf:preview:en",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(admin_lang, "settings_back_settings_btn"),
                    callback_data="set:back:main",
                )
            ],
        ]
    )


def confirmation_main_text_kb(target_lang: str, admin_lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(admin_lang, "confirm_edit_title_plain"),
                    callback_data=f"conf:edit:title:{target_lang}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(admin_lang, "confirm_edit_question_plain"),
                    callback_data=f"conf:edit:question:{target_lang}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(admin_lang, "confirm_edit_confirm_button"),
                    callback_data=f"conf:edit:yes_button:{target_lang}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(admin_lang, "confirm_edit_change_button"),
                    callback_data=f"conf:edit:no_button:{target_lang}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(admin_lang, "confirm_back_to_confirmation"),
                    callback_data=f"conf:back:lang:{target_lang}",
                )
            ],
        ]
    )


def confirmation_responses_kb(target_lang: str, admin_lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(admin_lang, "confirm_edit_client_confirm_response"),
                    callback_data=f"conf:edit:yes_response:{target_lang}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(admin_lang, "confirm_edit_client_change_prompt"),
                    callback_data=f"conf:edit:no_action_prompt:{target_lang}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(admin_lang, "confirm_edit_admin_confirm_notice"),
                    callback_data=f"conf:edit:yes_admin:{target_lang}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(admin_lang, "confirm_edit_admin_change_notice"),
                    callback_data=f"conf:edit:no_admin:{target_lang}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(admin_lang, "confirm_back_to_confirmation"),
                    callback_data=f"conf:back:lang:{target_lang}",
                )
            ],
        ]
    )


def confirmation_reset_confirm_kb(target_lang: str, admin_lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(admin_lang, "confirm_reset_yes"),
                    callback_data=f"conf:reset:yes:{target_lang}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(admin_lang, "confirm_reset_no"),
                    callback_data=f"conf:reset:no:{target_lang}",
                )
            ],
        ]
    )
