import logging
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import Booking, BookingStatus
from app.repositories import (
    BookingRepository,
    ClientRepository,
    ServiceLocationRepository,
    ServiceRepository,
    SettingsRepository,
    UnavailableRepository,
    WorkingHoursRepository,
)
from app.services.availability_service import AvailabilityService
from app.services.calendar_service import CalendarService
from app.bot.i18n import t
from app.utils.datetime_utils import normalize_slot, now_local, to_local_naive
from app.utils.formatting import format_datetime

logger = logging.getLogger(__name__)


class BookingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.settings = get_settings()
        self.client_repo = ClientRepository(session)
        self.service_repo = ServiceRepository(session)
        self.booking_repo = BookingRepository(session)
        self.settings_repo = SettingsRepository(session)
        self.calendar_service = CalendarService(session)
        self.availability_service = AvailabilityService(
            working_hours_repo=WorkingHoursRepository(session),
            unavailable_repo=UnavailableRepository(session),
            booking_repo=self.booking_repo,
            calendar_service=self.calendar_service,
        )

    async def create_booking(
        self,
        telegram_id: int,
        service_id: int,
        start_at: datetime,
        client_name: str,
        client_phone: str | None,
        auto_confirm: bool = False,
        location_text: str | None = None,
        client_comment: str | None = None,
        service_location_id: int | None = None,
        service_location_title: str | None = None,
        service_location_address: str | None = None,
    ) -> Booking:
        start_at = normalize_slot(start_at)
        service = await self.service_repo.get_by_id(service_id)
        if not service or not service.is_active or service.archived_at is not None:
            logger.warning("Booking rejected: service_id=%s not available", service_id)
            raise ValueError("Service not available")

        available, reason = await self.availability_service.is_slot_available(
            service_id, start_at, self.service_repo
        )
        logger.info(
            "Booking availability check: service_id=%s date=%s time=%s datetime=%s "
            "duration=%s available=%s reason=%s google_cal=%s",
            service_id,
            start_at.date(),
            start_at.time(),
            start_at.isoformat(),
            service.duration_minutes,
            available,
            reason,
            await self.calendar_service.is_enabled(),
        )
        if not available:
            raise ValueError("Time slot is no longer available")

        end_at = start_at + timedelta(minutes=service.duration_minutes)
        client = await self.client_repo.update_contact(telegram_id, client_name, client_phone or "")
        status = BookingStatus.CONFIRMED if auto_confirm else BookingStatus.PENDING
        booking = await self.booking_repo.create(
            client_id=client.id,
            service_id=service.id,
            start_at=start_at,
            end_at=end_at,
            client_name=client_name,
            client_phone=client_phone,
            status=status,
            location_text=location_text,
            client_comment=client_comment,
            service_location_id=service_location_id,
            service_location_title=service_location_title,
            service_location_address=service_location_address,
        )
        await self.session.commit()
        await self.session.refresh(booking)
        logger.info("Booking created: id=%s service_id=%s start_at=%s", booking.id, service_id, start_at)

        if status == BookingStatus.CONFIRMED:
            await self._sync_calendar(booking)
        return booking

    async def confirm_booking(self, booking_id: int) -> Booking:
        booking = await self.booking_repo.get_by_id(booking_id)
        if not booking:
            raise ValueError("Booking not found")
        booking.status = BookingStatus.CONFIRMED
        await self.session.commit()
        await self.session.refresh(booking)
        await self._sync_calendar(booking)
        return booking

    async def cancel_booking(self, booking_id: int, *, telegram_id: int | None = None) -> Booking:
        booking = await self.booking_repo.get_by_id(booking_id)
        if not booking:
            raise ValueError("Booking not found")

        if telegram_id is not None:
            client = await self.client_repo.get_by_telegram_id(telegram_id)
            if not client or booking.client_id != client.id:
                raise ValueError("Not allowed")

            if to_local_naive(booking.start_at) - now_local() <= timedelta(
                hours=self.settings.cancel_booking_hours_before
            ):
                raise ValueError("Too late to cancel")

        if booking.google_event_id:
            await self.calendar_service.delete_event(booking.google_event_id)

        booking.status = BookingStatus.CANCELLED
        await self.session.commit()
        await self.session.refresh(booking)
        return booking

    async def complete_booking(self, booking_id: int) -> Booking:
        booking = await self.booking_repo.get_by_id(booking_id)
        if not booking:
            raise ValueError("Booking not found")
        booking.status = BookingStatus.COMPLETED
        await self.session.commit()
        await self.session.refresh(booking)
        return booking

    async def _get_editable_client_booking(self, booking_id: int, telegram_id: int) -> Booking:
        booking = await self.booking_repo.get_by_id(booking_id)
        client = await self.client_repo.get_by_telegram_id(telegram_id)
        if not booking or not client or booking.client_id != client.id:
            raise ValueError("Not allowed")
        if booking.status not in (BookingStatus.PENDING, BookingStatus.CONFIRMED):
            raise ValueError("Not editable")
        return booking

    def _can_reschedule_by_time(self, booking: Booking) -> bool:
        return to_local_naive(booking.start_at) - now_local() > timedelta(
            hours=self.settings.effective_reschedule_hours_before()
        )

    def _reset_reminders(self, booking: Booking) -> None:
        booking.client_reminder_1_sent_at = None
        booking.client_reminder_2_sent_at = None
        booking.admin_reminder_sent_at = None

    @staticmethod
    def _event_location(booking: Booking) -> str | None:
        return booking.location_text or booking.service_location_address or None

    async def _build_calendar_payload(self, booking: Booking) -> tuple[str, str, str | None]:
        service = await self.service_repo.get_by_id(booking.service_id)
        lang = self.settings.default_language
        service_name = service.name if service else "?"
        summary = t(lang, "calendar_event_title", service_name=service_name)
        description_parts = [
            t(lang, "calendar_label_client", value=booking.client_name),
            t(
                lang,
                "calendar_label_phone",
                value=booking.client_phone or t(lang, "phone_not_provided"),
            ),
            t(lang, "calendar_label_service", value=service_name),
            t(
                lang,
                "calendar_label_datetime",
                value=format_datetime(booking.start_at),
            ),
        ]
        if booking.service_location_title:
            description_parts.append(
                t(
                    lang,
                    "calendar_label_service_location",
                    title=booking.service_location_title,
                )
            )
            if booking.service_location_address:
                description_parts.append(
                    t(
                        lang,
                        "calendar_label_service_location_address",
                        value=booking.service_location_address,
                    )
                )
        if booking.location_text:
            description_parts.append(
                t(lang, "calendar_label_address", value=booking.location_text)
            )
        if booking.client_comment:
            description_parts.append(
                t(lang, "calendar_label_comment", value=booking.client_comment)
            )
        description_parts.append(
            t(lang, "calendar_label_booking_id", value=str(booking.id))
        )
        return summary, "\n".join(description_parts), self._event_location(booking)

    async def _sync_calendar(self, booking: Booking) -> None:
        if not await self.calendar_service.is_enabled():
            return
        try:
            summary, description, location = await self._build_calendar_payload(booking)
            event_id = await self.calendar_service.create_event(
                summary=summary,
                start_at=booking.start_at,
                end_at=booking.end_at,
                description=description,
                location=location,
            )
            if event_id:
                booking.google_event_id = event_id
                await self.session.commit()
        except Exception:
            logger.exception("Failed to sync booking %s to Google Calendar", booking.id)

    async def _update_calendar(self, booking: Booking) -> None:
        if not await self.calendar_service.is_enabled():
            return
        try:
            summary, description, location = await self._build_calendar_payload(booking)
            if booking.google_event_id:
                event_id = await self.calendar_service.update_event(
                    booking.google_event_id,
                    summary=summary,
                    start_at=booking.start_at,
                    end_at=booking.end_at,
                    description=description,
                    location=location,
                )
                if event_id and event_id != booking.google_event_id:
                    booking.google_event_id = event_id
                    await self.session.commit()
            elif booking.status == BookingStatus.CONFIRMED:
                await self._sync_calendar(booking)
        except Exception:
            logger.exception("Failed to update Google Calendar for booking %s", booking.id)

    async def reschedule_booking(
        self,
        booking_id: int,
        telegram_id: int,
        new_start_at: datetime,
    ) -> Booking:
        booking = await self._get_editable_client_booking(booking_id, telegram_id)
        if not self._can_reschedule_by_time(booking):
            raise ValueError("Too late to reschedule")

        new_start_at = normalize_slot(new_start_at)
        service = await self.service_repo.get_by_id(booking.service_id)
        if not service or not service.is_active or service.archived_at is not None:
            raise ValueError("Service not available")

        available, reason = await self.availability_service.is_slot_available(
            booking.service_id,
            new_start_at,
            self.service_repo,
            exclude_booking_id=booking.id,
        )
        logger.info(
            "Reschedule availability: booking_id=%s new_start=%s available=%s reason=%s",
            booking_id,
            new_start_at.isoformat(),
            available,
            reason,
        )
        if not available:
            raise ValueError("Time slot is no longer available")

        old_start = booking.start_at
        booking.start_at = new_start_at
        booking.end_at = new_start_at + timedelta(minutes=service.duration_minutes)
        self._reset_reminders(booking)
        await self.session.commit()
        await self.session.refresh(booking)

        if booking.status == BookingStatus.CONFIRMED:
            await self._update_calendar(booking)

        logger.info(
            "Booking rescheduled: id=%s from=%s to=%s",
            booking.id,
            old_start,
            new_start_at,
        )
        return booking

    async def change_service_location(
        self,
        booking_id: int,
        telegram_id: int,
        location_id: int,
    ) -> Booking:
        booking = await self._get_editable_client_booking(booking_id, telegram_id)
        location = await ServiceLocationRepository(self.session).get_by_id(location_id)
        if (
            not location
            or location.service_id != booking.service_id
            or not location.is_active
        ):
            raise ValueError("Invalid location")

        booking.service_location_id = location.id
        booking.service_location_title = location.title
        booking.service_location_address = location.address_text
        await self.session.commit()
        await self.session.refresh(booking)

        if booking.status == BookingStatus.CONFIRMED:
            await self._update_calendar(booking)
        return booking

    async def change_client_address(
        self,
        booking_id: int,
        telegram_id: int,
        address: str,
    ) -> Booking:
        booking = await self._get_editable_client_booking(booking_id, telegram_id)
        service = await self.service_repo.get_by_id(booking.service_id)
        if not service or not service.requires_location:
            raise ValueError("Address change not allowed")

        booking.location_text = address.strip() or None
        await self.session.commit()
        await self.session.refresh(booking)

        if booking.status == BookingStatus.CONFIRMED:
            await self._update_calendar(booking)
        return booking

    async def change_client_comment(
        self,
        booking_id: int,
        telegram_id: int,
        comment: str | None,
    ) -> Booking:
        booking = await self._get_editable_client_booking(booking_id, telegram_id)
        service = await self.service_repo.get_by_id(booking.service_id)
        if not service or not service.requires_location:
            raise ValueError("Comment change not allowed")

        booking.client_comment = comment.strip() if comment and comment.strip() else None
        await self.session.commit()
        await self.session.refresh(booking)

        if booking.status == BookingStatus.CONFIRMED:
            await self._update_calendar(booking)
        return booking
