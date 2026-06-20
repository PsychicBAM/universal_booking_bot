from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.i18n import t


def admin_service_detail_media_rows(
    service_id: int, show_media_to_clients: bool, lang: str = "ru"
) -> list[list[InlineKeyboardButton]]:
    show_btn = t(lang, "hide_from_clients") if show_media_to_clients else t(lang, "show_to_clients")
    return [
        [InlineKeyboardButton(text=t(lang, "service_media"), callback_data=f"sm:menu:{service_id}")],
        [InlineKeyboardButton(text=show_btn, callback_data=f"sm:show:{service_id}")],
    ]


def service_media_menu_kb(service_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "add_photo"), callback_data=f"sm:add:ph:{service_id}")],
            [InlineKeyboardButton(text=t(lang, "add_video"), callback_data=f"sm:add:vd:{service_id}")],
            [InlineKeyboardButton(text=t(lang, "choose_cover"), callback_data=f"sm:cover:{service_id}")],
            [InlineKeyboardButton(text=t(lang, "delete_media"), callback_data=f"sm:del:{service_id}")],
            [InlineKeyboardButton(text=t(lang, "preview_media"), callback_data=f"sm:preview:{service_id}")],
            [InlineKeyboardButton(text=t(lang, "back"), callback_data=f"sm:back:{service_id}")],
        ]
    )


def service_media_cover_kb(service_id: int, photo_ids: list[tuple[int, int]], lang: str = "ru") -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=t(lang, "media_photo_n", n=str(n)), callback_data=f"sm:cover:set:{media_id}")]
        for n, media_id in photo_ids
    ]
    rows.append([InlineKeyboardButton(text=t(lang, "back"), callback_data=f"sm:menu:{service_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def service_media_delete_kb(service_id: int, items: list[tuple[str, int, int]], lang: str = "ru") -> InlineKeyboardMarkup:
    rows = []
    for label_key, n, media_id in items:
        label = t(lang, label_key, n=str(n))
        rows.append([InlineKeyboardButton(text=f"🗑 {label}", callback_data=f"sm:del:go:{media_id}")])
    rows.append([InlineKeyboardButton(text=t(lang, "back"), callback_data=f"sm:menu:{service_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def client_service_card_kb(
    service_id: int,
    lang: str = "ru",
    *,
    has_photos: bool = False,
    has_video: bool = False,
    service_type: str = "booking",
) -> InlineKeyboardMarkup:
    from app.models import SERVICE_TYPE_ORDER

    if service_type == SERVICE_TYPE_ORDER:
        action_btn = InlineKeyboardButton(text=t(lang, "order_button"), callback_data=f"cb:order:{service_id}")
    else:
        action_btn = InlineKeyboardButton(text=t(lang, "book_appointment"), callback_data=f"cb:book:{service_id}")
    rows = [[action_btn]]
    if has_photos:
        rows.append([InlineKeyboardButton(text=t(lang, "view_photos"), callback_data=f"cb:photos:{service_id}")])
    if has_video:
        rows.append([InlineKeyboardButton(text=t(lang, "view_video"), callback_data=f"cb:video:{service_id}")])
    rows.append([InlineKeyboardButton(text=t(lang, "back"), callback_data="cb:svc_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
