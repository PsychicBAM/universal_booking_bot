from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from app.bot.i18n import LANG_EN, LANG_RU, all_texts, status_label, t, weekday_name
from app.bot.keyboards.booking_time_kb import dates_kb
from app.bot.keyboards.service_media_kb import admin_service_detail_media_rows
from app.bot.keyboards.service_location_kb import admin_service_detail_location_row
from app.models import Booking, Service
from app.services.language_service import get_enabled_languages_sync, is_language_switching_enabled, parse_enabled_languages_value
from app.utils.datetime_utils import slot_to_callback
from app.utils.formatting import format_date, format_time


def main_menu(
    is_admin: bool = False,
    lang: str = "ru",
    *,
    booking_enabled: bool = True,
    order_enabled: bool = False,
) -> ReplyKeyboardMarkup:
    rows: list[list[KeyboardButton]] = []
    compact = booking_enabled and order_enabled
    if compact:
        rows.append([KeyboardButton(text=t(lang, "main_menu_services"))])
        rows.append([KeyboardButton(text=t(lang, "main_menu_my_activity"))])
    else:
        if booking_enabled:
            rows.append([KeyboardButton(text=t(lang, "book_appointment"))])
        if order_enabled:
            rows.append([KeyboardButton(text=t(lang, "order_services_button"))])
        if booking_enabled:
            rows.append([KeyboardButton(text=t(lang, "my_bookings"))])
        if order_enabled:
            rows.append([KeyboardButton(text=t(lang, "my_orders_button"))])
    rows.append([KeyboardButton(text=t(lang, "contact_admin"))])
    if is_language_switching_enabled():
        rows.append([KeyboardButton(text=t(lang, "language"))])
    if is_admin:
        rows.append([KeyboardButton(text=t(lang, "admin_menu"))])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def admin_menu(
    lang: str = "ru",
    *,
    booking_enabled: bool = True,
    order_enabled: bool = False,
) -> ReplyKeyboardMarkup:
    rows: list[list[KeyboardButton]] = []
    if booking_enabled and order_enabled:
        rows.append(
            [
                KeyboardButton(text=t(lang, "admin_services")),
                KeyboardButton(text=t(lang, "schedule_button")),
            ]
        )
        rows.append(
            [
                KeyboardButton(text=t(lang, "admin_bookings")),
                KeyboardButton(text=t(lang, "orders_admin_button")),
            ]
        )
        rows.append(
            [
                KeyboardButton(text=t(lang, "admin_clients_button")),
                KeyboardButton(text=t(lang, "admin_settings")),
            ]
        )
        if is_language_switching_enabled():
            rows.append([KeyboardButton(text=t(lang, "language"))])
    elif booking_enabled:
        rows.append(
            [
                KeyboardButton(text=t(lang, "admin_services")),
                KeyboardButton(text=t(lang, "schedule_button")),
            ]
        )
        rows.append(
            [
                KeyboardButton(text=t(lang, "admin_bookings")),
                KeyboardButton(text=t(lang, "admin_clients_button")),
            ]
        )
        settings_row = [KeyboardButton(text=t(lang, "admin_settings"))]
        if is_language_switching_enabled():
            settings_row.append(KeyboardButton(text=t(lang, "language")))
        rows.append(settings_row)
    elif order_enabled:
        rows.append(
            [
                KeyboardButton(text=t(lang, "admin_services")),
                KeyboardButton(text=t(lang, "orders_admin_button")),
            ]
        )
        rows.append(
            [
                KeyboardButton(text=t(lang, "admin_clients_button")),
                KeyboardButton(text=t(lang, "admin_settings")),
            ]
        )
        if is_language_switching_enabled():
            rows.append([KeyboardButton(text=t(lang, "language"))])
    else:
        rows.append([KeyboardButton(text=t(lang, "admin_services"))])
        rows.append([KeyboardButton(text=t(lang, "admin_settings"))])
    rows.append([KeyboardButton(text=t(lang, "back_main"))])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


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


def services_kb(
    services: list[Service],
    lang: str = "ru",
    *,
    show_type_icons: bool = False,
) -> InlineKeyboardMarkup:
    from app.models import SERVICE_TYPE_ORDER

    buttons = []
    for s in services:
        if show_type_icons:
            icon = "📝" if s.service_type == SERVICE_TYPE_ORDER else "📅"
            label = f"{icon} {s.name}"
        else:
            label = s.name
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"svc:{s.id}")])
    buttons.append([InlineKeyboardButton(text=t(lang, "cancel"), callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def my_activity_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "my_activity_bookings"), callback_data="myact:bookings")],
            [InlineKeyboardButton(text=t(lang, "my_activity_orders"), callback_data="myact:orders")],
            [InlineKeyboardButton(text=t(lang, "back_main"), callback_data="myact:back")],
        ]
    )


