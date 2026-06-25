from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.i18n import t
from app.models import ServiceOrder, ServiceOrderStatus


def order_confirm_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "order_submit"), callback_data="ord:confirm:yes")],
            [InlineKeyboardButton(text=t(lang, "order_edit_data"), callback_data="ord:confirm:edit")],
            [InlineKeyboardButton(text=t(lang, "cancel"), callback_data="cancel")],
        ]
    )


def admin_orders_hub_kb(counts: dict[str, int], lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "orders_folder_new", count=str(counts.get("new", 0))),
                    callback_data="ord:folder:new:0",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "orders_folder_in_progress", count=str(counts.get("in_progress", 0))),
                    callback_data="ord:folder:in_progress:0",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "orders_folder_completed", count=str(counts.get("completed", 0))),
                    callback_data="ord:folder:completed:0",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "orders_folder_cancelled", count=str(counts.get("cancelled", 0))),
                    callback_data="ord:folder:cancelled:0",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "orders_folder_declined", count=str(counts.get("declined", 0))),
                    callback_data="ord:folder:declined:0",
                )
            ],
            [InlineKeyboardButton(text=t(lang, "back_to_admin_panel"), callback_data="ord:back:admin")],
        ]
    )


def admin_orders_folder_kb(
    orders: list[ServiceOrder],
    section: str,
    page: int,
    total_pages: int,
    lang: str,
) -> InlineKeyboardMarkup:
    from app.bot.utils.order_labels import format_admin_order_button

    rows = [
        [InlineKeyboardButton(text=format_admin_order_button(o, lang), callback_data=f"ord:view:{o.id}:{section}:{page}")]
        for o in orders
    ]
    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀️", callback_data=f"ord:folder:{section}:{page - 1}"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text="▶️", callback_data=f"ord:folder:{section}:{page + 1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton(text=t(lang, "orders_back_hub"), callback_data="ord:hub")])
    return InlineKeyboardMarkup(inline_keyboard=rows or [[InlineKeyboardButton(text="—", callback_data="noop")]])


def _order_back_button(section: str, page: int, lang: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=t(lang, "back"), callback_data=f"ord:folder:{section}:{page}")


def admin_order_detail_kb(order_id: int, status: str, section: str, page: int, lang: str) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if status == ServiceOrderStatus.NEW.value:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t(lang, "order_accept_button"),
                    callback_data=f"ord:accept:{order_id}",
                )
            ]
        )
        rows.append(
            [
                InlineKeyboardButton(
                    text=t(lang, "order_decline_button"),
                    callback_data=f"ord:decline:{order_id}",
                )
            ]
        )
        rows.append(
            [InlineKeyboardButton(text=t(lang, "message_client_btn"), callback_data=f"ord:msg:{order_id}")]
        )
        rows.append(
            [InlineKeyboardButton(text=t(lang, "order_admin_note_btn"), callback_data=f"ord:note:{order_id}")]
        )
    elif status == ServiceOrderStatus.ACCEPTED.value:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t(lang, "order_mark_in_progress"),
                    callback_data=f"ord:status:in_progress:{order_id}",
                )
            ]
        )
        rows.append(
            [
                InlineKeyboardButton(
                    text=t(lang, "order_mark_completed"),
                    callback_data=f"ord:status:completed:{order_id}",
                )
            ]
        )
        rows.append(
            [InlineKeyboardButton(text=t(lang, "order_cancel"), callback_data=f"ord:status:cancelled:{order_id}")]
        )
        rows.extend(_accepted_active_rows(order_id, lang))
    elif status == ServiceOrderStatus.IN_PROGRESS.value:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t(lang, "order_mark_completed"),
                    callback_data=f"ord:status:completed:{order_id}",
                )
            ]
        )
        rows.append(
            [InlineKeyboardButton(text=t(lang, "order_cancel"), callback_data=f"ord:status:cancelled:{order_id}")]
        )
        rows.extend(_accepted_active_rows(order_id, lang))
    else:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t(lang, "order_message_history_button"),
                    callback_data=f"ord:history:{order_id}:{section}:{page}",
                )
            ]
        )
        rows.append(
            [InlineKeyboardButton(text=t(lang, "message_client_btn"), callback_data=f"ord:msg:{order_id}")]
        )
    rows.append([_order_back_button(section, page, lang)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _accepted_active_rows(order_id: int, lang: str) -> list[list[InlineKeyboardButton]]:
    return [
        [InlineKeyboardButton(text=t(lang, "message_client_btn"), callback_data=f"ord:msg:{order_id}")],
        [
            InlineKeyboardButton(
                text=t(lang, "order_message_history_button"),
                callback_data=f"ord:history:{order_id}:in_progress:0",
            )
        ],
        [InlineKeyboardButton(text=t(lang, "order_admin_note_btn"), callback_data=f"ord:note:{order_id}")],
    ]


def admin_new_order_kb(order_id: int, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "order_accept_button"),
                    callback_data=f"ord:accept:{order_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "order_decline_button"),
                    callback_data=f"ord:decline:{order_id}",
                )
            ],
            [InlineKeyboardButton(text=t(lang, "order_open_btn"), callback_data=f"ord:view:{order_id}:new:0")],
            [InlineKeyboardButton(text=t(lang, "message_client_btn"), callback_data=f"ord:msg:{order_id}")],
        ]
    )


