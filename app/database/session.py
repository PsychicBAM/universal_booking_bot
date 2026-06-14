from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.database.base import Base

settings = get_settings()

engine = create_async_engine(settings.database_url, echo=False)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    import app.models  # noqa: F401 — register models with Base.metadata

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await _migrate_sqlite_columns()


async def _migrate_sqlite_columns() -> None:
    """Add new columns to existing SQLite DBs without Alembic."""
    if "sqlite" not in settings.database_url:
        return
    async with engine.begin() as conn:
        result = await conn.exec_driver_sql("PRAGMA table_info(clients)")
        client_columns = {row[1] for row in result.fetchall()}
        if "language" not in client_columns:
            default_lang = settings.default_language
            await conn.exec_driver_sql(
                f"ALTER TABLE clients ADD COLUMN language VARCHAR(5) DEFAULT '{default_lang}'"
            )

        result = await conn.exec_driver_sql("PRAGMA table_info(bookings)")
        booking_columns = {row[1] for row in result.fetchall()}
        reminder_datetime_cols = (
            "client_reminder_1_sent_at",
            "client_reminder_2_sent_at",
            "admin_reminder_sent_at",
        )
        for col in reminder_datetime_cols:
            if col not in booking_columns:
                await conn.exec_driver_sql(f"ALTER TABLE bookings ADD COLUMN {col} DATETIME")

        if "reminder_24h_sent" in booking_columns:
            await conn.exec_driver_sql(
                "UPDATE bookings SET client_reminder_1_sent_at = datetime('now') "
                "WHERE client_reminder_1_sent_at IS NULL AND reminder_24h_sent = 1"
            )
        if "reminder_2h_sent" in booking_columns:
            await conn.exec_driver_sql(
                "UPDATE bookings SET client_reminder_2_sent_at = datetime('now') "
                "WHERE client_reminder_2_sent_at IS NULL AND reminder_2h_sent = 1"
            )
        if "admin_reminder_sent" in booking_columns:
            await conn.exec_driver_sql(
                "UPDATE bookings SET admin_reminder_sent_at = datetime('now') "
                "WHERE admin_reminder_sent_at IS NULL AND admin_reminder_sent = 1"
            )

        result = await conn.exec_driver_sql("PRAGMA table_info(services)")
        service_columns = {row[1] for row in result.fetchall()}
        if "archived_at" not in service_columns:
            await conn.exec_driver_sql("ALTER TABLE services ADD COLUMN archived_at DATETIME")
        if "buffer_after_minutes" not in service_columns:
            await conn.exec_driver_sql(
                "ALTER TABLE services ADD COLUMN buffer_after_minutes INTEGER NOT NULL DEFAULT 0"
            )
        if "requires_location" not in service_columns:
            await conn.exec_driver_sql(
                "ALTER TABLE services ADD COLUMN requires_location BOOLEAN NOT NULL DEFAULT 0"
            )
        if "show_media_to_clients" not in service_columns:
            await conn.exec_driver_sql(
                "ALTER TABLE services ADD COLUMN show_media_to_clients BOOLEAN NOT NULL DEFAULT 1"
            )

        result = await conn.exec_driver_sql("PRAGMA table_info(bookings)")
        booking_columns = {row[1] for row in result.fetchall()}
        if "location_text" not in booking_columns:
            await conn.exec_driver_sql("ALTER TABLE bookings ADD COLUMN location_text TEXT")
        if "client_comment" not in booking_columns:
            await conn.exec_driver_sql("ALTER TABLE bookings ADD COLUMN client_comment TEXT")
        if "service_location_id" not in booking_columns:
            await conn.exec_driver_sql("ALTER TABLE bookings ADD COLUMN service_location_id INTEGER")
        if "service_location_title" not in booking_columns:
            await conn.exec_driver_sql("ALTER TABLE bookings ADD COLUMN service_location_title VARCHAR(255)")
        if "service_location_address" not in booking_columns:
            await conn.exec_driver_sql("ALTER TABLE bookings ADD COLUMN service_location_address TEXT")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
