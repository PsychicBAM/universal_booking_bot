from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.datetime_utils import now_local, to_local_naive
from app.models import (
    Booking,
    BookingStatus,
    BotSettings,
    CalendarSettings,
    Client,
    Service,
    ServiceLocation,
    ServiceMedia,
    ServiceOrder,
    ServiceOrderStatus,
    SERVICE_TYPE_BOOKING,
    SERVICE_TYPE_ORDER,
    SupportMessage,
    SupportMessageStatus,
    UnavailableDate,
    UnavailableTimeRange,
    WorkingBreak,
    WorkingHours,
)


class ClientRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def build_full_name(first_name: str | None, last_name: str | None) -> str | None:
        parts = [p for p in (first_name, last_name) if p]
        if not parts:
            return None
        full = " ".join(parts).strip()
        return full[:100] if full else None

    async def get_by_telegram_id(self, telegram_id: int) -> Client | None:
        result = await self.session.execute(select(Client).where(Client.telegram_id == telegram_id))
        return result.scalar_one_or_none()

    async def get_or_create(self, telegram_id: int, name: str | None = None) -> Client:
        from app.config import get_settings
        from sqlalchemy.exc import IntegrityError

        client = await self.get_by_telegram_id(telegram_id)
        if client:
            if name and not client.name:
                client.name = name
            return client
        client = Client(telegram_id=telegram_id, name=name, language=get_settings().default_language)
        self.session.add(client)
        try:
            await self.session.flush()
        except IntegrityError:
            await self.session.rollback()
            existing = await self.get_by_telegram_id(telegram_id)
            if not existing:
                raise
            return existing
        return client

    async def set_language(self, telegram_id: int, language: str) -> Client:
        client = await self.get_or_create(telegram_id)
        client.language = language
        await self.session.flush()
        return client

    async def update_contact(self, telegram_id: int, name: str, phone: str) -> Client:
        client = await self.get_or_create(telegram_id)
        client.name = name
        client.full_name = name
        if phone:
            client.phone = phone
            client.phone_source = client.phone_source or "imported"
            client.phone_updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        return client

    async def sync_telegram_profile(self, user) -> Client | None:
        if user is None:
            return None
        client = await self.get_or_create(user.id)
        client.first_name = user.first_name
        client.last_name = user.last_name
        client.username = user.username
        client.language_code = user.language_code
        full_name = self.build_full_name(user.first_name, user.last_name)
        if full_name:
            client.full_name = full_name
            if not client.name:
                client.name = full_name
        elif user.first_name and not client.name:
            client.name = user.first_name
        client.last_seen_at = datetime.now(timezone.utc)
        await self.session.flush()
        return client

    async def set_display_name(self, telegram_id: int, name: str) -> Client:
        client = await self.get_or_create(telegram_id)
        stripped = name.strip()
        client.name = stripped
        client.full_name = stripped
        await self.session.flush()
        return client

    async def set_phone(self, telegram_id: int, phone: str, *, source: str) -> Client:
        client = await self.get_or_create(telegram_id)
        client.phone = phone.strip()
        client.phone_source = source
        client.phone_updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        return client

    async def ensure_for_booking(self, telegram_id: int) -> Client:
        return await self.get_or_create(telegram_id)

    async def get_by_id(self, client_id: int) -> Client | None:
        result = await self.session.execute(select(Client).where(Client.id == client_id))
        return result.scalar_one_or_none()

    async def list_by_ids(self, client_ids: list[int]) -> list[Client]:
        if not client_ids:
            return []
        result = await self.session.execute(select(Client).where(Client.id.in_(client_ids)))
        return list(result.scalars().all())


class ServiceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_client_services(self, *, service_type: str | None = None) -> list[Service]:
        """Active, non-archived services visible to clients."""
        stmt = (
            select(Service)
            .where(Service.is_active.is_(True))
            .where(Service.archived_at.is_(None))
            .order_by(Service.name)
        )
        if service_type:
            stmt = stmt.where(Service.service_type == service_type)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_active_services(self) -> list[Service]:
        """Active, non-archived services for admin main list."""
        result = await self.session.execute(
            select(Service)
            .where(Service.is_active.is_(True))
            .where(Service.archived_at.is_(None))
            .order_by(Service.name)
        )
        return list(result.scalars().all())

    async def list_disabled_services(self) -> list[Service]:
        """Disabled but not archived services."""
        result = await self.session.execute(
            select(Service)
            .where(Service.is_active.is_(False))
            .where(Service.archived_at.is_(None))
            .order_by(Service.name)
        )
        return list(result.scalars().all())

    async def list_active(self) -> list[Service]:
        return await self.list_client_services()

    async def list_admin_services(self) -> list[Service]:
        """All non-archived services (active + disabled). For diagnostics only."""
        result = await self.session.execute(
            select(Service).where(Service.archived_at.is_(None)).order_by(Service.name)
        )
        return list(result.scalars().all())

    async def list_archived_services(self) -> list[Service]:
        result = await self.session.execute(
            select(Service).where(Service.archived_at.isnot(None)).order_by(Service.name)
        )
        return list(result.scalars().all())

    async def count_active_services(self) -> int:
        from sqlalchemy import func

        result = await self.session.execute(
            select(func.count())
            .select_from(Service)
            .where(Service.is_active.is_(True))
            .where(Service.archived_at.is_(None))
        )
        return int(result.scalar_one())

    async def count_disabled_services(self) -> int:
        from sqlalchemy import func

        result = await self.session.execute(
            select(func.count())
            .select_from(Service)
            .where(Service.is_active.is_(False))
            .where(Service.archived_at.is_(None))
        )
        return int(result.scalar_one())

    async def count_archived_services(self) -> int:
        from sqlalchemy import func

        result = await self.session.execute(
            select(func.count()).select_from(Service).where(Service.archived_at.isnot(None))
        )
        return int(result.scalar_one())

    async def search_by_name(self, query: str) -> list[Service]:
        pattern = f"%{query.strip()}%"
        result = await self.session.execute(
            select(Service)
            .where(Service.archived_at.is_(None))
            .where(Service.name.ilike(pattern))
            .order_by(Service.name)
        )
        return list(result.scalars().all())

    async def list_all(self) -> list[Service]:
        result = await self.session.execute(select(Service).order_by(Service.name))
        return list(result.scalars().all())

    async def get_by_id(self, service_id: int) -> Service | None:
        result = await self.session.execute(select(Service).where(Service.id == service_id))
        return result.scalar_one_or_none()

    async def buffer_minutes_by_id(self) -> dict[int, int]:
        result = await self.session.execute(select(Service.id, Service.buffer_after_minutes))
        return {row[0]: int(row[1] or 0) for row in result.all()}

    async def create(
        self,
        name: str,
        description: str | None,
        duration_minutes: int,
        price: int,
        buffer_after_minutes: int = 0,
        *,
        service_type: str = SERVICE_TYPE_BOOKING,
    ) -> Service:
        service = Service(
            name=name,
            description=description,
            duration_minutes=duration_minutes,
            buffer_after_minutes=buffer_after_minutes,
            price=price,
            service_type=service_type,
        )
        self.session.add(service)
        await self.session.flush()
        return service

    async def delete(self, service: Service) -> None:
        await self.session.delete(service)

    async def count_bookings_for_service(self, service_id: int) -> int:
        from app.models import Booking

        result = await self.session.execute(
            select(func.count()).select_from(Booking).where(Booking.service_id == service_id)
        )
        return int(result.scalar_one())

    async def archive_service(self, service: Service) -> None:
        service.is_active = False
        service.archived_at = datetime.now(timezone.utc)

    async def restore_service(self, service_id: int) -> Service | None:
        service = await self.get_by_id(service_id)
        if not service or service.archived_at is None:
            return None
        service.is_active = True
        service.archived_at = None
        return service

    async def permanently_delete_service_if_safe(self, service_id: int) -> str:
        """Return 'deleted', 'blocked', or 'not_found'."""
        service = await self.get_by_id(service_id)
        if not service:
            return "not_found"
        if await self.count_bookings_for_service(service_id) > 0:
            return "blocked"
        await self.delete(service)
        return "deleted"

    async def safe_delete_service(self, service_id: int) -> str:
        """Return 'deleted', 'archived', or 'not_found'."""
        service = await self.get_by_id(service_id)
        if not service:
            return "not_found"
        if service.archived_at is not None:
            return "archived"
        if await self.count_bookings_for_service(service_id) > 0:
            await self.archive_service(service)
            return "archived"
        await self.delete(service)
        return "deleted"


class ServiceOrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, order_id: int) -> ServiceOrder | None:
        result = await self.session.execute(
            select(ServiceOrder).where(ServiceOrder.id == order_id)
        )
        return result.scalar_one_or_none()

    async def list_by_status(
        self,
        status: str | None = None,
        *,
        page: int = 0,
        limit: int = 10,
    ) -> tuple[list[ServiceOrder], int]:
        stmt = select(ServiceOrder).order_by(ServiceOrder.created_at.desc())
        if status:
            stmt = stmt.where(ServiceOrder.status == status)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = int((await self.session.execute(count_stmt)).scalar_one())
        stmt = stmt.offset(page * limit).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total

    async def count_by_status(self) -> dict[str, int]:
        result = await self.session.execute(
            select(ServiceOrder.status, func.count())
            .group_by(ServiceOrder.status)
        )
        counts = {row[0]: int(row[1]) for row in result.all()}
        for status in ServiceOrderStatus:
            counts.setdefault(status.value, 0)
        return counts

    async def list_for_client(self, client_id: int) -> list[ServiceOrder]:
        result = await self.session.execute(
            select(ServiceOrder)
            .where(ServiceOrder.client_id == client_id)
            .order_by(ServiceOrder.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_distinct_client_ids(self) -> list[int]:
        result = await self.session.execute(select(ServiceOrder.client_id).distinct())
        return sorted({row[0] for row in result.all()})

    async def list_all_grouped_by_client(
        self, client_ids: list[int]
    ) -> dict[int, list[ServiceOrder]]:
        if not client_ids:
            return {}
        result = await self.session.execute(
            select(ServiceOrder).where(ServiceOrder.client_id.in_(client_ids))
        )
        grouped: dict[int, list[ServiceOrder]] = {client_id: [] for client_id in client_ids}
        for order in result.scalars().all():
            grouped.setdefault(order.client_id, []).append(order)
        return grouped

    async def create(
        self,
        *,
        service_id: int,
        client_id: int,
        client_name: str | None,
        client_phone: str | None,
        client_username: str | None,
        details: str | None,
    ) -> ServiceOrder:
        order = ServiceOrder(
            service_id=service_id,
            client_id=client_id,
            client_name=client_name,
            client_phone=client_phone,
            client_username=client_username,
            details=details,
            status=ServiceOrderStatus.NEW.value,
        )
        self.session.add(order)
        await self.session.flush()
        return order

    async def update_status(self, order_id: int, status: str) -> ServiceOrder | None:
        order = await self.get_by_id(order_id)
        if not order:
            return None
        order.status = status
        if status in (ServiceOrderStatus.COMPLETED.value, ServiceOrderStatus.CANCELLED.value):
            order.closed_at = datetime.now(timezone.utc)
        await self.session.flush()
        return order

    async def set_admin_note(self, order_id: int, note: str | None) -> ServiceOrder | None:
        order = await self.get_by_id(order_id)
        if not order:
            return None
        order.admin_note = note
        await self.session.flush()
        return order


class WorkingHoursRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_active(self) -> list[WorkingHours]:
        result = await self.session.execute(
            select(WorkingHours).where(WorkingHours.is_active.is_(True))
        )
        return list(result.scalars().all())

    async def list_all(self) -> list[WorkingHours]:
        result = await self.session.execute(select(WorkingHours).order_by(WorkingHours.day_of_week))
        return list(result.scalars().all())

    async def get_by_day(self, day_of_week: int) -> WorkingHours | None:
        result = await self.session.execute(
            select(WorkingHours).where(
                WorkingHours.day_of_week == day_of_week,
                WorkingHours.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def get_day_row(self, day_of_week: int) -> WorkingHours | None:
        result = await self.session.execute(
            select(WorkingHours).where(WorkingHours.day_of_week == day_of_week)
        )
        return result.scalar_one_or_none()

    async def upsert_day(self, day_of_week: int, start_time, end_time) -> WorkingHours:
        result = await self.session.execute(
            select(WorkingHours).where(WorkingHours.day_of_week == day_of_week)
        )
        wh = result.scalar_one_or_none()
        if wh:
            wh.start_time = start_time
            wh.end_time = end_time
            wh.is_active = True
        else:
            wh = WorkingHours(day_of_week=day_of_week, start_time=start_time, end_time=end_time)
            self.session.add(wh)
        await self.session.flush()
        return wh

    async def disable_day(self, day_of_week: int) -> None:
        result = await self.session.execute(
            select(WorkingHours).where(WorkingHours.day_of_week == day_of_week)
        )
        wh = result.scalar_one_or_none()
        if wh:
            wh.is_active = False


class WorkingBreakRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_by_weekday(self, weekday: int, *, active_only: bool = True) -> list[WorkingBreak]:
        stmt = select(WorkingBreak).where(WorkingBreak.weekday == weekday)
        if active_only:
            stmt = stmt.where(WorkingBreak.is_active.is_(True))
        stmt = stmt.order_by(WorkingBreak.start_time)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_all(self, *, active_only: bool = True) -> list[WorkingBreak]:
        stmt = select(WorkingBreak).order_by(WorkingBreak.weekday, WorkingBreak.start_time)
        if active_only:
            stmt = stmt.where(WorkingBreak.is_active.is_(True))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, break_id: int) -> WorkingBreak | None:
        result = await self.session.execute(
            select(WorkingBreak).where(WorkingBreak.id == break_id)
        )
        return result.scalar_one_or_none()

    async def _find_duplicate(
        self, weekday: int, start_time, end_time, exclude_id: int | None = None
    ) -> WorkingBreak | None:
        stmt = select(WorkingBreak).where(
            WorkingBreak.weekday == weekday,
            WorkingBreak.start_time == start_time,
            WorkingBreak.end_time == end_time,
        )
        if exclude_id is not None:
            stmt = stmt.where(WorkingBreak.id != exclude_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_break(
        self,
        weekday: int,
        start_time,
        end_time,
        title: str | None = None,
        *,
        working_hours_repo: WorkingHoursRepository | None = None,
    ) -> WorkingBreak:
        from app.services.working_break_service import validate_break_for_day

        wh_repo = working_hours_repo or WorkingHoursRepository(self.session)
        await validate_break_for_day(wh_repo, weekday, start_time, end_time)
        if await self._find_duplicate(weekday, start_time, end_time):
            raise ValueError("duplicate_break")
        br = WorkingBreak(
            weekday=weekday,
            start_time=start_time,
            end_time=end_time,
            title=title,
            is_active=True,
        )
        self.session.add(br)
        await self.session.flush()
        return br

    async def update_break(
        self,
        break_id: int,
        *,
        start_time=None,
        end_time=None,
        title=None,
        is_active: bool | None = None,
        working_hours_repo: WorkingHoursRepository | None = None,
    ) -> WorkingBreak | None:
        from app.services.working_break_service import validate_break_for_day

        br = await self.get_by_id(break_id)
        if not br:
            return None
        new_start = start_time if start_time is not None else br.start_time
        new_end = end_time if end_time is not None else br.end_time
        if start_time is not None or end_time is not None:
            wh_repo = working_hours_repo or WorkingHoursRepository(self.session)
            await validate_break_for_day(wh_repo, br.weekday, new_start, new_end)
            if await self._find_duplicate(br.weekday, new_start, new_end, exclude_id=break_id):
                raise ValueError("duplicate_break")
            br.start_time = new_start
            br.end_time = new_end
        if title is not None:
            br.title = title or None
        if is_active is not None:
            br.is_active = is_active
        await self.session.flush()
        return br

    async def delete_break(self, break_id: int) -> bool:
        br = await self.get_by_id(break_id)
        if not br:
            return False
        await self.session.delete(br)
        await self.session.flush()
        return True


class UnavailableRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_dates(self) -> list[UnavailableDate]:
        result = await self.session.execute(select(UnavailableDate).order_by(UnavailableDate.target_date))
        return list(result.scalars().all())

    async def list_upcoming_dates(self, from_date) -> list[UnavailableDate]:
        result = await self.session.execute(
            select(UnavailableDate)
            .where(UnavailableDate.target_date >= from_date)
            .order_by(UnavailableDate.target_date)
        )
        return list(result.scalars().all())

    async def get_date_by_id(self, item_id: int) -> UnavailableDate | None:
        result = await self.session.execute(select(UnavailableDate).where(UnavailableDate.id == item_id))
        return result.scalar_one_or_none()

    async def delete_date(self, item_id: int) -> bool:
        item = await self.get_date_by_id(item_id)
        if not item:
            return False
        await self.session.delete(item)
        await self.session.flush()
        return True

    async def add_date(self, target_date, reason: str | None = None) -> UnavailableDate:
        result = await self.session.execute(
            select(UnavailableDate).where(UnavailableDate.target_date == target_date)
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.reason = reason
            return existing
        item = UnavailableDate(target_date=target_date, reason=reason)
        self.session.add(item)
        await self.session.flush()
        return item

    async def is_date_unavailable(self, target_date) -> bool:
        result = await self.session.execute(
            select(UnavailableDate).where(UnavailableDate.target_date == target_date)
        )
        return result.scalar_one_or_none() is not None

    async def unavailable_dates_between(self, start_date, end_date) -> set:
        result = await self.session.execute(
            select(UnavailableDate.target_date).where(
                UnavailableDate.target_date >= start_date,
                UnavailableDate.target_date <= end_date,
            )
        )
        return set(result.scalars().all())

    async def time_ranges_between(self, start_date, end_date) -> list:
        result = await self.session.execute(
            select(UnavailableTimeRange)
            .where(UnavailableTimeRange.target_date >= start_date)
            .where(UnavailableTimeRange.target_date <= end_date)
            .order_by(UnavailableTimeRange.target_date, UnavailableTimeRange.start_time)
        )
        return list(result.scalars().all())

    async def list_time_ranges_for_date(self, target_date) -> list[UnavailableTimeRange]:
        result = await self.session.execute(
            select(UnavailableTimeRange).where(UnavailableTimeRange.target_date == target_date)
        )
        return list(result.scalars().all())

    async def list_upcoming_time_ranges(self, from_date) -> list[UnavailableTimeRange]:
        result = await self.session.execute(
            select(UnavailableTimeRange)
            .where(UnavailableTimeRange.target_date >= from_date)
            .order_by(UnavailableTimeRange.target_date, UnavailableTimeRange.start_time)
        )
        return list(result.scalars().all())

    async def get_time_range_by_id(self, item_id: int) -> UnavailableTimeRange | None:
        result = await self.session.execute(
            select(UnavailableTimeRange).where(UnavailableTimeRange.id == item_id)
        )
        return result.scalar_one_or_none()

    async def delete_time_range(self, item_id: int) -> bool:
        item = await self.get_time_range_by_id(item_id)
        if not item:
            return False
        await self.session.delete(item)
        await self.session.flush()
        return True

    async def add_time_range(self, target_date, start_time, end_time, reason: str | None = None):
        item = UnavailableTimeRange(
            target_date=target_date,
            start_time=start_time,
            end_time=end_time,
            reason=reason,
        )
        self.session.add(item)
        await self.session.flush()
        return item


class BookingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, booking_id: int) -> Booking | None:
        result = await self.session.execute(select(Booking).where(Booking.id == booking_id))
        return result.scalar_one_or_none()

    async def list_for_client(self, client_id: int) -> list[Booking]:
        result = await self.session.execute(
            select(Booking)
            .where(Booking.client_id == client_id)
            .where(Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]))
            .order_by(Booking.start_at)
        )
        return list(result.scalars().all())

    async def get_latest_for_client(self, client_id: int) -> Booking | None:
        result = await self.session.execute(
            select(Booking)
            .where(Booking.client_id == client_id)
            .where(Booking.status != BookingStatus.CANCELLED)
            .order_by(Booking.start_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_all_for_client(self, client_id: int) -> list[Booking]:
        result = await self.session.execute(
            select(Booking)
            .where(Booking.client_id == client_id)
            .order_by(Booking.start_at.desc())
        )
        return list(result.scalars().all())

    async def list_distinct_client_ids(self) -> list[int]:
        result = await self.session.execute(select(Booking.client_id).distinct())
        return list(result.scalars().all())

    async def list_all_grouped_by_client(self, client_ids: list[int]) -> dict[int, list[Booking]]:
        if not client_ids:
            return {}
        result = await self.session.execute(
            select(Booking)
            .where(Booking.client_id.in_(client_ids))
            .order_by(Booking.start_at)
        )
        grouped: dict[int, list[Booking]] = {client_id: [] for client_id in client_ids}
        for booking in result.scalars().all():
            grouped.setdefault(booking.client_id, []).append(booking)
        return grouped

    async def list_active_between(self, start: datetime, end: datetime) -> list[Booking]:
        result = await self.session.execute(
            select(Booking)
            .where(Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]))
            .where(Booking.start_at < end)
            .where(Booking.end_at > start)
        )
        return list(result.scalars().all())

    async def find_overlapping_active_booking(
        self,
        candidate_start: datetime,
        candidate_end: datetime,
        candidate_buffer_minutes: int,
        buffer_map: dict[int, int],
        *,
        exclude_booking_id: int | None = None,
    ) -> Booking | None:
        """Return first active booking overlapping [start, end+buffer], or None."""
        from app.utils.datetime_utils import to_local_naive

        candidate_start = to_local_naive(candidate_start)
        candidate_end_buffered = to_local_naive(candidate_end) + timedelta(
            minutes=candidate_buffer_minutes
        )
        bookings = await self.list_active_between(candidate_start, candidate_end_buffered)
        for booking in bookings:
            if exclude_booking_id is not None and booking.id == exclude_booking_id:
                continue
            existing_start = to_local_naive(booking.start_at)
            existing_end = to_local_naive(booking.end_at) + timedelta(
                minutes=buffer_map.get(booking.service_id, 0)
            )
            if existing_start < candidate_end_buffered and existing_end > candidate_start:
                return booking
        return None

    async def has_active_overlap(
        self,
        candidate_start: datetime,
        candidate_end: datetime,
        candidate_buffer_minutes: int,
        buffer_map: dict[int, int],
        *,
        exclude_booking_id: int | None = None,
    ) -> tuple[bool, int | None]:
        conflict = await self.find_overlapping_active_booking(
            candidate_start,
            candidate_end,
            candidate_buffer_minutes,
            buffer_map,
            exclude_booking_id=exclude_booking_id,
        )
        if conflict is None:
            return False, None
        return True, conflict.id

    async def find_exact_active_duplicate(
        self,
        service_id: int,
        start_at: datetime,
        *,
        exclude_booking_id: int | None = None,
    ) -> Booking | None:
        from app.utils.datetime_utils import normalize_slot, slots_match

        start_at = normalize_slot(start_at)
        day_start = start_at.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = start_at.replace(hour=23, minute=59, second=59, microsecond=0)
        bookings = await self.list_active_between(day_start, day_end)
        for booking in bookings:
            if exclude_booking_id is not None and booking.id == exclude_booking_id:
                continue
            if booking.service_id == service_id and slots_match(booking.start_at, start_at):
                return booking
        return None

    async def list_all_bookings(self) -> list[Booking]:
        result = await self.session.execute(select(Booking).order_by(Booking.start_at))
        return list(result.scalars().all())

    async def list_upcoming(self, limit: int = 50) -> list[Booking]:
        now = now_local()
        result = await self.session.execute(
            select(Booking)
            .where(Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]))
            .where(Booking.start_at >= now)
            .order_by(Booking.start_at)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_upcoming_active(self, *, limit: int = 500) -> list[Booking]:
        """All future pending/confirmed bookings, soonest first."""
        now = now_local()
        result = await self.session.execute(
            select(Booking)
            .where(Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]))
            .where(Booking.start_at >= now)
            .order_by(Booking.start_at)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_for_reminders(self, now: datetime | None = None) -> list[Booking]:
        """Future pending/confirmed bookings (local-naive comparison)."""
        now = now or now_local()
        result = await self.session.execute(
            select(Booking).where(
                Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED])
            )
        )
        future: list[Booking] = []
        for booking in result.scalars().all():
            if to_local_naive(booking.start_at) > now:
                future.append(booking)
        future.sort(key=lambda b: to_local_naive(b.start_at))
        return future

    async def create(
        self,
        client_id: int,
        service_id: int,
        start_at: datetime,
        end_at: datetime,
        client_name: str,
        client_phone: str | None,
        status: BookingStatus = BookingStatus.PENDING,
        location_text: str | None = None,
        client_comment: str | None = None,
        service_location_id: int | None = None,
        service_location_title: str | None = None,
        service_location_address: str | None = None,
    ) -> Booking:
        booking = Booking(
            client_id=client_id,
            service_id=service_id,
            start_at=start_at,
            end_at=end_at,
            client_name=client_name,
            client_phone=client_phone,
            location_text=location_text,
            client_comment=client_comment,
            service_location_id=service_location_id,
            service_location_title=service_location_title,
            service_location_address=service_location_address,
            status=status,
        )
        self.session.add(booking)
        await self.session.flush()
        return booking


class SettingsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, key: str, default: str | None = None) -> str | None:
        result = await self.session.execute(select(BotSettings).where(BotSettings.key == key))
        row = result.scalar_one_or_none()
        return row.value if row else default

    async def set(self, key: str, value: str) -> None:
        result = await self.session.execute(select(BotSettings).where(BotSettings.key == key))
        row = result.scalar_one_or_none()
        if row:
            row.value = value
        else:
            self.session.add(BotSettings(key=key, value=value))
        await self.session.flush()

    async def get_calendar_settings(self) -> CalendarSettings:
        result = await self.session.execute(select(CalendarSettings).limit(1))
        row = result.scalar_one_or_none()
        if row:
            return row
        from app.config import get_settings

        row = CalendarSettings(
            google_calendar_enabled=get_settings().google_calendar_enabled,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def set_calendar_enabled(self, enabled: bool) -> None:
        cal = await self.get_calendar_settings()
        cal.google_calendar_enabled = enabled
        await self.session.flush()


MAX_SERVICE_PHOTOS = 5
MAX_SERVICE_VIDEOS = 1


class ServiceMediaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_service(self, service_id: int) -> list[ServiceMedia]:
        result = await self.session.execute(
            select(ServiceMedia)
            .where(ServiceMedia.service_id == service_id)
            .order_by(ServiceMedia.media_type, ServiceMedia.position, ServiceMedia.id)
        )
        return list(result.scalars().all())

    async def count_photos(self, service_id: int) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(ServiceMedia)
            .where(ServiceMedia.service_id == service_id, ServiceMedia.media_type == "photo")
        )
        return int(result.scalar_one())

    async def count_videos(self, service_id: int) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(ServiceMedia)
            .where(ServiceMedia.service_id == service_id, ServiceMedia.media_type == "video")
        )
        return int(result.scalar_one())

    async def get_by_id(self, media_id: int) -> ServiceMedia | None:
        result = await self.session.execute(select(ServiceMedia).where(ServiceMedia.id == media_id))
        return result.scalar_one_or_none()

    async def add(
        self,
        service_id: int,
        media_type: str,
        telegram_file_id: str,
        *,
        is_cover: bool = False,
        position: int = 0,
    ) -> ServiceMedia:
        item = ServiceMedia(
            service_id=service_id,
            media_type=media_type,
            telegram_file_id=telegram_file_id,
            is_cover=is_cover,
            position=position,
        )
        self.session.add(item)
        await self.session.flush()
        return item

    async def delete(self, media: ServiceMedia) -> None:
        await self.session.delete(media)
        await self.session.flush()

    async def clear_covers(self, service_id: int) -> None:
        result = await self.session.execute(
            select(ServiceMedia).where(
                ServiceMedia.service_id == service_id,
                ServiceMedia.media_type == "photo",
            )
        )
        for item in result.scalars().all():
            item.is_cover = False

    async def set_cover(self, media_id: int, service_id: int) -> ServiceMedia | None:
        media = await self.get_by_id(media_id)
        if not media or media.service_id != service_id or media.media_type != "photo":
            return None
        await self.clear_covers(service_id)
        media.is_cover = True
        await self.session.flush()
        return media

    async def get_cover_photo(self, service_id: int) -> ServiceMedia | None:
        result = await self.session.execute(
            select(ServiceMedia).where(
                ServiceMedia.service_id == service_id,
                ServiceMedia.media_type == "photo",
                ServiceMedia.is_cover.is_(True),
            )
        )
        cover = result.scalar_one_or_none()
        if cover:
            return cover
        result = await self.session.execute(
            select(ServiceMedia)
            .where(ServiceMedia.service_id == service_id, ServiceMedia.media_type == "photo")
            .order_by(ServiceMedia.position, ServiceMedia.id)
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_photos(self, service_id: int) -> list[ServiceMedia]:
        result = await self.session.execute(
            select(ServiceMedia)
            .where(ServiceMedia.service_id == service_id, ServiceMedia.media_type == "photo")
            .order_by(ServiceMedia.is_cover.desc(), ServiceMedia.position, ServiceMedia.id)
        )
        return list(result.scalars().all())

    async def get_video(self, service_id: int) -> ServiceMedia | None:
        result = await self.session.execute(
            select(ServiceMedia)
            .where(ServiceMedia.service_id == service_id, ServiceMedia.media_type == "video")
            .limit(1)
        )
        return result.scalar_one_or_none()


class ServiceLocationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_service(self, service_id: int, *, active_only: bool = False) -> list[ServiceLocation]:
        query = select(ServiceLocation).where(ServiceLocation.service_id == service_id)
        if active_only:
            query = query.where(ServiceLocation.is_active.is_(True))
        query = query.order_by(ServiceLocation.position, ServiceLocation.id)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_active_for_service(self, service_id: int) -> list[ServiceLocation]:
        return await self.list_for_service(service_id, active_only=True)

    async def get_by_id(self, location_id: int) -> ServiceLocation | None:
        result = await self.session.execute(
            select(ServiceLocation).where(ServiceLocation.id == location_id)
        )
        return result.scalar_one_or_none()

    async def count_for_service(self, service_id: int) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(ServiceLocation)
            .where(ServiceLocation.service_id == service_id)
        )
        return int(result.scalar_one())

    async def count_bookings(self, location_id: int) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(Booking)
            .where(Booking.service_location_id == location_id)
        )
        return int(result.scalar_one())

    async def next_position(self, service_id: int) -> int:
        result = await self.session.execute(
            select(func.max(ServiceLocation.position)).where(ServiceLocation.service_id == service_id)
        )
        value = result.scalar_one()
        return int(value or 0) + 1

    async def create(
        self,
        service_id: int,
        title: str,
        *,
        address_text: str | None = None,
        description: str | None = None,
    ) -> ServiceLocation:
        location = ServiceLocation(
            service_id=service_id,
            title=title,
            address_text=address_text,
            description=description,
            position=await self.next_position(service_id),
        )
        self.session.add(location)
        await self.session.flush()
        return location

    async def hide(self, location: ServiceLocation) -> None:
        location.is_active = False
        await self.session.flush()

    async def show(self, location: ServiceLocation) -> None:
        location.is_active = True
        await self.session.flush()

    async def delete(self, location: ServiceLocation) -> None:
        await self.session.delete(location)
        await self.session.flush()

    async def safe_delete(self, location_id: int) -> str:
        """Return 'deleted', 'hidden', or 'not_found'."""
        location = await self.get_by_id(location_id)
        if not location:
            return "not_found"
        if await self.count_bookings(location_id) > 0:
            await self.hide(location)
            return "hidden"
        await self.delete(location)
        return "deleted"


class SupportMessageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, message_id: int) -> SupportMessage | None:
        result = await self.session.execute(
            select(SupportMessage).where(SupportMessage.id == message_id)
        )
        return result.scalar_one_or_none()

    async def list_for_client_telegram(
        self, client_telegram_id: int, *, limit: int = 20
    ) -> list[SupportMessage]:
        result = await self.session.execute(
            select(SupportMessage)
            .where(SupportMessage.client_telegram_id == client_telegram_id)
            .order_by(SupportMessage.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create(
        self,
        client_telegram_id: int,
        client_name: str,
        client_username: str | None,
        message_text: str,
        *,
        topic: str | None = None,
        booking_id: int | None = None,
    ) -> SupportMessage:
        item = SupportMessage(
            client_telegram_id=client_telegram_id,
            client_name=client_name,
            client_username=client_username,
            message_text=message_text,
            topic=topic,
            booking_id=booking_id,
            status=SupportMessageStatus.OPEN,
        )
        self.session.add(item)
        await self.session.flush()
        return item

    async def mark_replied(
        self,
        message: SupportMessage,
        admin_telegram_id: int,
        reply_text: str,
    ) -> SupportMessage:
        message.admin_reply_text = reply_text
        message.replied_by_admin_id = admin_telegram_id
        message.status = SupportMessageStatus.REPLIED
        message.replied_at = datetime.now(timezone.utc)
        await self.session.flush()
        return message

    async def mark_closed(self, message: SupportMessage) -> SupportMessage:
        message.status = SupportMessageStatus.CLOSED
        message.closed_at = datetime.now(timezone.utc)
        await self.session.flush()
        return message