def times_kb(slots: list, lang: str = "ru", prefix: str = "time") -> InlineKeyboardMarkup:
    """Legacy alias — uses compact 3-column time grid."""
    from app.bot.keyboards.booking_time_kb import time_grid_kb
    from app.utils.datetime_utils import slot_to_callback

    return time_grid_kb(slots, lang, time_cb=lambda slot: f"{prefix}:{slot_to_callback(slot)}")


def confirm_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t(lang, "confirm_btn"), callback_data="confirm:yes"),
                InlineKeyboardButton(text=t(lang, "cancel"), callback_data="cancel"),
            ]
        ]
    )


def bookings_kb(
    bookings: list[Booking],
    lang: str = "ru",
    service_names: dict[int, str] | None = None,
    *,
    back_callback: str = "my:back:main",
    back_label_key: str = "back_main",
) -> InlineKeyboardMarkup:
    from app.bot.utils.booking_labels import format_client_booking_button

    names = service_names or {}
    buttons = [
        [
            InlineKeyboardButton(
                text=format_client_booking_button(
                    b,
                    lang,
                    service_name=names.get(b.service_id),
                ),
                callback_data=f"my:view:{b.id}",
            )
        ]
        for b in bookings
    ]
    if not buttons:
        buttons = [[InlineKeyboardButton(text="—", callback_data="noop")]]
    buttons.append(
        [InlineKeyboardButton(text=t(lang, back_label_key), callback_data=back_callback)]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def my_bookings_back_kb(
    lang: str = "ru",
    *,
    from_activity_hub: bool = False,
) -> InlineKeyboardMarkup:
    if from_activity_hub:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=t(lang, "back_to_my_activity"), callback_data="myact:hub")]
            ]
        )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "back_main"), callback_data="my:back:main")]
        ]
    )


def booking_actions_kb(booking_id: int, can_cancel: bool = True, lang: str = "ru") -> InlineKeyboardMarkup:
    rows = []
    if can_cancel:
        rows.append([InlineKeyboardButton(text=t(lang, "cancel_booking_btn"), callback_data=f"cancel_booking:{booking_id}")])
    rows.append([InlineKeyboardButton(text=t(lang, "back_main"), callback_data="my_bookings")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_services_hub_kb(
    *,
    active_count: int,
    disabled_count: int,
    archived_count: int,
    lang: str = "ru",
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "add_service"), callback_data="adm_svc:add")],
            [
                InlineKeyboardButton(
                    text=t(lang, "services_folder_active", count=str(active_count)),
                    callback_data="svc:active",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "services_folder_disabled", count=str(disabled_count)),
                    callback_data="svc:disabled",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "services_folder_archive", count=str(archived_count)),
                    callback_data="svc:archive",
                )
            ],
            [InlineKeyboardButton(text=t(lang, "services_search_button"), callback_data="svc:search")],
            [InlineKeyboardButton(text=t(lang, "back_to_admin_panel"), callback_data="svc:back")],
        ]
    )


def _service_type_prefix(service: Service) -> str:
    from app.models import SERVICE_TYPE_ORDER

    return "📝" if service.service_type == SERVICE_TYPE_ORDER else "📅"


