from dataclasses import dataclass
from datetime import date, datetime, time as dt_time, timedelta
import logging
import time as perf_time

from app.config import get_settings
from app.models import Service, WorkingBreak, WorkingHours
from app.repositories import (
    BookingRepository,
    ServiceRepository,
    UnavailableRepository,
    WorkingBreakRepository,
    WorkingHoursRepository,
)
from app.services.calendar_service import CalendarService
from app.utils.datetime_utils import now_local, normalize_slot, slots_match, to_local_naive

logger = logging.getLogger(__name__)


@dataclass
class _RangeContext:
    working_hours: dict[int, WorkingHours]
    working_breaks: list[WorkingBreak]
    unavailable_dates: set[date]
    time_ranges_by_date: dict[date, list[tuple[datetime, datetime]]]
    booking_ranges: list[tuple[datetime, datetime]]
    google_busy_ranges: list[tuple[datetime, datetime]]


class AvailabilityService:
    def __init__(
        self,
        working_hours_repo: WorkingHoursRepository,
        unavailable_repo: UnavailableRepository,
        booking_repo: BookingRepository,
        calendar_service: CalendarService,
        working_breaks_repo: WorkingBreakRepository | None = None,
    ) -> None:
        self.working_hours_repo = working_hours_repo
        self.unavailable_repo = unavailable_repo
        self.booking_repo = booking_repo
        self.calendar_service = calendar_service
        self.working_breaks_repo = working_breaks_repo
        self.settings = get_settings()

    async def get_available_dates(
        self,
        service_id: int,
        service_repo: ServiceRepository,
        *,
        days_limit: int | None = None,
        exclude_booking_id: int | None = None,
    ) -> list[date]:
        service = await service_repo.get_by_id(service_id)
        if not service or not service.is_active:
            return []

        today = now_local().date()
        page_days = days_limit if days_limit is not None else self.settings.booking_first_page_days
        page_days = min(page_days, self.settings.booking_days_ahead)
        end_date = today + timedelta(days=max(page_days - 1, 0))

        ctx = await self._build_range_context(
            today, end_date, service_repo, exclude_booking_id=exclude_booking_id
        )

        dates: list[date] = []
        current = today
        while current <= end_date:
            if self._date_has_slots_cached(current, service, ctx):
                dates.append(current)
            current += timedelta(days=1)
        return dates

    async def get_available_slots(
        self,
        service_id: int,
        target_date: date,
        service_repo: ServiceRepository,
        *,
        exclude_booking_id: int | None = None,
    ) -> list[datetime]:
        service = await service_repo.get_by_id(service_id)
        if not service:
            return []
        if await self.unavailable_repo.is_date_unavailable(target_date):
            return []

        wh = await self.working_hours_repo.get_by_day(target_date.weekday())
        if not wh:
            return []

        duration = timedelta(minutes=service.duration_minutes)
        buffer = timedelta(minutes=service.buffer_after_minutes)
        step = timedelta(minutes=self.settings.default_slot_step_minutes)
        day_start = datetime.combine(target_date, wh.start_time)
        day_end = datetime.combine(target_date, wh.end_time)

        now = now_local()
        blocked_ranges = await self._collect_blocked_ranges(
            target_date, day_start, day_end, service_repo, exclude_booking_id=exclude_booking_id
        )
        slots: list[datetime] = []
        cursor = day_start
        while cursor + duration <= day_end:
            slot_end = cursor + duration
            occupied_end = slot_end + buffer
            if cursor >= now and not self._overlaps_any(cursor, occupied_end, blocked_ranges):
                slots.append(normalize_slot(cursor))
            cursor += step
        return slots

    async def _build_range_context(
        self,
        start_date: date,
        end_date: date,
        service_repo: ServiceRepository,
        *,
        exclude_booking_id: int | None = None,
    ) -> _RangeContext:
        working_hours = {
            wh.day_of_week: wh for wh in await self.working_hours_repo.list_active()
        }
        unavailable_dates = await self.unavailable_repo.unavailable_dates_between(
            start_date, end_date
        )
        time_ranges_by_date: dict[date, list[tuple[datetime, datetime]]] = {}
        for item in await self.unavailable_repo.time_ranges_between(start_date, end_date):
            time_ranges_by_date.setdefault(item.target_date, []).append(
                (
                    datetime.combine(item.target_date, item.start_time),
                    datetime.combine(item.target_date, item.end_time),
                )
            )

        range_start = datetime.combine(start_date, dt_time.min)
        range_end = datetime.combine(end_date, dt_time(23, 59, 59))
        bookings = await self.booking_repo.list_active_between(range_start, range_end)
        buffer_map = await service_repo.buffer_minutes_by_id()
        booking_ranges: list[tuple[datetime, datetime]] = []
        for booking in bookings:
            if exclude_booking_id is not None and booking.id == exclude_booking_id:
                continue
            buffer_m = buffer_map.get(booking.service_id, 0)
            booking_ranges.append(
                (
                    to_local_naive(booking.start_at),
                    to_local_naive(booking.end_at) + timedelta(minutes=buffer_m),
                )
            )

        google_busy_ranges: list[tuple[datetime, datetime]] = []
        if await self.calendar_service.is_enabled():
            t_google = perf_time.perf_counter()
            raw_busy = await self.calendar_service.get_busy_ranges(
                range_start,
                range_end,
                timeout_seconds=self.settings.google_calendar_busy_timeout_seconds,
            )
            google_busy_ranges = [
                (to_local_naive(busy_start), to_local_naive(busy_end))
                for busy_start, busy_end in raw_busy
            ]
            google_duration = perf_time.perf_counter() - t_google
            if google_busy_ranges:
                first = google_busy_ranges[0]
                last = google_busy_ranges[-1]
                logger.info(
                    "Google busy ranges loaded: count=%s first=%s—%s last=%s—%s duration=%.2fs",
                    len(google_busy_ranges),
                    first[0],
                    first[1],
                    last[0],
                    last[1],
                    google_duration,
                )
            else:
                logger.debug(
                    "Google busy ranges: none (duration=%.2fs)", google_duration
                )

        return _RangeContext(
            working_hours=working_hours,
            working_breaks=(
                await self.working_breaks_repo.list_all(active_only=True)
                if self.working_breaks_repo
                else []
            ),
            unavailable_dates=unavailable_dates,
            time_ranges_by_date=time_ranges_by_date,
            booking_ranges=booking_ranges,
            google_busy_ranges=google_busy_ranges,
        )

    def _date_has_slots_cached(
        self, target_date: date, service: Service, ctx: _RangeContext
    ) -> bool:
        if target_date in ctx.unavailable_dates:
            return False
        wh = ctx.working_hours.get(target_date.weekday())
        if not wh:
            return False

        duration = timedelta(minutes=service.duration_minutes)
        buffer = timedelta(minutes=service.buffer_after_minutes)
        day_start = datetime.combine(target_date, wh.start_time)
        day_end = datetime.combine(target_date, wh.end_time)
        if day_start + duration > day_end:
            return False

        blocked = self._blocked_ranges_for_day(target_date, day_start, day_end, ctx)
        step = timedelta(minutes=self.settings.default_slot_step_minutes)
        now = now_local()
        cursor = day_start
        while cursor + duration <= day_end:
            occupied_end = cursor + duration + buffer
            if cursor >= now and not self._overlaps_any(cursor, occupied_end, blocked):
                return True
            cursor += step
        return False

    @staticmethod
    def _blocked_ranges_for_day(
        target_date: date,
        day_start: datetime,
        day_end: datetime,
        ctx: _RangeContext,
    ) -> list[tuple[datetime, datetime]]:
        ranges = list(ctx.time_ranges_by_date.get(target_date, []))
        for br in ctx.working_breaks:
            if br.weekday == target_date.weekday() and br.is_active:
                ranges.append(
                    (
                        datetime.combine(target_date, br.start_time),
                        datetime.combine(target_date, br.end_time),
                    )
                )
        for blocked_start, blocked_end in ctx.booking_ranges:
            if blocked_start < day_end and blocked_end > day_start:
                ranges.append((blocked_start, blocked_end))
        for busy_start, busy_end in ctx.google_busy_ranges:
            busy_start = to_local_naive(busy_start)
            busy_end = to_local_naive(busy_end)
            if busy_start < day_end and busy_end > day_start:
                ranges.append((busy_start, busy_end))
        return ranges

    async def _collect_blocked_ranges(
        self,
        target_date: date,
        day_start: datetime,
        day_end: datetime,
        service_repo: ServiceRepository,
        *,
        exclude_booking_id: int | None = None,
        include_google: bool = True,
    ) -> list[tuple[datetime, datetime]]:
        ranges: list[tuple[datetime, datetime]] = []

        for item in await self.unavailable_repo.list_time_ranges_for_date(target_date):
            ranges.append(
                (
                    datetime.combine(target_date, item.start_time),
                    datetime.combine(target_date, item.end_time),
                )
            )

        if self.working_breaks_repo:
            for br in await self.working_breaks_repo.list_by_weekday(
                target_date.weekday(), active_only=True
            ):
                ranges.append(
                    (
                        datetime.combine(target_date, br.start_time),
                        datetime.combine(target_date, br.end_time),
                    )
                )

        bookings = await self.booking_repo.list_active_between(day_start, day_end)
        buffer_map = await service_repo.buffer_minutes_by_id()
        for booking in bookings:
            if exclude_booking_id is not None and booking.id == exclude_booking_id:
                continue
            buffer_m = buffer_map.get(booking.service_id, 0)
            ranges.append(
                (
                    to_local_naive(booking.start_at),
                    to_local_naive(booking.end_at) + timedelta(minutes=buffer_m),
                )
            )

        if include_google and await self.calendar_service.is_enabled():
            busy = await self.calendar_service.get_busy_ranges(
                day_start,
                day_end,
                timeout_seconds=self.settings.google_calendar_busy_timeout_seconds,
            )
            for busy_start, busy_end in busy:
                ranges.append((to_local_naive(busy_start), to_local_naive(busy_end)))
        return ranges

    @staticmethod
    def _overlaps_any(start: datetime, end: datetime, ranges: list[tuple[datetime, datetime]]) -> bool:
        start = to_local_naive(start)
        end = to_local_naive(end)
        for blocked_start, blocked_end in ranges:
            blocked_start = to_local_naive(blocked_start)
            blocked_end = to_local_naive(blocked_end)
            if start < blocked_end and end > blocked_start:
                return True
        return False

    async def is_slot_available(
        self,
        service_id: int,
        slot_start: datetime,
        service_repo: ServiceRepository,
        *,
        exclude_booking_id: int | None = None,
        include_google: bool = True,
    ) -> tuple[bool, str]:
        service = await service_repo.get_by_id(service_id)
        if not service or not service.is_active:
            return False, "service_not_found_or_inactive"

        slot_start = normalize_slot(slot_start)
        target_date = slot_start.date()

        if await self.unavailable_repo.is_date_unavailable(target_date):
            return False, "date_marked_unavailable"

        wh = await self.working_hours_repo.get_by_day(target_date.weekday())
        if not wh:
            return False, "no_working_hours_for_weekday"

        duration = timedelta(minutes=service.duration_minutes)
        buffer = timedelta(minutes=service.buffer_after_minutes)
        day_start = datetime.combine(target_date, wh.start_time)
        day_end = datetime.combine(target_date, wh.end_time)
        slot_end = slot_start + duration

        if slot_start < day_start or slot_end > day_end:
            return False, "outside_working_hours"

        if slot_start < now_local():
            return False, "slot_in_past"

        blocked_ranges = await self._collect_blocked_ranges(
            target_date,
            day_start,
            day_end,
            service_repo,
            exclude_booking_id=exclude_booking_id,
            include_google=include_google,
        )
        if self._overlaps_any(slot_start, slot_end + buffer, blocked_ranges):
            return False, "overlaps_blocked_range_or_existing_booking"

        slots = await self.get_available_slots(
            service_id, target_date, service_repo, exclude_booking_id=exclude_booking_id
        )
        for s in slots:
            if slots_match(s, slot_start):
                return True, "ok"

        return False, "slot_not_on_availability_grid"
