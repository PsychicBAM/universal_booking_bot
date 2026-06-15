from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.i18n import t
from app.services.client_data_service import ClientDataSettings


def _toggle_btn(lang: str, enabled: bool, on_key: str, off_key: str, callback: str) -> InlineKeyboardButton:
    label = t(lang, on_key if enabled else off_key)
    return InlineKeyboardButton(text=label, callback_data=callback)


def client_data_settings_kb(settings: ClientDataSettings, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                _toggle_btn(
                    lang,
                    settings.use_telegram_name,
                    "client_data_toggle_use_name_on",
                    "client_data_toggle_use_name_off",
                    "set:cda:toggle:use_name",
                )
            ],
            [
                _toggle_btn(
                    lang,
                    settings.confirm_telegram_name,
                    "client_data_toggle_confirm_name_on",
                    "client_data_toggle_confirm_name_off",
                    "set:cda:toggle:confirm_name",
                )
            ],
            [
                _toggle_btn(
                    lang,
                    settings.phone_request_contact,
                    "client_data_toggle_contact_on",
                    "client_data_toggle_contact_off",
                    "set:cda:toggle:contact",
                )
            ],
            [
                _toggle_btn(
                    lang,
                    settings.phone_manual_input,
                    "client_data_toggle_manual_on",
                    "client_data_toggle_manual_off",
                    "set:cda:toggle:manual",
                )
            ],
            [
                _toggle_btn(
                    lang,
                    settings.phone_required,
                    "client_data_toggle_required_on",
                    "client_data_toggle_required_off",
                    "set:cda:toggle:required",
                )
            ],
            [
                _toggle_btn(
                    lang,
                    settings.fast_reuse_saved_data,
                    "client_data_toggle_fast_on",
                    "client_data_toggle_fast_off",
                    "set:cda:toggle:fast",
                )
            ],
            [InlineKeyboardButton(text=t(lang, "client_data_preview"), callback_data="set:cda:preview")],
            [InlineKeyboardButton(text=t(lang, "settings_back_settings_btn"), callback_data="set:back:main")],
        ]
    )


def client_data_preview_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "settings_back_settings_btn"), callback_data="set:cda:open")],
        ]
    )
