from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.i18n import t
from app.services.admin_bookings_service import BookingDetailSource, build_booking_view_callback

DEFAULT_FILTER = "all"


def _list_cb(filter_key: str, page: int) -> str:
    return f"adm_cli:list:{filter_key}:{page}"


def _view_cb(client_id: int, filter_key: str, page: int) -> str:
    return f"adm_cli:view:{client_id}:{filter_key}:{page}"


def _section_cb(section: str, client_id: int, filter_key: str, page: int, section_page: int = 0) -> str:
    return f"adm_cli:{section}:{client_id}:{filter_key}:{page}:{section_page}"


def admin_clients_main_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "clients_all_button"),
                    callback_data=_list_cb(DEFAULT_FILTER, 0),
                )
            ],
            [InlineKeyboardButton(text=t(lang, "clients_search_button"), callback_data="adm_cli:search")],
            [InlineKeyboardButton(text=t(lang, "clients_back_admin"), callback_data="adm_cli:admin_back")],
        ]
    )


def admin_clients_list_kb(
    clients: list,
    filter_key: str,
    page: int,
    total_pages: int,
    lang: str = "ru",
) -> InlineKeyboardMarkup:
    from app.services.client_history_service import format_client_list_label

    rows: list[list[InlineKeyboardButton]] = []
    for stats in clients:
        rows.append(
            [
                InlineKeyboardButton(
                    text=format_client_list_label(stats, lang),
                    callback_data=_view_cb(stats.client_id, filter_key, page),
                )
            ]
        )
    if total_pages > 1:
        nav: list[InlineKeyboardButton] = []
        if page > 0:
            nav.append(
                InlineKeyboardButton(
                    text=t(lang, "pagination_prev"),
                    callback_data=_list_cb(filter_key, page - 1),
                )
            )
        if page < total_pages - 1:
            nav.append(
                InlineKeyboardButton(
                    text=t(lang, "pagination_next"),
                    callback_data=_list_cb(filter_key, page + 1),
                )
            )
        if nav:
            rows.append(nav)
    rows.append([InlineKeyboardButton(text=t(lang, "clients_back_admin"), callback_data="adm_cli:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_client_detail_kb(
    client_id: int,
    filter_key: str,
    page: int,
    *,
    username: str | None = None,
    lang: str = "ru",
) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=t(lang, "client_future_bookings"),
                callback_data=_section_cb("future", client_id, filter_key, page, 0),
            )
        ],
        [
            InlineKeyboardButton(
                text=t(lang, "client_booking_history"),
                callback_data=_section_cb("hist", client_id, filter_key, page, 0),
            )
        ],
        [
            InlineKeyboardButton(
                text=t(lang, "client_message_button"),
                callback_data=f"adm_cli:msg:{client_id}:{filter_key}:{page}",
            )
        ],
        [
            InlineKeyboardButton(
                text=t(lang, "client_send_confirmation_nearest"),
                callback_data=f"adm_cli:confirm:{client_id}:{filter_key}:{page}",
            )
        ],
    ]
    if username:
        rows.insert(
            0,
            [
                InlineKeyboardButton(
                    text=t(lang, "client_open_telegram_profile"),
                    url=f"https://t.me/{username.lstrip('@')}",
                )
            ],
        )
    rows.append(
        [
            InlineKeyboardButton(
                text=t(lang, "clients_back_list"),
                callback_data=_list_cb(filter_key, page),
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_client_bookings_kb(
    booking_labels: list[tuple[int, str]],
    client_id: int,
    filter_key: str,
    page: int,
    section: str,
    section_page: int,
    total_pages: int,
    lang: str = "ru",
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for booking_id, label in booking_labels:
        rows.append(
            [
                InlineKeyboardButton(
                    text=label,
                    callback_data=build_booking_view_callback(
                        booking_id,
                        BookingDetailSource(
                            origin="client",
                            client_id=client_id,
                            client_tab=section,
                            client_filter=filter_key,
                            page=page,
                            client_section_page=section_page,
                        ),
                    ),
                )
            ]
        )
    if total_pages > 1:
        nav: list[InlineKeyboardButton] = []
        if section_page > 0:
            nav.append(
                InlineKeyboardButton(
                    text=t(lang, "pagination_prev"),
                    callback_data=_section_cb(section, client_id, filter_key, page, section_page - 1),
                )
            )
        if section_page < total_pages - 1:
            nav.append(
                InlineKeyboardButton(
                    text=t(lang, "pagination_next"),
                    callback_data=_section_cb(section, client_id, filter_key, page, section_page + 1),
                )
            )
        if nav:
            rows.append(nav)
    rows.append(
        [
            InlineKeyboardButton(
                text=t(lang, "clients_back_list"),
                callback_data=_view_cb(client_id, filter_key, page),
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_clients_search_results_kb(
    clients: list,
    lang: str = "ru",
) -> InlineKeyboardMarkup:
    from app.services.client_history_service import format_client_list_label

    rows: list[list[InlineKeyboardButton]] = []
    for stats in clients[:20]:
        rows.append(
            [
                InlineKeyboardButton(
                    text=format_client_list_label(stats, lang),
                    callback_data=_view_cb(stats.client_id, DEFAULT_FILTER, 0),
                )
            ]
        )
    rows.append([InlineKeyboardButton(text=t(lang, "clients_back_admin"), callback_data="adm_cli:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
