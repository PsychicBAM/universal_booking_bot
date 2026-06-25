from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.i18n import t
from app.bot.utils.attendance_helpers import (
    ATTENDANCE_CANNOT_ATTEND,
    ATTENDANCE_REASON_PROVIDED,
    has_attendance_response,
)
from app.bot.utils.booking_labels import format_admin_booking_button
from app.models import Booking, BookingStatus
from app.repositories import BookingRepository
from app.utils.datetime_utils import now_local, to_local_naive

BOOKINGS_PAGE_SIZE = 10
BOOKINGS_SECTIONS = frozenset(
    {
        "active",
        "upcoming",
        "pending_admin",
        "confirmed_bookings",
        "waiting_client_response",
        "needs_change",
        "history",
        "cancelled",
        "search",
    }
)
SECTION_ALIASES = {
    "waiting": "pending_admin",
    "confirmed": "confirmed_bookings",
    "pending": "pending_admin",
    "upcoming": "active",
}
LIST_SECTION_ALIASES = {
    "upcoming": "active",
    "confirmed_bookings": "active",
    "waiting_client_response": "active",
    "needs_change": "active",
}
DEFAULT_BOOKINGS_SECTION = "active"
DEFAULT_CLIENT_FILTER = "all"


@dataclass(frozen=True)
class BookingDetailSource:
    """Where admin opened a booking detail screen (for Back navigation)."""

    origin: str = "bookings"  # bookings | client | unknown
    section: str = DEFAULT_BOOKINGS_SECTION
    page: int = 0
    client_id: int | None = None
    client_tab: str | None = None  # future | hist
    client_filter: str = DEFAULT_CLIENT_FILTER
    client_section_page: int = 0


def _safe_int_token(token: str | None) -> int | None:
    return int(token) if token and token.isdigit() else None


def _client_tab_from_short(token: str) -> str:
    return "future" if token == "f" else "hist"


def _client_tab_to_short(tab: str) -> str:
    return "f" if tab == "future" else "h"


def build_booking_view_callback(booking_id: int, source: BookingDetailSource) -> str:
    if source.origin == "client" and source.client_id is not None and source.client_tab:
        tab = _client_tab_to_short(source.client_tab)
        return (
            f"adm_book:view:{booking_id}:from:c:{source.client_id}:{tab}:"
            f"{source.client_filter}:{source.page}:{source.client_section_page}"
        )
    section = normalize_bookings_section(source.section)
    return f"adm_book:view:{booking_id}:from:{section}:{source.page}"


def parse_booking_detail_source(data: str) -> tuple[int | None, BookingDetailSource | None]:
    parts = data.split(":")
    if parts[0] == "adm_booking" and len(parts) >= 2:
        booking_id = _safe_int_token(parts[1])
        if booking_id is None:
            return None, None
        return booking_id, BookingDetailSource(origin="unknown")
    if len(parts) < 4 or parts[0] != "adm_book" or parts[1] != "view":
        return None, None
    booking_id = _safe_int_token(parts[2])
    if booking_id is None:
        return None, None
    if len(parts) >= 6 and parts[3] == "from":
        if parts[4] == "c" and len(parts) >= 8:
            client_id = _safe_int_token(parts[5])
            if client_id is None:
                return booking_id, BookingDetailSource(origin="unknown")
            client_tab = _client_tab_from_short(parts[6])
            from app.services.client_history_service import normalize_client_filter

            client_filter = normalize_client_filter(parts[7] if len(parts) > 7 else DEFAULT_CLIENT_FILTER)
            page = _safe_int_token(parts[8] if len(parts) > 8 else None) or 0
            section_page = _safe_int_token(parts[9] if len(parts) > 9 else None) or 0
            return booking_id, BookingDetailSource(
                origin="client",
                client_id=client_id,
                client_tab=client_tab,
                client_filter=client_filter,
                page=page,
                client_section_page=section_page,
            )
        section = resolve_bookings_list_section(parts[4] if len(parts) > 4 else DEFAULT_BOOKINGS_SECTION)
        page = _safe_int_token(parts[5] if len(parts) > 5 else None) or 0
        return booking_id, BookingDetailSource(section=section, page=page)
    return booking_id, BookingDetailSource(origin="unknown")


def booking_detail_back_callback(source: BookingDetailSource) -> str:
    if source.origin == "client" and source.client_id is not None and source.client_tab:
        return (
            f"adm_cli:{source.client_tab}:{source.client_id}:"
            f"{source.client_filter}:{source.page}:{source.client_section_page}"
        )
    if source.origin == "bookings":
        return f"adm_book:list:{normalize_bookings_section(source.section)}:{source.page}"
    return "adm_book:hub"


def encode_attendance_back(source: BookingDetailSource) -> str:
    if source.origin == "client" and source.client_id is not None and source.client_tab:
        tab = _client_tab_to_short(source.client_tab)
        return (
            f"from:c:{source.client_id}:{tab}:{source.client_filter}:"
            f"{source.page}:{source.client_section_page}"
        )
    section = normalize_bookings_section(source.section)
    return f"from:{section}:{source.page}"


