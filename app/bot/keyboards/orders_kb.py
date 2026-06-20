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


def admin_order_detail_kb(order_id: int, status: str, section: str, page: int, lang: str) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if status == ServiceOrderStatus.NEW.value:
        rows.append(
            [InlineKeyboardButton(text=t(lang, "order_mark_in_progress"), callback_data=f"ord:status:in_progress:{order_id}")]
        )
    if status in (ServiceOrderStatus.NEW.value, ServiceOrderStatus.IN_PROGRESS.value):
        rows.append(
            [InlineKeyboardButton(text=t(lang, "order_mark_completed"), callback_data=f"ord:status:completed:{order_id}")]
        )
    if status in (ServiceOrderStatus.NEW.value, ServiceOrderStatus.IN_PROGRESS.value):
        rows.append(
            [InlineKeyboardButton(text=t(lang, "order_cancel"), callback_data=f"ord:status:cancelled:{order_id}")]
        )
    rows.extend(
        [
            [InlineKeyboardButton(text=t(lang, "message_client_btn"), callback_data=f"ord:msg:{order_id}")],
            [InlineKeyboardButton(text=t(lang, "order_admin_note_btn"), callback_data=f"ord:note:{order_id}")],
            [
                InlineKeyboardButton(
                    text=t(lang, "back"),
                    callback_data=f"ord:folder:{section}:{page}",
                )
            ],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_new_order_kb(order_id: int, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "order_open_btn"), callback_data=f"ord:view:{order_id}:new:0")],
            [InlineKeyboardButton(text=t(lang, "message_client_btn"), callback_data=f"ord:msg:{order_id}")],
            [
                InlineKeyboardButton(
                    text=t(lang, "order_mark_in_progress"),
                    callback_data=f"ord:status:in_progress:{order_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "order_mark_completed"),
                    callback_data=f"ord:status:completed:{order_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "order_cancel"),
                    callback_data=f"ord:status:cancelled:{order_id}",
                )
            ],
        ]
    )


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


def client_order_detail_kb(order_id: int, status: str, lang: str) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if status in (ServiceOrderStatus.NEW.value, ServiceOrderStatus.IN_PROGRESS.value):
        rows.append(
            [InlineKeyboardButton(text=t(lang, "order_cancel_client"), callback_data=f"myord:cancel:{order_id}")]
        )
    rows.append([InlineKeyboardButton(text=t(lang, "back_main"), callback_data="myord:list")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
