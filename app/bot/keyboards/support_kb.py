from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.i18n import t
from app.models import Booking, SupportMessage, SupportMessageStatus
from app.utils.formatting import format_datetime


def _topic_label(lang: str, topic: str | None) -> str:
    topics = {"booking", "reschedule", "cancel", "payment", "other"}
    if topic in topics:
        return t(lang, f"support_topic_{topic}")
    return t(lang, "support_topic_other")


def _status_label(lang: str, status: SupportMessageStatus) -> str:
    if status == SupportMessageStatus.OPEN:
        return t(lang, "support_status_open")
    if status == SupportMessageStatus.REPLIED:
        return t(lang, "support_status_replied")
    return t(lang, "support_status_closed")


def format_request_list_label(request: SupportMessage, lang: str) -> str:
    return f"#{request.id} [{_status_label(lang, request.status)}] {_topic_label(lang, request.topic)}"


def _topic_rows(lang: str) -> list[list[InlineKeyboardButton]]:
    return [
        [InlineKeyboardButton(text=t(lang, "support_topic_booking"), callback_data="sup:topic:booking")],
        [
            InlineKeyboardButton(
                text=t(lang, "support_topic_reschedule"), callback_data="sup:topic:reschedule"
            ),
            InlineKeyboardButton(
                text=t(lang, "support_topic_cancel"), callback_data="sup:topic:cancel"
            ),
        ],
        [
            InlineKeyboardButton(
                text=t(lang, "support_topic_payment"), callback_data="sup:topic:payment"
            ),
            InlineKeyboardButton(text=t(lang, "support_topic_other"), callback_data="sup:topic:other"),
        ],
    ]


def support_main_menu_kb(lang: str) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text=t(lang, "support_new_request"), callback_data="sup:new"),
            InlineKeyboardButton(text=t(lang, "support_my_requests"), callback_data="sup:my"),
        ],
        *_topic_rows(lang),
        [InlineKeyboardButton(text=t(lang, "support_back_to_menu"), callback_data="sup:back:main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def support_new_topics_kb(lang: str) -> InlineKeyboardMarkup:
    rows = [
        *_topic_rows(lang),
        [InlineKeyboardButton(text=t(lang, "support_back_btn"), callback_data="sup:back:menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def support_booking_pick_kb(bookings: list[Booking], lang: str) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"#{booking.id} {format_datetime(booking.start_at)}",
                callback_data=f"sup:book:{booking.id}",
            )
        ]
        for booking in bookings
    ]
    rows.append(
        [InlineKeyboardButton(text=t(lang, "support_skip_booking"), callback_data="sup:book:skip")]
    )
    rows.append([InlineKeyboardButton(text=t(lang, "support_back_btn"), callback_data="sup:back:topic")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def support_message_nav_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t(lang, "support_back_btn"), callback_data="sup:back:prompt"),
                InlineKeyboardButton(text=t(lang, "cancel"), callback_data="cancel"),
            ],
        ]
    )


def support_requests_list_kb(requests: list[SupportMessage], lang: str) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=format_request_list_label(request, lang),
                callback_data=f"sup:req:{request.id}",
            )
        ]
        for request in requests
    ]
    rows.append([InlineKeyboardButton(text=t(lang, "support_back_btn"), callback_data="sup:back:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def support_request_detail_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "support_new_request"), callback_data="sup:new")],
            [
                InlineKeyboardButton(
                    text=t(lang, "support_back_to_requests"), callback_data="sup:back:my"
                )
            ],
        ]
    )


def support_admin_kb(message_id: int, client_username: str | None, lang: str) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(text=t(lang, "support_reply_button"), callback_data=f"sup:reply:{message_id}")],
    ]
    if client_username:
        username = client_username.lstrip("@")
        rows.append(
            [
                InlineKeyboardButton(
                    text=t(lang, "support_open_profile_button"),
                    url=f"https://t.me/{username}",
                )
            ]
        )
    rows.append(
        [InlineKeyboardButton(text=t(lang, "support_close_button"), callback_data=f"sup:close:{message_id}")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)
