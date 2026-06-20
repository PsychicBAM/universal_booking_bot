from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.i18n import LANG_EN, LANG_RU, t
from app.services.bot_settings_service import BotSettingsSnapshot


def _toggle_label(lang: str, enabled: bool, on_key: str, off_key: str) -> str:
    return t(lang, on_key if enabled else off_key)


def settings_main_kb(
    snapshot: BotSettingsSnapshot,
    lang: str,
    *,
    booking_enabled: bool = True,
    order_enabled: bool = False,
) -> InlineKeyboardMarkup:
    ac_btn = _toggle_label(
        lang,
        snapshot.auto_confirm,
        "settings_auto_confirm_btn_on",
        "settings_auto_confirm_btn_off",
    )
    rows = [
        [InlineKeyboardButton(text=t(lang, "service_modes_settings_button"), callback_data="set:modes:open")],
    ]
    if booking_enabled:
        rows.append([InlineKeyboardButton(text=ac_btn, callback_data="set:ac:toggle")])
        rows.append([InlineKeyboardButton(text=t(lang, "settings_reminders_btn"), callback_data="set:rm:open")])
    rows.append([InlineKeyboardButton(text=t(lang, "settings_enabled_languages_btn"), callback_data="set:enabled:open")])
    if len(snapshot.enabled_languages) > 1:
        rows.append([InlineKeyboardButton(text=t(lang, "settings_language_btn"), callback_data="set:lang:open")])
    rows.extend(
        [
            [InlineKeyboardButton(text=t(lang, "settings_contact_btn"), callback_data="set:contact:open")],
            [InlineKeyboardButton(text=t(lang, "client_data_settings_button"), callback_data="set:cda:open")],
        ]
    )
    if booking_enabled:
        rows.append([InlineKeyboardButton(text=t(lang, "confirm_settings_button"), callback_data="conf:open")])
    rows.extend(
        [
            [InlineKeyboardButton(text=t(lang, "start_screen_btn"), callback_data="set:start:open")],
            [InlineKeyboardButton(text=t(lang, "settings_calendar_btn"), callback_data="set:cal:open")],
            [InlineKeyboardButton(text=t(lang, "settings_advanced_btn"), callback_data="set:adv:open")],
            [InlineKeyboardButton(text=t(lang, "settings_back_admin_btn"), callback_data="set:back:admin")],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def settings_language_kb(lang: str, enabled_languages: list[str] | None = None) -> InlineKeyboardMarkup:
    from app.services.language_service import parse_enabled_languages_value

    codes = parse_enabled_languages_value(",".join(enabled_languages or ["ru", "en"]))
    rows: list[list[InlineKeyboardButton]] = []
    if "ru" in codes:
        rows.append([InlineKeyboardButton(text=LANG_RU, callback_data="set:lang:ru")])
    if "en" in codes:
        rows.append([InlineKeyboardButton(text=LANG_EN, callback_data="set:lang:en")])
    rows.append([InlineKeyboardButton(text=t(lang, "settings_back_settings_btn"), callback_data="set:back:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def settings_enabled_languages_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "enabled_languages_btn_ru"), callback_data="set:enabled:ru")],
            [InlineKeyboardButton(text=t(lang, "enabled_languages_btn_en"), callback_data="set:enabled:en")],
            [InlineKeyboardButton(text=t(lang, "enabled_languages_btn_both"), callback_data="set:enabled:both")],
            [InlineKeyboardButton(text=t(lang, "settings_back_settings_btn"), callback_data="set:back:main")],
        ]
    )


def settings_reminders_kb(snapshot: BotSettingsSnapshot, lang: str) -> InlineKeyboardMarkup:
    rm_toggle = _toggle_label(
        lang,
        snapshot.reminders.enabled,
        "settings_reminders_toggle_on",
        "settings_reminders_toggle_off",
    )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=rm_toggle, callback_data="set:rm:toggle")],
            [InlineKeyboardButton(text=t(lang, "settings_reminder_client1_btn"), callback_data="set:rm:c1")],
            [InlineKeyboardButton(text=t(lang, "settings_reminder_client2_btn"), callback_data="set:rm:c2")],
            [InlineKeyboardButton(text=t(lang, "settings_reminder_admin_btn"), callback_data="set:rm:adm")],
            [InlineKeyboardButton(text=t(lang, "settings_reminder_test_btn"), callback_data="set:rm:test:open")],
            [InlineKeyboardButton(text=t(lang, "settings_back_settings_btn"), callback_data="set:back:main")],
        ]
    )


