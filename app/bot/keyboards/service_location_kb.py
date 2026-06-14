from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.i18n import t
from app.models import ServiceLocation


def admin_service_detail_location_row(service_id: int, lang: str = "ru") -> list[InlineKeyboardButton]:
    return [
        InlineKeyboardButton(text=t(lang, "service_locations_btn"), callback_data=f"loc:list:{service_id}")
    ]


def locations_list_kb(service_id: int, locations: list[ServiceLocation], lang: str = "ru") -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(text=t(lang, "add_location"), callback_data=f"loc:add:{service_id}")]
    ]
    for location in locations:
        prefix = "✅ " if location.is_active else "❌ "
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{prefix}{location.title}",
                    callback_data=f"loc:view:{location.id}",
                )
            ]
        )
    rows.append(
        [InlineKeyboardButton(text=t(lang, "back_to_service"), callback_data=f"loc:back:{service_id}")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def location_detail_kb(location_id: int, service_id: int, is_active: bool, lang: str = "ru") -> InlineKeyboardMarkup:
    toggle = t(lang, "hide_location") if is_active else t(lang, "show_location")
    toggle_data = f"loc:hide:{location_id}" if is_active else f"loc:show:{location_id}"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "edit_location_name"), callback_data=f"loc:edit:name:{location_id}")],
            [InlineKeyboardButton(text=t(lang, "edit_location_address"), callback_data=f"loc:edit:addr:{location_id}")],
            [
                InlineKeyboardButton(
                    text=t(lang, "edit_location_description"),
                    callback_data=f"loc:edit:desc:{location_id}",
                )
            ],
            [InlineKeyboardButton(text=toggle, callback_data=toggle_data)],
            [InlineKeyboardButton(text=t(lang, "delete_location"), callback_data=f"loc:del:{location_id}")],
            [InlineKeyboardButton(text=t(lang, "back_to_locations"), callback_data=f"loc:list:{service_id}")],
        ]
    )


def location_delete_confirm_kb(location_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "location_delete_confirm_yes"),
                    callback_data=f"loc:del_confirm:{location_id}",
                )
            ],
            [InlineKeyboardButton(text=t(lang, "location_delete_confirm_no"), callback_data=f"loc:view:{location_id}")],
        ]
    )


def client_locations_kb(locations: list[ServiceLocation], lang: str = "ru") -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=location.title, callback_data=f"cb:loc:{location.id}")]
        for location in locations
    ]
    rows.append([InlineKeyboardButton(text=t(lang, "back"), callback_data="cb:svc_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
