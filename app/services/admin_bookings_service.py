from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.i18n import t
from app.bot.utils.attendance_helpers import (
    ATTENDANCE_CANNOT_ATTEND,
    ATTENDANCE_CONFIRMED,
    ATTENDANCE_REASON_PROVIDED,
    has_attendance_response,
)
from app.bot.utils.booking_labels import format_admin_booking_button
from app.models import Booking, BookingStatus
from app.repositories import BookingRepository
from app.utils.datetime_utils import now_local, to_local_naive

BOOKINGS_PAGE_SIZE = 10
BOOKINGS_SECTIONS = frozenset(
    {"upcoming", "waiting", "confirmed", "needs_change", "history", "cancelled"}
)
DEFAULT_BOOKINGS_SECTION = "upcoming"

_FOLDER_INTRO_KEYS = {
    "waiting": "bookings_folder_waiting_intro",
    "confirmed": "bookings_folder_confirmed_intro",
    "needs_change": "bookings_folder_needs_change_intro",
}


@dataclass
class BookingsHubCounts:
    upcoming_count: int
    waiting_count: int
    confirmed_count: int
    needs_change_count: int
    history_count: int
    cancelled_count: int


def normalize_bookings_section(section: str) -> str:
    key = (section or DEFAULT_BOOKINGS_SECTION).strip().lower()
    return key if key in BOOKINGS_SECTIONS else DEFAULT_BOOKINGS_SECTION


def _is_upcoming_active(booking: Booking, now: datetime) -> bool:
    if booking.status not in (BookingStatus.PENDING, BookingStatus.CONFIRMED):
        return False
    return to_local_naive(booking.start_at) >= now


def _is_waiting(booking: Booking, now: datetime) -> bool:
    return _is_upcoming_active(booking, now) and not has_attendance_response(booking)


def _is_confirmed_attendance(booking: Booking, now: datetime) -> bool:
    return _is_upcoming_active(booking, now) and booking.attendance_status == ATTENDANCE_CONFIRMED


def _is_needs_change(booking: Booking, now: datetime) -> bool:
    return _is_upcoming_active(booking, now) and booking.attendance_status in (
        ATTENDANCE_CANNOT_ATTEND,
        ATTENDANCE_REASON_PROVIDED,
    )


def _is_history(booking: Booking, now: datetime) -> bool:
    return booking.status != BookingStatus.CANCELLED and to_local_naive(booking.start_at) < now


def _is_cancelled(booking: Booking) -> bool:
    return booking.status == BookingStatus.CANCELLED


def compute_bookings_hub_counts(
    bookings: list[Booking],
    now: datetime | None = None,
) -> BookingsHubCounts:
    now = now or now_local()
    upcoming = waiting = confirmed = needs_change = history = cancelled = 0
    for booking in bookings:
        if _is_cancelled(booking):
            cancelled += 1
        if _is_history(booking, now):
            history += 1
        if _is_upcoming_active(booking, now):
            upcoming += 1
            if _is_waiting(booking, now):
                waiting += 1
            elif _is_confirmed_attendance(booking, now):
                confirmed += 1
            elif _is_needs_change(booking, now):
                needs_change += 1
    return BookingsHubCounts(
        upcoming_count=upcoming,
        waiting_count=waiting,
        confirmed_count=confirmed,
        needs_change_count=needs_change,
        history_count=history,
        cancelled_count=cancelled,
    )


def filter_bookings_for_section(
    bookings: list[Booking],
    section: str,
    now: datetime | None = None,
) -> list[Booking]:
    section = normalize_bookings_section(section)
    now = now or now_local()
    if section == "upcoming":
        items = [b for b in bookings if _is_upcoming_active(b, now)]
        items.sort(key=lambda b: to_local_naive(b.start_at))
        return items
    if section == "waiting":
        items = [b for b in bookings if _is_waiting(b, now)]
        items.sort(key=lambda b: to_local_naive(b.start_at))
        return items
    if section == "confirmed":
        items = [b for b in bookings if _is_confirmed_attendance(b, now)]
        items.sort(key=lambda b: to_local_naive(b.start_at))
        return items
    if section == "needs_change":
        items = [b for b in bookings if _is_needs_change(b, now)]
        items.sort(key=lambda b: to_local_naive(b.start_at))
        return items
    if section == "history":
        items = [b for b in bookings if _is_history(b, now)]
        items.sort(key=lambda b: to_local_naive(b.start_at), reverse=True)
        return items
    items = [b for b in bookings if _is_cancelled(b)]
    items.sort(key=lambda b: to_local_naive(b.start_at), reverse=True)
    return items


