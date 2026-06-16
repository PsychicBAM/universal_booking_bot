import logging
import time
from dataclasses import dataclass
from datetime import datetime

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.i18n import t
from app.config import get_settings
from app.database.session import async_session_factory
from app.models import Booking, Client
from app.repositories import BookingRepository, ServiceRepository
from app.services.attendance_service import (
    attendance_reminder_keyboard,
    format_attendance_reminder_text,
)
from app.services.confirmation_text_service import load_confirmation_text_config
from app.services.language_service import get_user_language
from app.services.reminder_diagnostics import reminder_flags_summary_for_log, reminder_was_sent
from app.services.reminder_matching import is_reminder_due, reminder_window_label
from app.services.reminder_settings import ReminderConfig, load_reminder_config
from app.utils.datetime_utils import now_local, to_local_naive
from app.utils.formatting import format_datetime
from app.utils.perf_logging import log_action_timing

logger = logging.getLogger(__name__)

REMINDER_LOG_LOOKAHEAD_MINUTES = 24 * 60


@dataclass(frozen=True)
class ManualTestResult:
    ok: bool
    message_key: str
    booking_id: int | None = None


class ReminderService:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.settings = get_settings()

    @staticmethod
    def _log_process_timing(*, processed: int, errors: int, started_at: float) -> None:
        try:
            log_action_timing(
                "reminder run",
                processed=processed,
                errors=errors,
                total=time.perf_counter() - started_at,
            )
        except Exception:
            logger.exception("Reminder timing log failed (reminder job completed)")

    async def process_reminders(self) -> None:
        t_total = time.perf_counter()
        processed = 0
        errors = 0
        try:
            async with async_session_factory() as session:
                config = await load_reminder_config(session)
                if not config.enabled:
                    logger.info("Reminder check skipped: reminders disabled")
                    return
                text_config = await load_confirmation_text_config(session)

                now = now_local()
                bookings = await BookingRepository(session).list_for_reminders(now)
                self._log_run_header(config, now, len(bookings))

                for booking in bookings:
                    try:
                        await self._process_booking_reminders(
                            session, booking, now, config, text_config, log_details=True
                        )
                        processed += 1
                    except Exception:
                        errors += 1
                        logger.exception(
                            "Reminder processing failed for booking_id=%s",
                            booking.id,
                        )

                await session.commit()
        except Exception:
            errors += 1
            logger.exception("Reminder job failed")
        finally:
            self._log_process_timing(processed=processed, errors=errors, started_at=t_total)

    def _log_run_header(self, config: ReminderConfig, now: datetime, booking_count: int) -> None:
        if config.test_mode:
            logger.info(
                "Reminder check: now=%s test_mode=True client_test=%sm admin_test=%sm "
                "attendance=%s bookings_checked=%s",
                now.strftime("%Y-%m-%d %H:%M"),
                config.test_client_reminder_minutes,
                config.test_admin_reminder_minutes,
                config.attendance_confirmation_enabled,
                booking_count,
            )
        else:
            logger.info(
                "Reminder check: now=%s test_mode=False client1=%sm client2=%sm admin=%sm "
                "attendance=%s bookings_checked=%s",
                now.strftime("%Y-%m-%d %H:%M"),
                config.client_reminder_1_minutes,
                config.client_reminder_2_minutes,
                config.admin_reminder_minutes,
                config.attendance_confirmation_enabled,
                booking_count,
            )

    def _log_booking_candidate(self, booking: Booking, delta_minutes: float) -> None:
        if delta_minutes > REMINDER_LOG_LOOKAHEAD_MINUTES:
            return
        status = booking.status.value if hasattr(booking.status, "value") else booking.status
        logger.info(
            "Reminder candidate booking_id=%s starts_in=%.1fmin status=%s %s attendance_status=%s",
            booking.id,
            delta_minutes,
            status,
            reminder_flags_summary_for_log(booking),
            booking.attendance_status or "none",
        )

    def _log_skip(self, booking_id: int, reason: str, **extra) -> None:
        parts = [f"Skip booking_id={booking_id} reason={reason}"]
        for key, value in extra.items():
            parts.append(f"{key}={value}")
        logger.info(" ".join(parts))

    async def _process_booking_reminders(
        self,
        session: AsyncSession,
        booking: Booking,
        now: datetime,
        config: ReminderConfig,
        text_config,
        *,
        log_details: bool,
    ) -> None:
        start_at = to_local_naive(booking.start_at)
        delta_minutes = (start_at - now).total_seconds() / 60
        if delta_minutes <= 0:
            if log_details and delta_minutes > -REMINDER_LOG_LOOKAHEAD_MINUTES:
                self._log_skip(booking.id, "already started", starts_in=f"{delta_minutes:.1f}min")
            return

        client = await session.get(Client, booking.client_id)
        if not client:
            if log_details:
                self._log_skip(booking.id, "client not found")
            return

        if log_details:
            self._log_booking_candidate(booking, delta_minutes)

        service = await ServiceRepository(session).get_by_id(booking.service_id)
        service_name = service.name if service else f"#{booking.service_id}"
        date_time = format_datetime(start_at)
        client_lang = client.language or self.settings.default_language

        if config.test_mode:
            await self._maybe_send_client_test_reminder(
                booking,
                client,
                client_lang,
                service_name,
                date_time,
                now,
                config,
                text_config,
                delta_minutes,
                log_details=log_details,
            )
            await self._maybe_send_admin_reminder(
                booking,
                service_name,
                date_time,
                now,
                config,
                delta_minutes,
                test_mode=True,
                log_details=log_details,
            )
            return

        await self._maybe_send_client_reminders(
            booking,
            client,
            client_lang,
            service_name,
            date_time,
            now,
            config,
            text_config,
            delta_minutes,
            log_details=log_details,
        )
        await self._maybe_send_admin_reminder(
            booking,
            service_name,
            date_time,
            now,
            config,
            delta_minutes,
            test_mode=False,
            log_details=log_details,
        )

    async def send_manual_test_reminders(self) -> ManualTestResult:
        """Send client + admin reminder for nearest booking without touching sent flags."""
        async with async_session_factory() as session:
            config = await load_reminder_config(session)
            text_config = await load_confirmation_text_config(session)
            bookings = await BookingRepository(session).list_upcoming_active(limit=1)
            if not bookings:
                return ManualTestResult(False, "reminder_test_manual_no_bookings")
            booking = bookings[0]
            client = await session.get(Client, booking.client_id)
            if not client:
                return ManualTestResult(False, "reminder_test_manual_fail", booking.id)
            service = await ServiceRepository(session).get_by_id(booking.service_id)
            service_name = service.name if service else f"#{booking.service_id}"
            start_at = to_local_naive(booking.start_at)
            date_time = format_datetime(start_at)
            client_lang = client.language or self.settings.default_language
            now = now_local()

            client_ok = await self._send_client_reminder(
                booking,
                client,
                client_lang,
                service_name,
                date_time,
                now,
                config,
                text_config,
                "client_1",
            )
            admin_ok = await self._send_admin_reminder_messages(
                booking, service_name, date_time, mark_sent=False
            )
            if client_ok and admin_ok:
                logger.info(
                    "Manual test reminders sent for booking_id=%s (flags unchanged)",
                    booking.id,
                )
                return ManualTestResult(True, "reminder_test_manual_ok", booking.id)
            if client_ok or admin_ok:
                return ManualTestResult(False, "reminder_test_manual_partial", booking.id)
            return ManualTestResult(False, "reminder_test_manual_fail", booking.id)

    async def _maybe_send_client_test_reminder(
        self,
        booking: Booking,
        client: Client,
        client_lang: str,
        service_name: str,
        date_time: str,
        now: datetime,
        config: ReminderConfig,
        text_config,
        delta_minutes: float,
        *,
        log_details: bool,
    ) -> None:
        target = config.test_client_reminder_minutes
        if reminder_was_sent(booking, "client_reminder_1_sent_at"):
            if log_details and delta_minutes <= REMINDER_LOG_LOOKAHEAD_MINUTES:
                self._log_skip(booking.id, "client_reminder_1_sent_at already set")
            return
        if not is_reminder_due(delta_minutes, target):
            if log_details and delta_minutes <= REMINDER_LOG_LOOKAHEAD_MINUTES:
                self._log_skip(
                    booking.id,
                    "outside client test window",
                    starts_in=f"{delta_minutes:.1f}min",
                    target=f"{target}min",
                    window=reminder_window_label(target),
                )
            return
        logger.info("Sending test client reminder for booking_id=%s", booking.id)
        if await self._send_client_reminder(
            booking, client, client_lang, service_name, date_time, now, config, text_config, "client_1"
        ):
            booking.client_reminder_1_sent_at = now
            logger.info(
                "Sent test client reminder for booking_id=%s to telegram_id=%s",
                booking.id,
                client.telegram_id,
            )

    async def _maybe_send_client_reminders(
        self,
        booking: Booking,
        client: Client,
        client_lang: str,
        service_name: str,
        date_time: str,
        now: datetime,
        config: ReminderConfig,
        text_config,
        delta_minutes: float,
        *,
        log_details: bool,
    ) -> None:
        if delta_minutes <= config.client_reminder_2_minutes:
            if reminder_was_sent(booking, "client_reminder_2_sent_at"):
                if log_details and delta_minutes <= REMINDER_LOG_LOOKAHEAD_MINUTES:
                    self._log_skip(booking.id, "client_reminder_2_sent_at already set")
                return
            if not is_reminder_due(delta_minutes, config.client_reminder_2_minutes):
                if log_details and delta_minutes <= REMINDER_LOG_LOOKAHEAD_MINUTES:
                    self._log_skip(
                        booking.id,
                        "outside client reminder 2 window",
                        starts_in=f"{delta_minutes:.1f}min",
                        target=f"{config.client_reminder_2_minutes}min",
                    )
                return
            logger.info("Sending client reminder 2 for booking_id=%s", booking.id)
            if await self._send_client_reminder(
                booking, client, client_lang, service_name, date_time, now, config, text_config, "client_2"
            ):
                booking.client_reminder_2_sent_at = now
                logger.info(
                    "Sent client reminder 2 for booking_id=%s to telegram_id=%s",
                    booking.id,
                    client.telegram_id,
                )
            return

        if reminder_was_sent(booking, "client_reminder_1_sent_at"):
            if log_details and delta_minutes <= REMINDER_LOG_LOOKAHEAD_MINUTES:
                self._log_skip(booking.id, "client_reminder_1_sent_at already set")
            return
        if not is_reminder_due(delta_minutes, config.client_reminder_1_minutes):
            if log_details and delta_minutes <= REMINDER_LOG_LOOKAHEAD_MINUTES:
                self._log_skip(
                    booking.id,
                    "outside client reminder 1 window",
                    starts_in=f"{delta_minutes:.1f}min",
                    target=f"{config.client_reminder_1_minutes}min",
                )
            return
        logger.info("Sending client reminder 1 for booking_id=%s", booking.id)
        if await self._send_client_reminder(
            booking, client, client_lang, service_name, date_time, now, config, text_config, "client_1"
        ):
            booking.client_reminder_1_sent_at = now
            logger.info(
                "Sent client reminder 1 for booking_id=%s to telegram_id=%s",
                booking.id,
                client.telegram_id,
            )

    async def _maybe_send_admin_reminder(
        self,
        booking: Booking,
        service_name: str,
        date_time: str,
        now: datetime,
        config: ReminderConfig,
        delta_minutes: float,
        *,
        test_mode: bool,
        log_details: bool,
    ) -> None:
        if reminder_was_sent(booking, "admin_reminder_sent_at"):
            if log_details and delta_minutes <= REMINDER_LOG_LOOKAHEAD_MINUTES:
                self._log_skip(booking.id, "admin_reminder_sent_at already set")
            return

        threshold = config.test_admin_reminder_minutes if test_mode else config.admin_reminder_minutes
        if not is_reminder_due(delta_minutes, threshold):
            if log_details and delta_minutes <= REMINDER_LOG_LOOKAHEAD_MINUTES:
                self._log_skip(
                    booking.id,
                    "outside admin reminder window",
                    starts_in=f"{delta_minutes:.1f}min",
                    target=f"{threshold}min",
                    window=reminder_window_label(threshold),
                )
            return

        label = "test admin" if test_mode else "admin"
        logger.info("Sending %s reminder for booking_id=%s", label, booking.id)
        await self._send_admin_reminder_messages(
            booking, service_name, date_time, mark_sent=True, now=now
        )

    async def _send_admin_reminder_messages(
        self,
        booking: Booking,
        service_name: str,
        date_time: str,
        *,
        mark_sent: bool,
        now: datetime | None = None,
    ) -> bool:
        phone = booking.client_phone or t(self.settings.default_language, "phone_not_provided")
        sent_any = False
        for admin_id in self.settings.admin_ids:
            admin_lang = await get_user_language(admin_id)
            loc_block = (
                t(admin_lang, "reminder_admin_location", location=booking.location_text)
                if booking.location_text
                else ""
            )
            svc_loc_block = ""
            if booking.service_location_title:
                svc_loc_block = t(
                    admin_lang,
                    "reminder_admin_service_location",
                    title=booking.service_location_title,
                )
                if booking.service_location_address:
                    svc_loc_block += t(
                        admin_lang,
                        "reminder_admin_service_location_address",
                        address=booking.service_location_address,
                    )
            com_block = (
                t(admin_lang, "reminder_admin_comment", comment=booking.client_comment)
                if booking.client_comment
                else ""
            )
            text = t(
                admin_lang,
                "reminder_admin",
                service_name=service_name,
                date_time=date_time,
                client_name=booking.client_name,
                client_phone=phone,
                location_block=loc_block + svc_loc_block,
                comment_block=com_block,
            )
            if await self._notify(admin_id, text):
                sent_any = True
                logger.info(
                    "Sent admin reminder for booking_id=%s to admin_id=%s",
                    booking.id,
                    admin_id,
                )
        if sent_any and mark_sent and now is not None:
            booking.admin_reminder_sent_at = now
        return sent_any

    async def _send_client_reminder(
        self,
        booking: Booking,
        client: Client,
        client_lang: str,
        service_name: str,
        date_time: str,
        now: datetime,
        config: ReminderConfig,
        text_config,
        reminder_type: str,
    ) -> bool:
        use_attendance = config.attendance_confirmation_enabled
        if use_attendance:
            text = format_attendance_reminder_text(
                booking, service_name, date_time, client_lang, text_config, include_prompt=True
            )
            keyboard = attendance_reminder_keyboard(
                booking, client_lang, text_config, config, reminder_type
            )
        else:
            text = t(
                client_lang,
                "reminder_client",
                service_name=service_name,
                date_time=date_time,
            )
            keyboard = None

        try:
            await self.bot.send_message(
                client.telegram_id,
                text,
                reply_markup=keyboard,
            )
            return True
        except Exception:
            logger.exception(
                "Failed to send client reminder for booking_id=%s to telegram_id=%s",
                booking.id,
                client.telegram_id,
            )
            return False

    async def _notify(self, telegram_id: int, text: str) -> bool:
        try:
            await self.bot.send_message(telegram_id, text)
            return True
        except Exception:
            logger.exception("Failed to send reminder to telegram_id=%s", telegram_id)
            return False