def _time_preset_row(lang: str, prefix: str, minutes_list: list[int]) -> list[list[InlineKeyboardButton]]:
    rows = []
    row: list[InlineKeyboardButton] = []
    for m in minutes_list:
        row.append(InlineKeyboardButton(text=_minutes_btn_label(lang, m), callback_data=f"{prefix}:{m}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return rows


def _minutes_btn_label(lang: str, minutes: int) -> str:
    return t(lang, f"time_preset_{minutes}")


def reminder_client1_presets_kb(lang: str) -> InlineKeyboardMarkup:
    rows = _time_preset_row(lang, "set:rm:c1", [1440, 720, 360, 180, 60])
    rows.append([InlineKeyboardButton(text=t(lang, "settings_enter_manual_btn"), callback_data="set:rm:c1:manual")])
    rows.append([InlineKeyboardButton(text=t(lang, "settings_back_reminders_btn"), callback_data="set:rm:open")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def reminder_client2_presets_kb(lang: str) -> InlineKeyboardMarkup:
    rows = _time_preset_row(lang, "set:rm:c2", [120, 60, 30, 15])
    rows.append([InlineKeyboardButton(text=t(lang, "settings_enter_manual_btn"), callback_data="set:rm:c2:manual")])
    rows.append([InlineKeyboardButton(text=t(lang, "settings_back_reminders_btn"), callback_data="set:rm:open")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def reminder_admin_presets_kb(lang: str) -> InlineKeyboardMarkup:
    rows = _time_preset_row(lang, "set:rm:adm", [1440, 180, 60, 30, 15])
    rows.append([InlineKeyboardButton(text=t(lang, "settings_enter_manual_btn"), callback_data="set:rm:adm:manual")])
    rows.append([InlineKeyboardButton(text=t(lang, "settings_back_reminders_btn"), callback_data="set:rm:open")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def settings_test_kb(snapshot: BotSettingsSnapshot, lang: str) -> InlineKeyboardMarkup:
    test_toggle = _toggle_label(
        lang,
        snapshot.reminders.test_mode,
        "settings_test_toggle_on",
        "settings_test_toggle_off",
    )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=test_toggle, callback_data="set:rm:test:toggle")],
            [InlineKeyboardButton(text=t(lang, "settings_test_client_section"), callback_data="set:rm:test:cl:menu")],
            [InlineKeyboardButton(text=t(lang, "settings_test_admin_section"), callback_data="set:rm:test:ad:menu")],
            [
                InlineKeyboardButton(
                    text=t(lang, "settings_test_send_nearest_btn"),
                    callback_data="set:rm:test:send_now",
                )
            ],
            [InlineKeyboardButton(text=t(lang, "settings_back_reminders_btn"), callback_data="set:rm:open")],
        ]
    )


def test_client_presets_kb(lang: str) -> InlineKeyboardMarkup:
    rows = _time_preset_row(lang, "set:rm:test:cl", [10, 5, 3, 1])
    rows.append([InlineKeyboardButton(text=t(lang, "settings_back_test_btn"), callback_data="set:rm:test:open")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def test_admin_presets_kb(lang: str) -> InlineKeyboardMarkup:
    rows = _time_preset_row(lang, "set:rm:test:ad", [10, 5, 3, 1])
    rows.append([InlineKeyboardButton(text=t(lang, "settings_back_test_btn"), callback_data="set:rm:test:open")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def settings_contact_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "settings_contact_edit_btn"), callback_data="set:contact:edit")],
            [InlineKeyboardButton(text=t(lang, "settings_contact_clear_btn"), callback_data="set:contact:clear")],
            [InlineKeyboardButton(text=t(lang, "settings_back_settings_btn"), callback_data="set:back:main")],
        ]
    )


def settings_advanced_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "settings_advanced_enter_btn"), callback_data="set:adv:manual")],
            [InlineKeyboardButton(text=t(lang, "settings_advanced_show_keys_btn"), callback_data="set:adv:keys")],
            [InlineKeyboardButton(text=t(lang, "settings_back_settings_btn"), callback_data="set:back:main")],
        ]
    )


def settings_advanced_keys_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "settings_back_advanced_btn"), callback_data="set:adv:open")],
        ]
    )


def settings_calendar_kb(lang: str, env_on: bool, db_on: bool) -> InlineKeyboardMarkup:
    if env_on:
        toggle = _toggle_label(
            lang,
            db_on,
            "settings_calendar_toggle_on",
            "settings_calendar_toggle_off",
        )
        toggle_data = "set:cal:toggle"
    else:
        toggle = t(lang, "settings_calendar_toggle_env_off")
        toggle_data = "set:cal:noop"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=toggle, callback_data=toggle_data)],
            [InlineKeyboardButton(text=t(lang, "settings_calendar_test_btn"), callback_data="set:cal:test")],
            [InlineKeyboardButton(text=t(lang, "settings_back_settings_btn"), callback_data="set:back:main")],
        ]
    )

