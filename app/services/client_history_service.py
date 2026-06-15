from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.i18n import t
from app.bot.utils.attendance_helpers import ATTENDANCE_CANNOT_ATTEND, ATTENDANCE_REASON_PROVIDED
from app.bot.utils.booking_labels import format_admin_booking_button
from app.models import Booking, BookingStatus, Client
from app.repositories import BookingRepository, ClientRepository, ServiceRepository
from app.utils.datetime_utils import now_local, to_local_naive
from app.utils.formatting import format_datetime

CLIENT_PAGE_SIZE = 10
DEFAULT_CLIENT_FILTER = "all"
VALID_CLIENT_FILTERS = frozenset(
    {"upcoming", "visited", "new", "returning", "cancelled", "all"}
)


def normalize_client_filter(filter_key: str) -> str:
    key = (filter_key or DEFAULT_CLIENT_FILTER).strip().lower()
    return key if key in VALID_CLIENT_FILTERS else DEFAULT_CLIENT_FILTER


def paginate_client_stats(
    items: list[ClientStats], page: int, per_page: int = CLIENT_PAGE_SIZE
) -> tuple[list[ClientStats], int, int]:
    total = len(items)
    total_pages = max(1, (total + per_page - 1) // per_page) if total else 1
    page = max(0, min(page, total_pages - 1))
    start = page * per_page
    return items[start : start + per_page], page, total_pages


def is_cancelled_booking(booking: Booking) -> bool:
    return booking.status == BookingStatus.CANCELLED


def is_non_cancelled_booking(booking: Booking) -> bool:
    return booking.status != BookingStatus.CANCELLED


def is_upcoming_booking(booking: Booking, now: datetime | None = None) -> bool:
    now = now or now_local()
    if booking.status not in (BookingStatus.PENDING, BookingStatus.CONFIRMED):
        return False
    return to_local_naive(booking.start_at) >= now


def is_past_served_booking(booking: Booking, now: datetime | None = None) -> bool:
    now = now or now_local()
    if booking.status == BookingStatus.COMPLETED:
        return True
    if booking.status in (BookingStatus.PENDING, BookingStatus.CONFIRMED):
        return to_local_naive(booking.start_at) < now
    return False


def is_cannot_attend_booking(booking: Booking) -> bool:
    return booking.attendance_status in (ATTENDANCE_CANNOT_ATTEND, ATTENDANCE_REASON_PROVIDED)


@dataclass
class ClientStats:
    client_id: int
    telegram_id: int
    name: str
    phone: str | None
    username: str | None
    telegram_name: str | None
    phone_source: str | None
    last_seen_at: datetime | None
    first_booking_at: datetime | None
    last_booking_at: datetime | None
    next_booking_at: datetime | None
    total_bookings: int
    non_cancelled_count: int
    completed_or_past_count: int
    upcoming_count: int
    cancelled_count: int
    cannot_attend_count: int
    last_service_name: str | None
    status_label_key: str


@dataclass
class ClientHistory:
    stats: ClientStats
    future_bookings: list[Booking]
    history_bookings: list[Booking]


def client_status_label_key(stats: ClientStats) -> str:
    if stats.non_cancelled_count >= 2 or (
        stats.completed_or_past_count >= 1 and stats.upcoming_count >= 1
    ):
        return "client_status_returning"
    if stats.non_cancelled_count == 1:
        return "client_status_new"
    if stats.completed_or_past_count > 0:
        return "client_status_visited"
    return "client_status_new"


def matches_client_filter(stats: ClientStats, filter_key: str) -> bool:
    key = normalize_client_filter(filter_key)
    if key == "all":
        return True
    if key == "upcoming":
        return stats.upcoming_count > 0
    if key == "visited":
        return stats.completed_or_past_count > 0
    if key == "new":
        return stats.non_cancelled_count == 1
    if key == "returning":
        return stats.non_cancelled_count >= 2 or (
            stats.completed_or_past_count >= 1 and stats.upcoming_count >= 1
        )
    if key == "cancelled":
        return stats.cancelled_count > 0
    return True


def _display_name(client: Client, bookings: list[Booking]) -> str:
    full_name = getattr(client, "full_name", None)
    if full_name:
        return full_name
    if client.name:
        return client.name
    for booking in sorted(bookings, key=lambda b: b.start_at, reverse=True):
        if booking.client_name:
            return booking.client_name
    return str(client.telegram_id)


def _display_phone(client: Client, bookings: list[Booking]) -> str | None:
    if client.phone:
        return client.phone
    for booking in sorted(bookings, key=lambda b: b.start_at, reverse=True):
        if booking.client_phone:
            return booking.client_phone
    return None


def compute_client_stats(
    client: Client,
    bookings: list[Booking],
    service_names: dict[int, str],
    *,
    now: datetime | None = None,
) -> ClientStats:
    now = now or now_local()
    total = len(bookings)
    non_cancelled = [b for b in bookings if is_non_cancelled_booking(b)]
    cancelled_count = sum(1 for b in bookings if is_cancelled_booking(b))
    upcoming = [b for b in non_cancelled if is_upcoming_booking(b, now)]
    past_served = [b for b in non_cancelled if is_past_served_booking(b, now)]
    cannot_attend_count = sum(1 for b in bookings if is_cannot_attend_booking(b))

    sorted_all = sorted(bookings, key=lambda b: b.start_at)
    first_booking_at = sorted_all[0].start_at if sorted_all else None
    last_past_at = max((b.start_at for b in past_served), default=None)
    next_booking_at = min((b.start_at for b in upcoming), default=None)

    last_service_name = None
    if sorted_all:
        latest = sorted_all[-1]
        last_service_name = service_names.get(latest.service_id)

    stats = ClientStats(
        client_id=client.id,
        telegram_id=client.telegram_id,
        name=_display_name(client, bookings),
        phone=_display_phone(client, bookings),
        username=getattr(client, "username", None),
        telegram_name=getattr(client, "full_name", None)
        or ClientRepository.build_full_name(
            getattr(client, "first_name", None), getattr(client, "last_name", None)
        ),
        phone_source=getattr(client, "phone_source", None),
        last_seen_at=getattr(client, "last_seen_at", None),
        first_booking_at=first_booking_at,
        last_booking_at=last_past_at,
        next_booking_at=next_booking_at,
        total_bookings=total,
        non_cancelled_count=len(non_cancelled),
        completed_or_past_count=len(past_served),
        upcoming_count=len(upcoming),
        cancelled_count=cancelled_count,
        cannot_attend_count=cannot_attend_count,
        last_service_name=last_service_name,
        status_label_key="client_status_new",
    )
    stats.status_label_key = client_status_label_key(stats)
    return stats


def format_client_list_label(stats: ClientStats, lang: str) -> str:
    name = stats.name
    if stats.status_label_key == "client_status_new" or stats.non_cancelled_count == 1:
        return t(lang, "clients_list_new", name=name, count=str(stats.non_cancelled_count))
    if stats.status_label_key == "client_status_returning":
        if stats.next_booking_at:
            next_date = stats.next_booking_at.strftime("%d.%m")
            return t(
                lang,
                "clients_list_returning",
                name=name,
                count=str(stats.non_cancelled_count),
                date=next_date,
            )
        return t(
            lang,
            "clients_list_returning_no_next",
            name=name,
            count=str(stats.non_cancelled_count),
        )
    if stats.cancelled_count > 0 and stats.completed_or_past_count == 0 and stats.upcoming_count == 0:
        return t(lang, "clients_list_cancelled", name=name, count=str(stats.cancelled_count))
    if stats.completed_or_past_count > 0:
        return t(
            lang,
            "clients_list_visited",
            name=name,
            count=str(stats.completed_or_past_count),
        )
    if stats.upcoming_count > 0:
        next_date = stats.next_booking_at.strftime("%d.%m") if stats.next_booking_at else "—"
        return t(
            lang,
            "clients_list_returning",
            name=name,
            count=str(stats.non_cancelled_count),
            date=next_date,
        )
    return t(lang, "clients_list_new", name=name, count=str(stats.non_cancelled_count))


def format_client_detail_text(stats: ClientStats, lang: str) -> str:
    from app.services.client_data_service import phone_source_label

    phone = stats.phone or t(lang, "not_provided")
    username = f"@{stats.username}" if stats.username else t(lang, "not_provided")
    telegram_name = stats.telegram_name or t(lang, "not_provided")
    phone_source = phone_source_label(lang, stats.phone_source) if stats.phone else t(lang, "not_provided")
    last_seen = format_datetime(stats.last_seen_at) if stats.last_seen_at else t(lang, "not_provided")
    first_date = format_datetime(stats.first_booking_at) if stats.first_booking_at else "—"
    last_date = format_datetime(stats.last_booking_at) if stats.last_booking_at else "—"
    next_date = (
        format_datetime(stats.next_booking_at)
        if stats.next_booking_at
        else t(lang, "client_next_booking_none")
    )
    status = t(lang, stats.status_label_key)
    return "\n".join(
        [
            t(lang, "client_detail_title"),
            "",
            t(lang, "client_name_line", name=stats.name),
            t(lang, "client_telegram_name_line", name=telegram_name),
            t(lang, "client_phone_line", phone=phone),
            t(lang, "client_phone_source_line", source=phone_source),
            t(lang, "client_username_line", username=username),
            t(lang, "client_telegram_id_line", telegram_id=str(stats.telegram_id)),
            t(lang, "client_last_seen_line", datetime=last_seen),
            "",
            t(lang, "client_stats_title"),
            t(lang, "client_total_bookings", count=str(stats.total_bookings)),
            t(lang, "client_upcoming_count", count=str(stats.upcoming_count)),
            t(lang, "client_past_count", count=str(stats.completed_or_past_count)),
            t(lang, "client_cancelled_count", count=str(stats.cancelled_count)),
            t(lang, "client_cannot_attend_count", count=str(stats.cannot_attend_count)),
            t(lang, "client_first_booking", date=first_date),
            t(lang, "client_last_booking", date=last_date),
            t(lang, "client_next_booking", date=next_date),
            t(lang, "client_status_line", status=status),
        ]
    )


def format_booking_history_row(
    booking: Booking,
    service_name: str,
    lang: str,
    client: Client | None = None,
) -> str:
    section = "cancelled" if is_cancelled_booking(booking) else "history"
    return format_admin_booking_button(booking, lang, section=section, client=client)


def format_future_booking_row(
    booking: Booking,
    service_name: str,
    lang: str,
    client: Client | None = None,
) -> str:
    return format_admin_booking_button(booking, lang, client=client)


async def _load_service_names(session: AsyncSession) -> dict[int, str]:
    services = await ServiceRepository(session).list_all()
    return {service.id: service.name for service in services}


async def _build_stats_index(session: AsyncSession) -> dict[int, ClientStats]:
    client_ids = await BookingRepository(session).list_distinct_client_ids()
    if not client_ids:
        return {}
    clients = {
        client.id: client
        for client in await ClientRepository(session).list_by_ids(client_ids)
    }
    bookings_by_client = await BookingRepository(session).list_all_grouped_by_client(client_ids)
    service_names = await _load_service_names(session)
    now = now_local()
    stats_index: dict[int, ClientStats] = {}
    for client_id in client_ids:
        client = clients.get(client_id)
        if not client:
            continue
        bookings = bookings_by_client.get(client_id, [])
        stats_index[client_id] = compute_client_stats(client, bookings, service_names, now=now)
    return stats_index


async def get_client_stats(session: AsyncSession, client_id: int) -> ClientStats | None:
    client = await ClientRepository(session).get_by_id(client_id)
    if not client:
        return None
    bookings = await BookingRepository(session).list_all_for_client(client_id)
    if not bookings:
        return None
    service_names = await _load_service_names(session)
    return compute_client_stats(client, bookings, service_names)


async def list_clients(
    session: AsyncSession,
    filter_key: str,
    *,
    page: int = 0,
    limit: int = CLIENT_PAGE_SIZE,
) -> tuple[list[ClientStats], int, int]:
    filter_key = normalize_client_filter(filter_key)
    stats_index = await _build_stats_index(session)
    filtered = [stats for stats in stats_index.values() if matches_client_filter(stats, filter_key)]
    filtered.sort(key=lambda s: (s.last_booking_at or s.next_booking_at or s.first_booking_at or now_local()), reverse=True)
    return paginate_client_stats(filtered, page, per_page=limit)


async def get_client_history(session: AsyncSession, client_id: int) -> ClientHistory | None:
    client = await ClientRepository(session).get_by_id(client_id)
    if not client:
        return None
    bookings = await BookingRepository(session).list_all_for_client(client_id)
    if not bookings:
        return None
    service_names = await _load_service_names(session)
    now = now_local()
    stats = compute_client_stats(client, bookings, service_names, now=now)
    future = sorted(
        [b for b in bookings if is_upcoming_booking(b, now)],
        key=lambda b: b.start_at,
    )
    history = [
        b
        for b in bookings
        if is_cancelled_booking(b) or is_past_served_booking(b, now) or is_cannot_attend_booking(b)
    ]
    history.sort(key=lambda b: b.start_at, reverse=True)
    return ClientHistory(stats=stats, future_bookings=future, history_bookings=history)


async def search_clients(session: AsyncSession, query: str) -> list[ClientStats]:
    query = (query or "").strip()
    if not query:
        return []
    stats_index = await _build_stats_index(session)
    results = [stats for stats in stats_index.values() if match_client_search_query(stats, query)]
    results.sort(key=lambda s: s.name.lower())
    return results


def match_client_search_query(stats: ClientStats, query: str) -> bool:
    query = (query or "").strip()
    if not query:
        return False
    needle = query.lower().lstrip("@")
    if needle in stats.name.lower():
        return True
    if stats.phone and needle in stats.phone.replace(" ", "").replace("-", "").lower():
        return True
    if stats.username and needle in stats.username.lower():
        return True
    if query.isdigit():
        if str(stats.telegram_id) == query or str(stats.client_id) == query:
            return True
    if str(stats.telegram_id).startswith(query):
        return True
    return False
