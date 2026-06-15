from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from app.bot.i18n import LANG_EN, LANG_RU, all_texts, status_label, t, weekday_name
from app.bot.utils.attendance_helpers import attendance_list_indicator
from app.bot.keyboards.service_media_kb import admin_service_detail_media_rows
from app.bot.keyboards.service_location_kb import admin_service_detail_location_row
from app.models import Booking, Service
from app.services.language_service import get_enabled_languages_sync, is_language_switching_enabled, parse_enabled_languages_value
from app.utils.datetime_utils import slot_to_callback
from app.utils.formatting import format_date, format_time


def main_menu(is_admin: bool = False, lang: str = "ru") -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=t(lang, "book_appointment"))],
        [KeyboardButton(text=t(lang, "my_bookings"))],
        [KeyboardButton(text=t(lang, "contact_admin"))],
    ]
    if is_language_switching_enabled():
        rows.append([KeyboardButton(text=t(lang, "language"))])
    if is_admin:
        rows.append([KeyboardButton(text=t(lang, "admin_menu"))])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def admin_menu(lang: str = "ru") -> ReplyKeyboardMarkup:
    bottom_row = [KeyboardButton(text=t(lang, "back_main"))]
    if is_language_switching_enabled():
        bottom_row.insert(0, KeyboardButton(text=t(lang, "language")))
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=t(lang, "admin_services")),
                KeyboardButton(text=t(lang, "admin_working_hours")),
            ],
            [
                KeyboardButton(text=t(lang, "admin_unavailable")),
                KeyboardButton(text=t(lang, "admin_bookings")),
            ],
            [
                KeyboardButton(text=t(lang, "admin_calendar")),
                KeyboardButton(text=t(lang, "admin_settings")),
            ],
            bottom_row,
        ],
        resize_keyboard=True,
    )


def cancel_kb(lang: str = "ru") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t(lang, "cancel"))]],
        resize_keyboard=True,
    )


def skip_cancel_kb(lang: str = "ru") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t(lang, "skip"))],
            [KeyboardButton(text=t(lang, "cancel"))],
        ],
        resize_keyboard=True,
    )


def language_kb(enabled: list[str] | None = None) -> InlineKeyboardMarkup:
    codes = parse_enabled_languages_value(",".join(enabled or get_enabled_languages_sync()))
    rows: list[list[InlineKeyboardButton]] = []
    if "ru" in codes:
        rows.append([InlineKeyboardButton(text=LANG_RU, callback_data="lang:ru")])
    if "en" in codes:
        rows.append([InlineKeyboardButton(text=LANG_EN, callback_data="lang:en")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def services_kb(services: list[Service], lang: str = "ru") -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=s.name, callback_data=f"svc:{s.id}")]
        for s in services
    ]
    buttons.append([InlineKeyboardButton(text=t(lang, "cancel"), callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def dates_kb(dates: list, lang: str = "ru", prefix: str = "date") -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=format_date(d), callback_data=f"{prefix}:{d.isoformat()}")]
        for d in dates[:14]
    ]
    buttons.append([InlineKeyboardButton(text=t(lang, "cancel"), callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def times_kb(slots: list, lang: str = "ru", prefix: str = "time") -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=format_time(s), callback_data=f"{prefix}:{slot_to_callback(s)}")]
        for s in slots
    ]
    buttons.append([InlineKeyboardButton(text=t(lang, "cancel"), callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def confirm_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t(lang, "confirm_btn"), callback_data="confirm:yes"),
                InlineKeyboardButton(text=t(lang, "cancel"), callback_data="cancel"),
            ]
        ]
    )