def paginate_bookings_folder(
    bookings: list[Booking],
    page: int,
    per_page: int = BOOKINGS_PAGE_SIZE,
) -> tuple[list[Booking], int, int]:
    total = len(bookings)
    total_pages = max(1, (total + per_page - 1) // per_page) if total else 1
    page = max(0, min(page, total_pages - 1))
    start = page * per_page
    return bookings[start : start + per_page], page, total_pages


def _folder_label_key(section: str) -> str:
    return f"bookings_folder_{normalize_bookings_section(section)}"


def _button_section_for_list(section: str) -> str | None:
    section = normalize_bookings_section(section)
    if section == "history":
        return "history"
    if section == "cancelled":
        return "cancelled"
    return None


def build_bookings_hub_body(counts: BookingsHubCounts, lang: str) -> str:
    lines = [
        t(lang, "bookings_hub_title"),
        t(lang, "bookings_hub_intro"),
        "",
        f"{t(lang, 'bookings_folder_upcoming')} — {counts.upcoming_count}",
        f"{t(lang, 'bookings_folder_waiting')} — {counts.waiting_count}",
        f"{t(lang, 'bookings_folder_confirmed')} — {counts.confirmed_count}",
        f"{t(lang, 'bookings_folder_needs_change')} — {counts.needs_change_count}",
        f"{t(lang, 'bookings_folder_history')} — {counts.history_count}",
        f"{t(lang, 'bookings_folder_cancelled')} — {counts.cancelled_count}",
    ]
    return "\n".join(lines)


def build_bookings_folder_body(
    section: str,
    page_items: list[Booking],
    lang: str,
) -> str:
    section = normalize_bookings_section(section)
    lines = [t(lang, _folder_label_key(section))]
    intro_key = _FOLDER_INTRO_KEYS.get(section)
    if intro_key:
        lines.append(t(lang, intro_key))
    if not page_items:
        lines.append("")
        lines.append(t(lang, "bookings_empty_folder"))
    return "\n".join(lines)


def format_folder_booking_button(booking: Booking, section: str, lang: str) -> str:
    button_section = _button_section_for_list(section)
    return format_admin_booking_button(booking, lang, section=button_section)


async def load_bookings_hub(session: AsyncSession) -> tuple[list[Booking], BookingsHubCounts]:
    bookings = await BookingRepository(session).list_all_bookings()
    counts = compute_bookings_hub_counts(bookings)
    return bookings, counts


async def load_bookings_folder(
    session: AsyncSession,
    section: str,
    page: int,
) -> tuple[list[Booking], list[Booking], int, int]:
    bookings = await BookingRepository(session).list_all_bookings()
    filtered = filter_bookings_for_section(bookings, section)
    page_items, page, total_pages = paginate_bookings_folder(filtered, page)
    return page_items, filtered, page, total_pages


def parse_bookings_view_callback(data: str) -> tuple[int, str, int]:
    # adm_book:view:{booking_id}:from:{section}:{page}
    parts = data.split(":")
    booking_id = int(parts[2])
    if len(parts) >= 6 and parts[3] == "from":
        section = normalize_bookings_section(parts[4])
        page = int(parts[5]) if parts[5].isdigit() else 0
        return booking_id, section, page
    return booking_id, DEFAULT_BOOKINGS_SECTION, 0


def parse_bookings_list_callback(data: str) -> tuple[str, int]:
    # adm_book:list:{section}:{page}
    parts = data.split(":")
    section = normalize_bookings_section(parts[2] if len(parts) > 2 else DEFAULT_BOOKINGS_SECTION)
    page = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 0
    return section, page


def parse_attendance_back(back: str) -> tuple[str, int]:
    if back.startswith("from:"):
        parts = back.split(":")
        section = normalize_bookings_section(parts[1] if len(parts) > 1 else DEFAULT_BOOKINGS_SECTION)
        page = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
        return section, page
    if back.startswith("list:"):
        return "waiting", 0
    return DEFAULT_BOOKINGS_SECTION, 0