def parse_attendance_back(back: str) -> BookingDetailSource:
    if back.startswith("from:c:"):
        parts = back.split(":")
        client_id = _safe_int_token(parts[2] if len(parts) > 2 else None)
        if client_id is None:
            return BookingDetailSource(origin="unknown")
        client_tab = _client_tab_from_short(parts[3] if len(parts) > 3 else "h")
        from app.services.client_history_service import normalize_client_filter

        client_filter = normalize_client_filter(parts[4] if len(parts) > 4 else DEFAULT_CLIENT_FILTER)
        page = _safe_int_token(parts[5] if len(parts) > 5 else None) or 0
        section_page = _safe_int_token(parts[6] if len(parts) > 6 else None) or 0
        return BookingDetailSource(
            origin="client",
            client_id=client_id,
            client_tab=client_tab,
            client_filter=client_filter,
            page=page,
            client_section_page=section_page,
        )
    if back.startswith("from:"):
        parts = back.split(":")
        section = resolve_bookings_list_section(parts[1] if len(parts) > 1 else DEFAULT_BOOKINGS_SECTION)
        page = _safe_int_token(parts[2] if len(parts) > 2 else None) or 0
        return BookingDetailSource(section=section, page=page)
    if back.startswith("list:"):
        return BookingDetailSource(section="active", page=0)
    return BookingDetailSource(origin="unknown")


def booking_detail_action_flags(
    booking: Booking,
    *,
    show_send_confirmation: bool = True,
    now: datetime | None = None,
) -> dict[str, bool]:
    now = now or now_local()
    status = booking.status.value if hasattr(booking.status, "value") else str(booking.status)
    is_future = to_local_naive(booking.start_at) >= now
    if status == BookingStatus.CANCELLED.value or status == BookingStatus.COMPLETED.value:
        return {
            "can_confirm": False,
            "can_cancel": False,
            "can_send_confirmation": False,
            "show_message": True,
        }
    if not is_future:
        return {
            "can_confirm": False,
            "can_cancel": False,
            "can_send_confirmation": False,
            "show_message": True,
        }
    return {
        "can_confirm": status == BookingStatus.PENDING.value,
        "can_cancel": status in (BookingStatus.PENDING.value, BookingStatus.CONFIRMED.value),
        "can_send_confirmation": status == BookingStatus.CONFIRMED.value and show_send_confirmation,
        "show_message": True,
    }

_FOLDER_INTRO_KEYS = {
    "pending_admin": "bookings_pending_admin_intro",
    "history": "bookings_folder_history",
    "cancelled": "bookings_folder_cancelled",
}

_FOLDER_TITLE_KEYS = {
    "active": "bookings_all_active_title",
    "pending_admin": "bookings_pending_admin_title",
    "confirmed_bookings": "bookings_all_active_title",
    "waiting_client_response": "bookings_all_active_title",
    "needs_change": "bookings_all_active_title",
    "upcoming": "bookings_all_active_title",
    "history": "bookings_folder_history",
    "cancelled": "bookings_folder_cancelled",
    "search": "bookings_search_button",
}


@dataclass
class BookingsHubCounts:
    active_count: int
    upcoming_count: int
    pending_admin_count: int
    confirmed_bookings_count: int
    waiting_client_response_count: int
    needs_change_count: int
    history_count: int
    cancelled_count: int


def normalize_bookings_section(section: str) -> str:
    key = (section or DEFAULT_BOOKINGS_SECTION).strip().lower()
    key = SECTION_ALIASES.get(key, key)
    return key if key in BOOKINGS_SECTIONS else DEFAULT_BOOKINGS_SECTION


def resolve_bookings_list_section(section: str) -> str:
    key = (section or DEFAULT_BOOKINGS_SECTION).strip().lower()
    key = LIST_SECTION_ALIASES.get(key, key)
    return normalize_bookings_section(key)


def _is_future(booking: Booking, now: datetime) -> bool:
    return to_local_naive(booking.start_at) >= now


def _is_upcoming_active(booking: Booking, now: datetime) -> bool:
    return booking.status in (BookingStatus.PENDING, BookingStatus.CONFIRMED) and _is_future(booking, now)


def _is_pending_admin(booking: Booking, now: datetime) -> bool:
    return booking.status == BookingStatus.PENDING and _is_future(booking, now)


def _is_confirmed_booking(booking: Booking, now: datetime) -> bool:
    return booking.status == BookingStatus.CONFIRMED and _is_future(booking, now)


def _is_waiting_client_response(booking: Booking, now: datetime) -> bool:
    return _is_confirmed_booking(booking, now) and not has_attendance_response(booking)


