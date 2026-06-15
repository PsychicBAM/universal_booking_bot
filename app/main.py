import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.bot.handlers import admin, booking_edit, cancel, client, common, service_locations, service_media, start, support
from app.bot.handlers import settings as settings_handlers
from app.bot.handlers import start_screen_settings
from app.bot.handlers import unavailable
from app.bot.handlers import working_hours
from app.bot.middlewares import AdminMiddleware, LanguageMiddleware
from app.bot.middlewares.clear_menu_fsm import ClearMenuFsmMiddleware
from app.config import get_settings
from app.database.session import init_db
from app.services.reminder_service import ReminderService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def seed_default_working_hours() -> None:
    from datetime import time

    from app.database.session import async_session_factory
    from app.repositories import WorkingHoursRepository

    async with async_session_factory() as session:
        repo = WorkingHoursRepository(session)
        existing = await repo.list_all()
        if existing:
            return
        for day in range(5):
            await repo.upsert_day(day, time(9, 0), time(18, 0))
        await session.commit()
        logger.info("Default working hours seeded (Mon-Fri 09:00-18:00)")


async def main() -> None:
    settings = get_settings()
    if not settings.bot_token or settings.bot_token.startswith("{{"):
        logger.error("BOT_TOKEN is not set. Copy .env.example to .env and configure it.")
        sys.exit(1)

    if settings.database_url.startswith("sqlite"):
        db_path = settings.database_url.split("///")[-1]
        os.makedirs(os.path.dirname(db_path) or "data", exist_ok=True)

    await init_db()
    await seed_default_working_hours()

    from app.services.language_service import init_language_cache

    await init_language_cache()

    from app.database.session import async_session_factory
    from app.services.calendar_service import CalendarService

    async with async_session_factory() as session:
        await CalendarService(session).log_startup_status()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.message.middleware(ClearMenuFsmMiddleware())
    dp.message.middleware(AdminMiddleware())
    dp.callback_query.middleware(AdminMiddleware())
    dp.message.middleware(LanguageMiddleware())
    dp.callback_query.middleware(LanguageMiddleware())

    dp.include_router(cancel.router)
    dp.include_router(start.router)
    dp.include_router(working_hours.router)
    dp.include_router(unavailable.router)
    dp.include_router(start_screen_settings.router)
    dp.include_router(settings_handlers.router)
    dp.include_router(service_media.router)
    dp.include_router(service_locations.router)
    dp.include_router(booking_edit.router)
    dp.include_router(support.router)
    dp.include_router(client.router)
    dp.include_router(admin.router)
    dp.include_router(common.router)

    scheduler = AsyncIOScheduler()
    reminder_service = ReminderService(bot)
    scheduler.add_job(reminder_service.process_reminders, "interval", minutes=1)
    scheduler.start()

    logger.info("Universal booking bot started")
    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown(wait=False)
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