def order_message_notify_admin_kb(order_id: int, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "order_open_btn"), callback_data=f"ord:view:{order_id}:new:0")],
            [InlineKeyboardButton(text=t(lang, "order_reply_button"), callback_data=f"ord:msg:{order_id}")],
        ]
    )


def order_message_notify_client_kb(order_id: int, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "order_open_btn"), callback_data=f"myord:view:{order_id}")],
            [InlineKeyboardButton(text=t(lang, "order_reply_button"), callback_data=f"myord:msg:{order_id}")],
        ]
    )


def order_history_kb(order_id: int, section: str, page: int, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "order_full_info_button"),
                    callback_data=f"ord:view:{order_id}:{section}:{page}",
                )
            ],
            [InlineKeyboardButton(text=t(lang, "back"), callback_data=f"ord:view:{order_id}:{section}:{page}")],
        ]
    )


def client_order_history_kb(order_id: int, section: str, lang: str) -> InlineKeyboardMarkup:
    back_cb = f"myord:view:{order_id}:{section}" if section in ("active", "history") else f"myord:view:{order_id}"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "back"), callback_data=back_cb)],
        ]
    )


def client_orders_hub_kb(counts, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "my_orders_active_button", count=str(counts.active_count)),
                    callback_data="myord:active",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "my_orders_history_button", count=str(counts.history_count)),
                    callback_data="myord:history",
                )
            ],
            [InlineKeyboardButton(text=t(lang, "back_main"), callback_data="myord:back")],
        ]
    )


def client_orders_empty_active_kb(counts, lang: str) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if counts.history_count > 0:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t(lang, "my_orders_history_button", count=str(counts.history_count)),
                    callback_data="myord:history",
                )
            ]
        )
    rows.append([InlineKeyboardButton(text=t(lang, "my_orders_back_to_hub"), callback_data="myord:hub")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def client_orders_empty_history_kb(counts, lang: str) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if counts.active_count > 0:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t(lang, "my_orders_active_button", count=str(counts.active_count)),
                    callback_data="myord:active",
                )
            ]
        )
    rows.append([InlineKeyboardButton(text=t(lang, "my_orders_back_to_hub"), callback_data="myord:hub")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def client_orders_active_kb(
    orders: list[ServiceOrder],
    lang: str,
    *,
    service_names: dict[int, str] | None = None,
) -> InlineKeyboardMarkup:
    from app.bot.utils.order_labels import format_client_order_button

    service_names = service_names or {}
    rows = [
        [
            InlineKeyboardButton(
                text=format_client_order_button(
                    order,
                    lang,
                    service_name=service_names.get(order.service_id),
                ),
                callback_data=f"myord:view:{order.id}:active",
            )
        ]
        for order in orders
    ]
    rows.append([InlineKeyboardButton(text=t(lang, "my_orders_back_to_hub"), callback_data="myord:hub")])
    return InlineKeyboardMarkup(inline_keyboard=rows or [[InlineKeyboardButton(text="—", callback_data="noop")]])


def client_orders_history_kb(
    orders: list[ServiceOrder],
    lang: str,
    *,
    service_names: dict[int, str] | None = None,
) -> InlineKeyboardMarkup:
    from app.bot.utils.order_labels import format_client_order_button

    service_names = service_names or {}
    rows = [
        [
            InlineKeyboardButton(
                text=format_client_order_button(
                    order,
                    lang,
                    service_name=service_names.get(order.service_id),
                ),
                callback_data=f"myord:view:{order.id}:history",
            )
        ]
        for order in orders
    ]
    rows.append([InlineKeyboardButton(text=t(lang, "my_orders_back_to_hub"), callback_data="myord:hub")])
    return InlineKeyboardMarkup(inline_keyboard=rows or [[InlineKeyboardButton(text="—", callback_data="noop")]])


def client_orders_kb(orders: list[ServiceOrder], lang: str) -> InlineKeyboardMarkup:
    from app.bot.utils.order_labels import format_client_order_button

    rows = [
        [InlineKeyboardButton(text=format_client_order_button(o, lang), callback_data=f"myord:view:{o.id}")]
        for o in orders
    ]
    if not rows:
        rows = [[InlineKeyboardButton(text="—", callback_data="noop")]]
    rows.append([InlineKeyboardButton(text=t(lang, "back_main"), callback_data="myord:back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def client_order_detail_kb(order_id: int, status: str, lang: str, *, section: str = "hub") -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    active_statuses = (
        ServiceOrderStatus.NEW.value,
        ServiceOrderStatus.ACCEPTED.value,
        ServiceOrderStatus.IN_PROGRESS.value,
    )
    rows.append(
        [InlineKeyboardButton(text=t(lang, "order_write_to_order_button"), callback_data=f"myord:msg:{order_id}")]
    )
    rows.append(
        [
            InlineKeyboardButton(
                text=t(lang, "order_message_history_button"),
                callback_data=f"myord:history:{order_id}:{section}",
            )
        ]
    )
    if status in active_statuses:
        rows.append(
            [InlineKeyboardButton(text=t(lang, "order_cancel_client"), callback_data=f"myord:cancel:{order_id}:{section}")]
        )
    if section == "active":
        back_cb = "myord:active"
    elif section == "history":
        back_cb = "myord:history"
    else:
        back_cb = "myord:hub"
    rows.append([InlineKeyboardButton(text=t(lang, "back"), callback_data=back_cb)])
    return InlineKeyboardMarkup(inline_keyboard=rows)
