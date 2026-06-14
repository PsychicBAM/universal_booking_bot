from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.datetime_utils import now_local
from app.models import (
    Booking,
    BookingStatus,
    BotSettings,
    CalendarSettings,
    Client,
    Service,
    ServiceLocation,
    ServiceMedia,
    UnavailableDate,
    UnavailableTimeRange,
    WorkingHours,
)


class ClientRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

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
        client.phone = phone
        await self.session.flush()
        return client


class ServiceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_active(self) -> list[Service]:
        return await self.list_active_services()

    async def list_active_services(self) -> list[Service]:
        result = await self.session.execute(
            select(Service)
            .where(Service.is_active.is_(True))
            .where(Service.archived_at.is_(None))
            .order_by(Service.name)
        )
        return list(result.scalars().all())

    async def list_archived_services(self) -> list[Service]:
        result = await self.session.execute(
            select(Service).where(Service.archived_at.isnot(None)).order_by(Service.name)
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
    ) -> Service:
        service = Service(
            name=name,
            description=description,
            duration_minutes=duration_minutes,
            buffer_after_minutes=buffer_after_minutes,
            price=price,
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

    async def list_active_between(self, start: datetime, end: datetime) -> list[Booking]:
        result = await self.session.execute(
            select(Booking)
            .where(Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]))
            .where(Booking.start_at < end)
            .where(Booking.end_at > start)
        )
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

    async def list_for_reminders(self, now: datetime) -> list[Booking]:
        result = await self.session.execute(
            select(Booking)
            .where(Booking.status == BookingStatus.CONFIRMED)
            .where(Booking.start_at > now)
        )
        return list(result.scalars().all())

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
