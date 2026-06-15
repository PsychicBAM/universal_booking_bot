from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.i18n import t
from app.services.language_service import parse_enabled_languages_value
from app.services.start_screen_service import StartScreenConfig


def _toggle_ru_label(lang: str, enabled: bool) -> str:
    return t(lang, "start_screen_toggle_ru_on" if enabled else "start_screen_toggle_ru_off")


def _toggle_en_label(lang: str, enabled: bool) -> str:
    return t(lang, "start_screen_toggle_en_on" if enabled else "start_screen_toggle_en_off")


def _toggle_single_label(lang: str, enabled: bool) -> str:
    return t(lang, "start_screen_toggle_photo_on" if enabled else "start_screen_toggle_photo_off")


def _ru_rows(config: StartScreenConfig, lang: str, *, generic_labels: bool) -> list[list[InlineKeyboardButton]]:
    edit_btn = t(lang, "start_screen_edit_text_btn" if generic_labels else "start_screen_edit_ru_btn")
    upload_btn = t(lang, "start_screen_upload_photo_btn" if generic_labels else "start_screen_upload_ru_btn")
    preview_btn = t(lang, "start_screen_preview_btn" if generic_labels else "start_screen_preview_ru_btn")
    toggle_label = (
        _toggle_single_label(lang, config.start_photo_enabled_ru)
        if generic_labels
        else _toggle_ru_label(lang, config.start_photo_enabled_ru)
    )
    return [
        [InlineKeyboardButton(text=edit_btn, callback_data="set:start:edit:ru")],
        [InlineKeyboardButton(text=upload_btn, callback_data="set:start:photo:ru")],
        [InlineKeyboardButton(text=toggle_label, callback_data="set:start:toggle_photo:ru")],
        [InlineKeyboardButton(text=preview_btn, callback_data="set:start:preview:ru")],
    ]


def _en_rows(config: StartScreenConfig, lang: str, *, generic_labels: bool) -> list[list[InlineKeyboardButton]]:
    edit_btn = t(lang, "start_screen_edit_text_btn" if generic_labels else "start_screen_edit_en_btn")
    upload_btn = t(lang, "start_screen_upload_photo_btn" if generic_labels else "start_screen_upload_en_btn")
    preview_btn = t(lang, "start_screen_preview_btn" if generic_labels else "start_screen_preview_en_btn")
    toggle_label = (
        _toggle_single_label(lang, config.start_photo_enabled_en)
        if generic_labels
        else _toggle_en_label(lang, config.start_photo_enabled_en)
    )
    return [
        [InlineKeyboardButton(text=edit_btn, callback_data="set:start:edit:en")],
        [InlineKeyboardButton(text=upload_btn, callback_data="set:start:photo:en")],
        [InlineKeyboardButton(text=toggle_label, callback_data="set:start:toggle_photo:en")],
        [InlineKeyboardButton(text=preview_btn, callback_data="set:start:preview:en")],
    ]


def start_screen_menu_kb(
    config: StartScreenConfig,
    lang: str,
    enabled_languages: list[str] | None = None,
) -> InlineKeyboardMarkup:
    codes = parse_enabled_languages_value(",".join(enabled_languages or ["ru", "en"]))
    single = len(codes) == 1
    rows: list[list[InlineKeyboardButton]] = []
    if "ru" in codes:
        rows.extend(_ru_rows(config, lang, generic_labels=single and codes == ["ru"]))
    if "en" in codes:
        rows.extend(_en_rows(config, lang, generic_labels=single and codes == ["en"]))
    rows.append([InlineKeyboardButton(text=t(lang, "start_screen_reset_btn"), callback_data="set:start:reset")])
    rows.append(
        [InlineKeyboardButton(text=t(lang, "start_screen_back_settings_btn"), callback_data="set:back:main")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def start_screen_reset_confirm_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "start_screen_reset_yes"), callback_data="set:start:reset:yes")],
            [InlineKeyboardButton(text=t(lang, "start_screen_reset_no"), callback_data="set:start:open")],
        ]
    )