def bookings_kb(bookings: list[Booking]) -> InlineKeyboardMarkup:
    buttons = []
    for b in bookings:
        buttons.append(
            [InlineKeyboardButton(text=format_time(b.start_at) + f" #{b.id}", callback_data=f"my:view:{b.id}")]
        )
    if not buttons:
        buttons = [[InlineKeyboardButton(text="—", callback_data="noop")]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def booking_actions_kb(booking_id: int, can_cancel: bool = True, lang: str = "ru") -> InlineKeyboardMarkup:
    rows = []
    if can_cancel:
        rows.append([InlineKeyboardButton(text=t(lang, "cancel_booking_btn"), callback_data=f"cancel_booking:{booking_id}")])
    rows.append([InlineKeyboardButton(text=t(lang, "back_main"), callback_data="my_bookings")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_active_services_kb(services: list[Service], lang: str = "ru") -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(text=t(lang, "add_service"), callback_data="adm_svc:add")]]
    for s in services:
        buttons.append(
            [InlineKeyboardButton(text=f"✅ {s.name}", callback_data=f"adm_svc:{s.id}")]
        )
    buttons.append(
        [InlineKeyboardButton(text=t(lang, "services_disabled_button"), callback_data="svc:disabled")]
    )
    buttons.append([InlineKeyboardButton(text=t(lang, "archived_services"), callback_data="svc:archive")])
    buttons.append([InlineKeyboardButton(text=t(lang, "back_to_admin_panel"), callback_data="svc:back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_disabled_services_kb(services: list[Service], lang: str = "ru") -> InlineKeyboardMarkup:
    buttons = []
    for s in services:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"🔴 {s.name}",
                    callback_data=f"svc:disabled:view:{s.id}",
                )
            ]
        )
    buttons.append([InlineKeyboardButton(text=t(lang, "back_to_services"), callback_data="svc:list")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_archived_services_kb(services: list[Service], lang: str = "ru") -> InlineKeyboardMarkup:
    buttons = []
    for s in services:
        buttons.append(
            [InlineKeyboardButton(text=f"📦 {s.name}", callback_data=f"svc:arch:view:{s.id}")]
        )
    if not buttons:
        buttons = [[InlineKeyboardButton(text=t(lang, "archive_empty"), callback_data="noop")]]
    buttons.append([InlineKeyboardButton(text=t(lang, "back_to_services"), callback_data="svc:list")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def archived_service_detail_kb(service_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "restore_service"), callback_data=f"svc:arch:restore:{service_id}")],
            [InlineKeyboardButton(text=t(lang, "delete_permanently"), callback_data=f"svc:arch:delete:{service_id}")],
            [InlineKeyboardButton(text=t(lang, "back_to_archive"), callback_data="svc:archive")],
        ]
    )


def permanent_delete_confirm_kb(service_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "delete_permanently_confirm_yes"), callback_data=f"svc:arch:delete_confirm:{service_id}")],
            [InlineKeyboardButton(text=t(lang, "delete_permanently_confirm_no"), callback_data=f"svc:arch:view:{service_id}")],
        ]
    )


def admin_services_kb(services: list[Service], lang: str = "ru") -> InlineKeyboardMarkup:
    """Backward-compatible alias for active services keyboard."""
    return admin_active_services_kb(services, lang)


def admin_service_delete_confirm_kb(service_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "service_delete_confirm_yes"), callback_data=f"adm_svc_del_yes:{service_id}")],
            [InlineKeyboardButton(text=t(lang, "service_delete_confirm_no"), callback_data=f"adm_svc_del_no:{service_id}")],
        ]
    )


