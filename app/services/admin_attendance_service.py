from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.i18n import t
from app.bot.utils.attendance_helpers import (
    ATTENDANCE_CANNOT_ATTEND,
    ATTENDANCE_CONFIRMED,
    ATTENDANCE_REASON_PROVIDED,
    has_attendance_response,
)
from app.bot.utils.booking_labels import format_admin_booking_button
from app.models import Booking, Client
from app.repositories import BookingRepository
from app.services.confirmation_text_service import (
    build_booking_confirmation_keyboard,
    build_booking_confirmation_message,
    load_confirmation_text_config,
)
from app.services.language_service import resolve_client_lang_for_client
from app.utils.datetime_utils import now_local, to_local_naive
from app.utils.formatting import format_datetime

ATTENDANCE_PAGE_SIZE = 10
DEFAULT_ATTENDANCE_FILTER = "7d"
VALID_FILTERS = frozenset({"today", "tomorrow", "7d", "all", "noresp"})


def normalize_attendance_filter(filter_key: str) -> str:
    key = (filter_key or DEFAULT_ATTENDANCE_FILTER).strip().lower()
    return key if key in VALID_FILTERS else DEFAULT_ATTENDANCE_FILTER


def filter_upcoming_for_attendance(bookings: list[Booking], filter_key: str, today: date) -> list[Booking]:
    key = normalize_attendance_filter(filter_key)
    tomorrow = today + timedelta(days=1)
    week_end = today + timedelta(days=7)
    filtered: list[Booking] = []
    for booking in bookings:
        start = to_local_naive(booking.start_at)
        if start < now_local():
            continue
        booking_date = start.date()
        if key == "today" and booking_date != today:
            continue
        if key == "tomorrow" and booking_date != tomorrow:
            continue
        if key == "7d" and booking_date > week_end:
            continue
        if key == "noresp" and has_attendance_response(booking):
            continue
        filtered.append(booking)
    return filtered


def paginate_bookings(bookings: list[Booking], page: int, per_page: int = ATTENDANCE_PAGE_SIZE) -> tuple[list[Booking], int, int]:
    total = len(bookings)
    total_pages = max(1, (total + per_page - 1) // per_page) if total else 1
    page = max(0, min(page, total_pages - 1))
    start = page * per_page
    return bookings[start : start + per_page], page, total_pages


def _urgency_bucket(booking_date: date, today: date) -> str:
    if booking_date == today:
        return "today"
    if booking_date == today + timedelta(days=1):
        return "tomorrow"
    if booking_date <= today + timedelta(days=7):
        return "week"
    return "later"


def build_attendance_list_body(bookings: list[Booking], lang: str, filter_key: str) -> str:
    lines = [t(lang, "admin_attendance_title"), ""]
    if not bookings:
        lines.append(t(lang, "admin_attendance_no_bookings"))
        return "\n".join(lines)

    today = now_local().date()
    buckets: dict[str, list[Booking]] = {"today": [], "tomorrow": [], "week": [], "later": []}
    for booking in bookings:
        buckets[_urgency_bucket(to_local_naive(booking.start_at).date(), today)].append(booking)

    section_keys = ("today", "tomorrow", "week", "later")
    if filter_key == "today":
        section_keys = ("today",)
    elif filter_key == "tomorrow":
        section_keys = ("tomorrow",)

    section_titles = {
        "today": t(lang, "admin_attendance_section_today"),
        "tomorrow": t(lang, "admin_attendance_section_tomorrow"),
        "week": t(lang, "admin_attendance_section_week"),
        "later": t(lang, "admin_attendance_section_later"),
    }
    for key in section_keys:
        items = buckets[key]
        if not items:
            continue
        lines.append(section_titles[key])
        for booking in items:
            lines.append(format_admin_booking_button(booking, lang))
        lines.append("")
    return "\n".join(lines).strip()


def format_attendance_response_admin(booking: Booking, lang: str) -> str:
    if not has_attendance_response(booking):
        return t(lang, "admin_attendance_no_response")
    if booking.attendance_status == ATTENDANCE_CONFIRMED:
        return t(lang, "admin_attendance_client_response_confirmed")
    if booking.attendance_status == ATTENDANCE_REASON_PROVIDED:
        return t(lang, "admin_attendance_client_response_reason")
    return t(lang, "admin_attendance_client_response_cannot")


def format_admin_attendance_detail(
    booking: Booking,
    service_name: str,
    lang: str,
) -> str:
    lines = [
        t(lang, "admin_attendance_title"),
        "",
        t(lang, "booking_id_label", id=str(booking.id)),
        t(lang, "admin_attendance_client_line", client_name=booking.client_name),
        t(lang, "admin_attendance_phone_line", phone=booking.client_phone or t(lang, "phone_not_provided")),
        t(lang, "admin_attendance_service_line", service=service_name),
        t(lang, "admin_attendance_datetime_line", date_time=format_datetime(booking.start_at)),
        t(
            lang,
            "admin_attendance_client_response",
            response=format_attendance_response_admin(booking, lang),
        ),
    ]
    if booking.attendance_reason:
        lines.append(t(lang, "admin_attendance_reason_line", reason=booking.attendance_reason))
    if booking.attendance_manual_sent_count:
        lines.append(
            t(
                lang,
                "admin_attendance_manual_info",
                count=str(booking.attendance_manual_sent_count),
            )
        )
    return "\n".join(lines)


def format_attendance_question_text(
    booking: Booking,
    service_name: str,
    date_time: str,
    lang: str,
    config,
    *,
    manual: bool = False,
) -> str:
    return build_booking_confirmation_message(
        booking,
        service_name,
        date_time,
        lang,
        config,
        manual=manual,
        include_prompt=True,
    )


async def send_attendance_question_to_client(
    bot: Bot,
    session: AsyncSession,
    booking: Booking,
    client: Client,
    service_name: str,
    *,
    manual: bool = False,
) -> bool:
    config = await load_confirmation_text_config(session)
    client_lang = await resolve_client_lang_for_client(client)
    date_time = format_datetime(booking.start_at)
    text = format_attendance_question_text(
        booking,
        service_name,
        date_time,
        client_lang,
        config,
        manual=manual,
    )
    keyboard = build_booking_confirmation_keyboard(booking.id, client_lang, config)
    try:
        await bot.send_message(client.telegram_id, text, reply_markup=keyboard)
        return True
    except Exception:
        return False


def mark_manual_attendance_sent(booking: Booking, admin_telegram_id: int) -> None:
    booking.attendance_manual_sent_at = datetime.now(timezone.utc)
    booking.attendance_manual_sent_by_admin_id = admin_telegram_id
    booking.attendance_manual_sent_count = int(booking.attendance_manual_sent_count or 0) + 1


async def load_attendance_list(
    session: AsyncSession,
    filter_key: str,
    page: int,
) -> tuple[list[Booking], list[Booking], int, int]:
    filter_key = normalize_attendance_filter(filter_key)
    all_bookings = await BookingRepository(session).list_upcoming_active()
    filtered = filter_upcoming_for_attendance(all_bookings, filter_key, now_local().date())
    page_items, page, total_pages = paginate_bookings(filtered, page)
    return page_items, filtered, page, total_pages