def _is_needs_change(booking: Booking, now: datetime) -> bool:
    return _is_confirmed_booking(booking, now) and booking.attendance_status in (
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
    upcoming = pending_admin = confirmed_bookings = waiting_client_response = 0
    needs_change = history = cancelled = 0
    for booking in bookings:
        if _is_cancelled(booking):
            cancelled += 1
        if _is_history(booking, now):
            history += 1
        if _is_upcoming_active(booking, now):
            upcoming += 1
        if _is_pending_admin(booking, now):
            pending_admin += 1
        if _is_confirmed_booking(booking, now):
            confirmed_bookings += 1
        if _is_waiting_client_response(booking, now):
            waiting_client_response += 1
        if _is_needs_change(booking, now):
            needs_change += 1
    return BookingsHubCounts(
        active_count=upcoming,
        upcoming_count=upcoming,
        pending_admin_count=pending_admin,
        confirmed_bookings_count=confirmed_bookings,
        waiting_client_response_count=waiting_client_response,
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
    if section == "active":
        items = [b for b in bookings if _is_upcoming_active(b, now)]
    elif section == "upcoming":
        items = [b for b in bookings if _is_upcoming_active(b, now)]
    elif section == "pending_admin":
        items = [b for b in bookings if _is_pending_admin(b, now)]
    elif section == "confirmed_bookings":
        items = [b for b in bookings if _is_confirmed_booking(b, now)]
    elif section == "waiting_client_response":
        items = [b for b in bookings if _is_waiting_client_response(b, now)]
    elif section == "needs_change":
        items = [b for b in bookings if _is_needs_change(b, now)]
    elif section == "history":
        items = [b for b in bookings if _is_history(b, now)]
    else:
        items = [b for b in bookings if _is_cancelled(b)]
    if section == "history" or section == "cancelled":
        items.sort(key=lambda b: to_local_naive(b.start_at), reverse=True)
    else:
        items.sort(key=lambda b: to_local_naive(b.start_at))
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


def _folder_title_key(section: str) -> str:
    section = normalize_bookings_section(section)
    return _FOLDER_TITLE_KEYS.get(section, f"bookings_folder_{section}")


def _button_section_for_list(section: str) -> str | None:
    section = normalize_bookings_section(section)
    if section in ("active", "upcoming", "confirmed_bookings", "waiting_client_response", "needs_change"):
        return None
    if section in ("history", "cancelled", "pending_admin"):
        return section
    return section


def build_bookings_hub_body(counts: BookingsHubCounts, lang: str) -> str:
    lines = [
        t(lang, "bookings_hub_title"),
        t(lang, "bookings_active_summary", count=str(counts.active_count)),
        t(lang, "bookings_pending_summary", count=str(counts.pending_admin_count)),
        t(lang, "bookings_confirmed_summary", count=str(counts.confirmed_bookings_count)),
        t(
            lang,
            "bookings_waiting_client_response_summary",
            count=str(counts.waiting_client_response_count),
        ),
        t(lang, "bookings_history_summary", count=str(counts.history_count)),
        t(lang, "bookings_cancelled_summary", count=str(counts.cancelled_count)),
        "",
        t(lang, "bookings_choose_action"),
    ]
    return "\n".join(lines)


def build_bookings_folder_body(
    section: str,
    page_items: list[Booking],
    lang: str,
) -> str:
    section = normalize_bookings_section(section)
    lines = [t(lang, _folder_title_key(section))]
    intro_key = _FOLDER_INTRO_KEYS.get(section)
    if intro_key:
        lines.append(t(lang, intro_key))
    if not page_items:
        lines.append("")
        lines.append(t(lang, "bookings_empty_folder"))
    return "\n".join(lines)


def format_folder_booking_button(
    booking: Booking,
    section: str,
    lang: str,
    *,
    service_name: str | None = None,
) -> str:
    button_section = _button_section_for_list(section)
    return format_admin_booking_button(
        booking,
        lang,
        section=button_section,
        service_name=service_name,
    )


def search_bookings(
    bookings: list[Booking],
    query: str,
    service_names: dict[int, str],
) -> list[Booking]:
    query = (query or "").strip()
    if not query:
        return []
    if query.isdigit():
        booking_id = int(query)
        return [booking for booking in bookings if booking.id == booking_id]
    needle = query.lower()
    matched: list[Booking] = []
    seen: set[int] = set()
    for booking in bookings:
        if booking.id in seen:
            continue
        service_name = service_names.get(booking.service_id, "")
        haystack = " ".join(
            filter(
                None,
                [
                    booking.client_name or "",
                    booking.client_phone or "",
                    service_name,
                ],
            )
        ).lower()
        if needle in haystack:
            matched.append(booking)
            seen.add(booking.id)
    matched.sort(key=lambda b: to_local_naive(b.start_at), reverse=True)
    return matched


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


def parse_bookings_view_callback(data: str) -> tuple[int, BookingDetailSource]:
    booking_id, source = parse_booking_detail_source(data)
    if booking_id is None or source is None:
        return 0, BookingDetailSource(origin="unknown")
    return booking_id, source


def parse_bookings_list_callback(data: str) -> tuple[str, int]:
    parts = data.split(":")
    section = resolve_bookings_list_section(parts[2] if len(parts) > 2 else DEFAULT_BOOKINGS_SECTION)
    page = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 0
    return section, page