def admin_service_detail_kb(
    service_id: int,
    is_active: bool,
    lang: str = "ru",
    *,
    archived: bool = False,
    show_media_to_clients: bool = True,
    detail_source: str = "active",
) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=t(lang, "edit_name"), callback_data=f"adm_svc_edit:name:{service_id}")],
        [InlineKeyboardButton(text=t(lang, "edit_description"), callback_data=f"adm_svc_edit:desc:{service_id}")],
        [InlineKeyboardButton(text=t(lang, "edit_duration"), callback_data=f"adm_svc_edit:dur:{service_id}")],
        [InlineKeyboardButton(text=t(lang, "edit_buffer"), callback_data=f"adm_svc_edit:buf:{service_id}")],
        [InlineKeyboardButton(text=t(lang, "toggle_location_request"), callback_data=f"adm_svc_loc:{service_id}")],
        [InlineKeyboardButton(text=t(lang, "client_comment_toggle"), callback_data=f"adm_svc_comment:{service_id}")],
        admin_service_detail_location_row(service_id, lang),
        [InlineKeyboardButton(text=t(lang, "edit_price"), callback_data=f"adm_svc_edit:price:{service_id}")],
    ]
    rows.extend(admin_service_detail_media_rows(service_id, show_media_to_clients, lang))
    if not archived:
        if is_active:
            rows.append(
                [InlineKeyboardButton(text=t(lang, "disable_service"), callback_data=f"svc:disable:{service_id}")]
            )
        else:
            rows.append(
                [InlineKeyboardButton(text=t(lang, "enable_service"), callback_data=f"svc:enable:{service_id}")]
            )
            rows.append(
                [
                    InlineKeyboardButton(
                        text=t(lang, "move_to_archive"),
                        callback_data=f"svc:move_arch:{service_id}",
                    )
                ]
            )
        rows.append(
            [InlineKeyboardButton(text=t(lang, "delete_service"), callback_data=f"adm_svc_del:{service_id}")]
        )
    if detail_source == "disabled":
        back_label = t(lang, "back_to_disabled_services")
        back_data = "svc:disabled"
    else:
        back_label = t(lang, "back_to_services")
        back_data = "svc:list"
    rows.append([InlineKeyboardButton(text=back_label, callback_data=back_data)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_bookings_kb(bookings: list[Booking], lang: str = "ru") -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=t(lang, "admin_attendance_button"), callback_data="adm_att:list:7d:0")]
    ]
    for b in bookings[:20]:
        status = status_label(lang, b.status.value)
        indicator = attendance_list_indicator(b)
        buttons.append(
            [InlineKeyboardButton(
                text=f"{indicator}#{b.id} {format_time(b.start_at)} [{status}]",
                callback_data=f"adm_booking:{b.id}",
            )]
        )
    if not buttons:
        buttons = [[InlineKeyboardButton(text=t(lang, "no_bookings_admin"), callback_data="noop")]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_booking_detail_kb(booking_id: int, status: str, lang: str = "ru") -> InlineKeyboardMarkup:
    rows = []
    if status == "pending":
        rows.append([InlineKeyboardButton(text=t(lang, "confirm_booking_btn"), callback_data=f"adm_confirm:{booking_id}")])
    if status in ("pending", "confirmed"):
        rows.append([InlineKeyboardButton(text=t(lang, "cancel_booking_btn"), callback_data=f"adm_cancel:{booking_id}")])
        rows.append([InlineKeyboardButton(text=t(lang, "message_client_btn"), callback_data=f"adm_msg:{booking_id}")])
        rows.append(
            [
                InlineKeyboardButton(
                    text=t(lang, "admin_attendance_send_question"),
                    callback_data=f"adm_att:view:{booking_id}:adm",
                )
            ]
        )
    rows.append([InlineKeyboardButton(text=t(lang, "back"), callback_data="adm_bookings:list")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def days_kb(lang: str = "ru", prefix: str = "wh_day") -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=weekday_name(lang, i, short=True), callback_data=f"{prefix}:{i}")]
        for i in range(7)
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


BOOK_APPOINTMENT_TEXTS = all_texts("book_appointment")
MY_BOOKINGS_TEXTS = all_texts("my_bookings")
CONTACT_ADMIN_TEXTS = all_texts("contact_admin")
LANGUAGE_TEXTS = all_texts("language")
ADMIN_MENU_TEXTS = all_texts("admin_menu")
BACK_MAIN_TEXTS = all_texts("back_main")
ADMIN_SERVICES_TEXTS = all_texts("admin_services")
ADMIN_WH_LEGACY_TEXTS = frozenset(
    {
        "🕒 Рабочее время",
        "🕒 Working hours",
        "Рабочее время",
        "Working hours",
    }
)
ADMIN_WH_TEXTS = all_texts("admin_working_hours") | ADMIN_WH_LEGACY_TEXTS
ADMIN_UNAVAILABLE_LEGACY_TEXTS = frozenset(
    {
        "Недоступные даты",
        "Unavailable dates",
    }
)
ADMIN_UNAVAILABLE_TEXTS = all_texts("admin_unavailable") | ADMIN_UNAVAILABLE_LEGACY_TEXTS
ADMIN_BOOKINGS_TEXTS = all_texts("admin_bookings")
ADMIN_CALENDAR_TEXTS = all_texts("admin_calendar")
ADMIN_SETTINGS_TEXTS = all_texts("admin_settings")
SKIP_TEXTS = all_texts("skip")

_MENU_TEXT_KEYS = (
    "book_appointment",
    "my_bookings",
    "contact_admin",
    "language",
    "admin_menu",
    "back_main",
    "admin_services",
    "admin_working_hours",
    "admin_unavailable",
    "admin_bookings",
    "admin_calendar",
    "admin_settings",
)
ALL_MENU_TEXTS: frozenset[str] = frozenset(
    text for key in _MENU_TEXT_KEYS for text in all_texts(key)
) | ADMIN_WH_LEGACY_TEXTS | ADMIN_UNAVAILABLE_LEGACY_TEXTS
