import logging
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import Booking, BookingStatus, Service
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
from app.services.booking_lock import booking_lock_manager
from app.services.calendar_service import CalendarService
from app.services.exceptions import SlotUnavailableError
from app.bot.i18n import t
from app.utils.datetime_utils import normalize_slot, now_local, to_local_naive
from app.utils.formatting import format_datetime

logger = logging.getLogger(__name__)


def _schedule_calendar_sync_create(booking_id: int) -> None:
    from app.services.booking_calendar_sync import schedule_calendar_sync_create

    schedule_calendar_sync_create(booking_id)


def _schedule_calendar_sync_update(booking_id: int) -> None:
    from app.services.booking_calendar_sync import schedule_calendar_sync_update

    schedule_calendar_sync_update(booking_id)


def _schedule_calendar_sync_delete(booking_id: int, event_id: str) -> None:
    from app.services.booking_calendar_sync import schedule_calendar_sync_delete

    schedule_calendar_sync_delete(booking_id, event_id)


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

    async def _assert_slot_available_for_write(
        self,
        service_id: int,
        start_at: datetime,
        *,
        exclude_booking_id: int | None = None,
    ) -> tuple[Service, datetime, datetime]:
        """Final local DB availability check (no Google API). Raises SlotUnavailableError."""
        start_at = normalize_slot(start_at)
        service = await self.service_repo.get_by_id(service_id)
        if not service or not service.is_active or service.archived_at is not None:
            logger.warning("Slot check rejected: service_id=%s not available", service_id)
            raise SlotUnavailableError("service_not_available")

        end_at = start_at + timedelta(minutes=service.duration_minutes)
        buffer_map = await self.service_repo.buffer_minutes_by_id()
        buffer_m = int(service.buffer_after_minutes or 0)

        conflict = await self.booking_repo.find_overlapping_active_booking(
            start_at,
            end_at,
            buffer_m,
            buffer_map,
            exclude_booking_id=exclude_booking_id,
        )
        if conflict is not None:
            logger.warning(
                "Slot unavailable due to overlap: service_id=%s start_at=%s conflict_booking_id=%s",
                service_id,
                start_at.isoformat(),
                conflict.id,
            )
            raise SlotUnavailableError("overlap", conflict_booking_id=conflict.id)

        duplicate = await self.booking_repo.find_exact_active_duplicate(
            service_id, start_at, exclude_booking_id=exclude_booking_id
        )
        if duplicate is not None:
            logger.warning(
                "Slot unavailable due to exact duplicate: service_id=%s start_at=%s booking_id=%s",
                service_id,
                start_at.isoformat(),
                duplicate.id,
            )
            raise SlotUnavailableError("exact_duplicate", conflict_booking_id=duplicate.id)

        available, reason = await self.availability_service.is_slot_available(
            service_id,
            start_at,
            self.service_repo,
            exclude_booking_id=exclude_booking_id,
            include_google=False,
        )
        logger.info(
            "Final availability check: service_id=%s start_at=%s available=%s reason=%s exclude=%s",
            service_id,
            start_at.isoformat(),
            available,
            reason,
            exclude_booking_id,
        )
        if not available:
            raise SlotUnavailableError(reason)

        return service, start_at, end_at

    async def _rollback_session(self) -> None:
        if self.session.in_transaction():
            await self.session.rollback()

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
        logger.info(
            "Booking create requested: telegram_id=%s service_id=%s start_at=%s",
            telegram_id,
            service_id,
            start_at.isoformat(),
        )

        async with booking_lock_manager.hold(start_at.date()):
            try:
                service, start_at, end_at = await self._assert_slot_available_for_write(
                    service_id, start_at
                )
                if service.requires_location and not (location_text and location_text.strip()):
                    raise ValueError("Location required")
                client = await self.client_repo.ensure_for_booking(telegram_id)
                await self.client_repo.set_display_name(telegram_id, client_name)
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
                logger.info(
                    "Booking created: id=%s service_id=%s start_at=%s status=%s",
                    booking.id,
                    service_id,
                    start_at.isoformat(),
                    status.value,
                )
            except SlotUnavailableError:
                await self._rollback_session()
                raise
            except Exception:
                await self._rollback_session()
                raise

        if booking.status == BookingStatus.CONFIRMED:
            _schedule_calendar_sync_create(booking.id)
        return booking

    async def confirm_booking(self, booking_id: int) -> Booking:
        booking = await self.booking_repo.get_by_id(booking_id)
        if not booking:
            raise ValueError("Booking not found")
        booking.status = BookingStatus.CONFIRMED
        await self.session.commit()
        await self.session.refresh(booking)
        _schedule_calendar_sync_create(booking.id)
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

        event_id = booking.google_event_id
        booking.status = BookingStatus.CANCELLED
        await self.session.commit()
        await self.session.refresh(booking)
        if event_id:
            _schedule_calendar_sync_delete(booking.id, event_id)
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
        booking.attendance_status = None
        booking.attendance_responded_at = None
        booking.attendance_reason = None
        booking.attendance_reminder_type = None

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

    async def sync_calendar_for_booking(self, booking: Booking) -> None:
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
                logger.info("Google Calendar sync success: booking_id=%s event_id=%s", booking.id, event_id)
            else:
                logger.warning(
                    "Google Calendar sync failed, but booking was saved: booking_id=%s",
                    booking.id,
                )
        except Exception:
            logger.exception(
                "Google Calendar sync failed, but booking was saved: booking_id=%s",
                booking.id,
            )

    async def update_calendar_for_booking(self, booking: Booking) -> None:
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
                await self.sync_calendar_for_booking(booking)
        except Exception:
            logger.exception(
                "Google Calendar update failed, but booking was saved: booking_id=%s",
                booking.id,
            )

    async def delete_calendar_event(self, event_id: str) -> None:
        try:
            await self.calendar_service.delete_event(event_id)
        except Exception:
            logger.exception("Google Calendar delete failed for event_id=%s", event_id)

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
        logger.info(
            "Reschedule requested: booking_id=%s telegram_id=%s new_start_at=%s",
            booking_id,
            telegram_id,
            new_start_at.isoformat(),
        )

        async with booking_lock_manager.hold(new_start_at.date()):
            try:
                booking = await self._get_editable_client_booking(booking_id, telegram_id)
                if not self._can_reschedule_by_time(booking):
                    raise ValueError("Too late to reschedule")

                service, new_start_at, new_end_at = await self._assert_slot_available_for_write(
                    booking.service_id,
                    new_start_at,
                    exclude_booking_id=booking.id,
                )

                old_start = booking.start_at
                booking.start_at = new_start_at
                booking.end_at = new_end_at
                self._reset_reminders(booking)
                await self.session.flush()
                await self.session.commit()
                await self.session.refresh(booking)
                logger.info(
                    "Booking rescheduled: id=%s from=%s to=%s",
                    booking.id,
                    old_start,
                    new_start_at,
                )
            except SlotUnavailableError:
                await self._rollback_session()
                raise
            except Exception:
                await self._rollback_session()
                raise

        if booking.status == BookingStatus.CONFIRMED:
            _schedule_calendar_sync_update(booking.id)

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
            _schedule_calendar_sync_update(booking.id)
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
            _schedule_calendar_sync_update(booking.id)
        return booking

    async def change_client_comment(
        self,
        booking_id: int,
        telegram_id: int,
        comment: str | None,
    ) -> Booking:
        booking = await self._get_editable_client_booking(booking_id, telegram_id)
        service = await self.service_repo.get_by_id(booking.service_id)
        if not service or not service.ask_client_comment:
            raise ValueError("Comment change not allowed")

        booking.client_comment = comment.strip() if comment and comment.strip() else None
        await self.session.commit()
        await self.session.refresh(booking)

        if booking.status == BookingStatus.CONFIRMED:
            _schedule_calendar_sync_update(booking.id)
        return booking
