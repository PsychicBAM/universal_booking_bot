import logging
from datetime import datetime

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.i18n import t
from app.config import get_settings
from app.database.session import async_session_factory
from app.models import Booking, Client
from app.repositories import BookingRepository, ServiceRepository
from app.services.language_service import get_user_language
from app.services.reminder_settings import ReminderConfig, load_reminder_config
from app.utils.datetime_utils import now_local, to_local_naive
from app.utils.formatting import format_datetime

logger = logging.getLogger(__name__)


class ReminderService:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.settings = get_settings()

    async def process_reminders(self) -> None:
        async with async_session_factory() as session:
            config = await load_reminder_config(session)
            if not config.enabled:
                return

            now = now_local()
            bookings = await BookingRepository(session).list_for_reminders(now)
            for booking in bookings:
                await self._process_booking_reminders(session, booking, now, config)

            await session.commit()

    async def _process_booking_reminders(
        self,
        session: AsyncSession,
        booking: Booking,
        now: datetime,
        config: ReminderConfig,
    ) -> None:
        start_at = to_local_naive(booking.start_at)
        delta_minutes = (start_at - now).total_seconds() / 60
        if delta_minutes <= 0:
            return

        client = await session.get(Client, booking.client_id)
        if not client:
            return

        service = await ServiceRepository(session).get_by_id(booking.service_id)
        service_name = service.name if service else f"#{booking.service_id}"
        date_time = format_datetime(start_at)
        client_lang = client.language or self.settings.default_language

        if config.test_mode:
            await self._maybe_send_client_test_reminder(
                booking, client, client_lang, service_name, date_time, now, config, delta_minutes
            )
            await self._maybe_send_admin_reminder(
                booking,
                service_name,
                date_time,
                now,
                config,
                delta_minutes,
                test_mode=True,
            )
            return

        await self._maybe_send_client_reminders(
            booking, client, client_lang, service_name, date_time, now, config, delta_minutes
        )
        await self._maybe_send_admin_reminder(
            booking,
            service_name,
            date_time,
            now,
            config,
            delta_minutes,
            test_mode=False,
        )

    async def _maybe_send_client_test_reminder(
        self,
        booking: Booking,
        client: Client,
        client_lang: str,
        service_name: str,
        date_time: str,
        now: datetime,
        config: ReminderConfig,
        delta_minutes: float,
    ) -> None:
        if booking.client_reminder_1_sent_at is not None:
            return
        if delta_minutes > config.test_client_reminder_minutes:
            return
        text = t(
            client_lang,
            "reminder_client",
            service_name=service_name,
            date_time=date_time,
        )
        if await self._notify(client.telegram_id, text):
            booking.client_reminder_1_sent_at = now
            logger.info(
                "Sent test client reminder for booking %s to %s",
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
        delta_minutes: float,
    ) -> None:
        if delta_minutes <= config.client_reminder_2_minutes:
            if booking.client_reminder_2_sent_at is None and delta_minutes > 0:
                text = t(
                    client_lang,
                    "reminder_client",
                    service_name=service_name,
                    date_time=date_time,
                )
                if await self._notify(client.telegram_id, text):
                    booking.client_reminder_2_sent_at = now
                    logger.info(
                        "Sent client reminder 2 for booking %s to %s",
                        booking.id,
                        client.telegram_id,
                    )
            return

        if (
            booking.client_reminder_1_sent_at is None
            and delta_minutes <= config.client_reminder_1_minutes
            and delta_minutes > 0
        ):
            text = t(
                client_lang,
                "reminder_client",
                service_name=service_name,
                date_time=date_time,
            )
            if await self._notify(client.telegram_id, text):
                booking.client_reminder_1_sent_at = now
                logger.info(
                    "Sent client reminder 1 for booking %s to %s",
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
    ) -> None:
        if booking.admin_reminder_sent_at is not None:
            return

        threshold = (
            config.test_admin_reminder_minutes if test_mode else config.admin_reminder_minutes
        )
        if delta_minutes > threshold or delta_minutes <= 0:
            return

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
                    "Sent admin reminder for booking %s to admin %s",
                    booking.id,
                    admin_id,
                )
        if sent_any:
            booking.admin_reminder_sent_at = now

    async def _notify(self, telegram_id: int, text: str) -> bool:
        try:
            await self.bot.send_message(telegram_id, text)
            return True
        except Exception:
            logger.exception("Failed to send reminder to %s", telegram_id)
            return False