def admin_active_services_grouped_kb(services: list[Service], lang: str = "ru") -> InlineKeyboardMarkup:
    from app.models import SERVICE_TYPE_ORDER

    booking_services = sorted(
        [s for s in services if s.service_type != SERVICE_TYPE_ORDER],
        key=lambda s: s.name.lower(),
    )
    order_services = sorted(
        [s for s in services if s.service_type == SERVICE_TYPE_ORDER],
        key=lambda s: s.name.lower(),
    )
    buttons: list[list[InlineKeyboardButton]] = []
    for service in booking_services:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"{_service_type_prefix(service)} {service.name}",
                    callback_data=f"adm_svc:{service.id}",
                )
            ]
        )
    for service in order_services:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"{_service_type_prefix(service)} {service.name}",
                    callback_data=f"adm_svc:{service.id}",
                )
            ]
        )
    buttons.append([InlineKeyboardButton(text=t(lang, "back_to_services"), callback_data="svc:hub")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_active_services_kb(services: list[Service], lang: str = "ru") -> InlineKeyboardMarkup:
    return admin_active_services_grouped_kb(services, lang)


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
    buttons.append([InlineKeyboardButton(text=t(lang, "back_to_services"), callback_data="svc:hub")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_archived_services_kb(services: list[Service], lang: str = "ru") -> InlineKeyboardMarkup:
    buttons = []
    for s in services:
        buttons.append(
            [InlineKeyboardButton(text=f"📦 {s.name}", callback_data=f"svc:arch:view:{s.id}")]
        )
    if not buttons:
        buttons = [[InlineKeyboardButton(text=t(lang, "archive_empty"), callback_data="noop")]]
    buttons.append([InlineKeyboardButton(text=t(lang, "back_to_services"), callback_data="svc:hub")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_service_search_results_kb(services: list[Service], lang: str = "ru") -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=f"{_service_type_prefix(s)} {s.name}",
                callback_data=f"adm_svc:{s.id}",
            )
        ]
        for s in services
    ]
    if not buttons:
        buttons = [[InlineKeyboardButton(text=t(lang, "services_search_no_results"), callback_data="noop")]]
    buttons.append([InlineKeyboardButton(text=t(lang, "back_to_services"), callback_data="svc:hub")])
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
    show_type_change: bool = False,
    is_order_type: bool = False,
) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=t(lang, "edit_name"), callback_data=f"adm_svc_edit:name:{service_id}")],
        [InlineKeyboardButton(text=t(lang, "edit_description"), callback_data=f"adm_svc_edit:desc:{service_id}")],
    ]
    if show_type_change:
        rows.append(
            [InlineKeyboardButton(text=t(lang, "service_type_change"), callback_data=f"svc:chtype:menu:{service_id}")]
        )
    if not is_order_type:
        rows.extend(
            [
                [InlineKeyboardButton(text=t(lang, "edit_duration"), callback_data=f"adm_svc_edit:dur:{service_id}")],
                [InlineKeyboardButton(text=t(lang, "edit_buffer"), callback_data=f"adm_svc_edit:buf:{service_id}")],
                [InlineKeyboardButton(text=t(lang, "toggle_location_request"), callback_data=f"adm_svc_loc:{service_id}")],
                [InlineKeyboardButton(text=t(lang, "client_comment_toggle"), callback_data=f"adm_svc_comment:{service_id}")],
                admin_service_detail_location_row(service_id, lang),
            ]
        )
    rows.append([InlineKeyboardButton(text=t(lang, "edit_price"), callback_data=f"adm_svc:price:menu:{service_id}")])
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


def days_kb(lang: str = "ru", prefix: str = "wh_day") -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=weekday_name(lang, i, short=True), callback_data=f"{prefix}:{i}")]
        for i in range(7)
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


BOOK_APPOINTMENT_TEXTS = all_texts("book_appointment")
MAIN_MENU_SERVICES_TEXTS = all_texts("main_menu_services")
MAIN_MENU_MY_ACTIVITY_TEXTS = all_texts("main_menu_my_activity")
ORDER_SERVICES_TEXTS = all_texts("order_services_button")
MY_BOOKINGS_TEXTS = all_texts("my_bookings")
MY_ORDERS_TEXTS = all_texts("my_orders_button")
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
ADMIN_ORDERS_TEXTS = all_texts("orders_admin_button")
ADMIN_CLIENTS_TEXTS = all_texts("admin_clients_button")
ADMIN_SCHEDULE_TEXTS = all_texts("schedule_button")
ADMIN_CALENDAR_TEXTS = all_texts("admin_calendar")
ADMIN_SETTINGS_TEXTS = all_texts("admin_settings")
SKIP_TEXTS = all_texts("skip")

_MENU_TEXT_KEYS = (
    "book_appointment",
    "main_menu_services",
    "main_menu_my_activity",
    "order_services_button",
    "my_bookings",
    "my_orders_button",
    "contact_admin",
    "language",
    "admin_menu",
    "back_main",
    "admin_services",
    "schedule_button",
    "admin_bookings",
    "orders_admin_button",
    "admin_clients_button",
    "admin_settings",
)
ALL_MENU_TEXTS: frozenset[str] = frozenset(
    text for key in _MENU_TEXT_KEYS for text in all_texts(key)
) | ADMIN_WH_TEXTS | ADMIN_UNAVAILABLE_TEXTS | ADMIN_WH_LEGACY_TEXTS | ADMIN_UNAVAILABLE_LEGACY_TEXTS
