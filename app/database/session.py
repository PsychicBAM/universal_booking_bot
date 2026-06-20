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
        client_new_cols = (
            ("first_name", "VARCHAR(255)"),
            ("last_name", "VARCHAR(255)"),
            ("username", "VARCHAR(255)"),
            ("language_code", "VARCHAR(16)"),
            ("full_name", "VARCHAR(255)"),
            ("phone_source", "VARCHAR(32)"),
            ("phone_updated_at", "DATETIME"),
            ("last_seen_at", "DATETIME"),
        )
        result = await conn.exec_driver_sql("PRAGMA table_info(clients)")
        client_columns = {row[1] for row in result.fetchall()}
        for col, col_type in client_new_cols:
            if col not in client_columns:
                await conn.exec_driver_sql(f"ALTER TABLE clients ADD COLUMN {col} {col_type}")
        if "phone" not in client_columns:
            await conn.exec_driver_sql("ALTER TABLE clients ADD COLUMN phone VARCHAR(50)")

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
        if "ask_client_comment" not in service_columns:
            await conn.exec_driver_sql(
                "ALTER TABLE services ADD COLUMN ask_client_comment BOOLEAN NOT NULL DEFAULT 0"
            )
        if "show_media_to_clients" not in service_columns:
            await conn.exec_driver_sql(
                "ALTER TABLE services ADD COLUMN show_media_to_clients BOOLEAN NOT NULL DEFAULT 1"
            )
        if "service_type" not in service_columns:
            await conn.exec_driver_sql(
                "ALTER TABLE services ADD COLUMN service_type VARCHAR(20) NOT NULL DEFAULT 'booking'"
            )

        result = await conn.exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='service_orders'"
        )
        if result.fetchone():
            result = await conn.exec_driver_sql("PRAGMA table_info(service_orders)")
            order_columns = {row[1] for row in result.fetchall()}
            order_new_cols = (
                ("decline_reason", "TEXT"),
                ("accepted_at", "DATETIME"),
                ("accepted_by_admin_id", "INTEGER"),
                ("declined_at", "DATETIME"),
                ("declined_by_admin_id", "INTEGER"),
            )
            for col, col_type in order_new_cols:
                if col not in order_columns:
                    await conn.exec_driver_sql(f"ALTER TABLE service_orders ADD COLUMN {col} {col_type}")

        result = await conn.exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='order_messages'"
        )
        if not result.fetchone():
            await conn.exec_driver_sql(
                """
                CREATE TABLE order_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    sender_type VARCHAR(16) NOT NULL,
                    sender_telegram_id INTEGER,
                    message_text TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(order_id) REFERENCES service_orders(id)
                )
                """
            )
            await conn.exec_driver_sql(
                "CREATE INDEX IF NOT EXISTS ix_order_messages_order_id ON order_messages (order_id)"
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
        attendance_cols = (
            ("attendance_status", "VARCHAR(32)"),
            ("attendance_responded_at", "DATETIME"),
            ("attendance_reason", "TEXT"),
            ("attendance_reminder_type", "VARCHAR(16)"),
        )
        for col, col_type in attendance_cols:
            if col not in booking_columns:
                await conn.exec_driver_sql(f"ALTER TABLE bookings ADD COLUMN {col} {col_type}")

        result = await conn.exec_driver_sql("PRAGMA table_info(bookings)")
        booking_columns = {row[1] for row in result.fetchall()}
        manual_att_cols = (
            ("attendance_manual_sent_at", "DATETIME"),
            ("attendance_manual_sent_by_admin_id", "INTEGER"),
            ("attendance_manual_sent_count", "INTEGER NOT NULL DEFAULT 0"),
        )
        for col, col_type in manual_att_cols:
            if col not in booking_columns:
                await conn.exec_driver_sql(f"ALTER TABLE bookings ADD COLUMN {col} {col_type}")

        result = await conn.exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='support_messages'"
        )
        if result.fetchone():
            result = await conn.exec_driver_sql("PRAGMA table_info(support_messages)")
            support_columns = {row[1] for row in result.fetchall()}
            if "topic" not in support_columns:
                await conn.exec_driver_sql("ALTER TABLE support_messages ADD COLUMN topic VARCHAR(50)")
            if "booking_id" not in support_columns:
                await conn.exec_driver_sql("ALTER TABLE support_messages ADD COLUMN booking_id INTEGER")

    await _maybe_add_booking_slot_unique_index()


async def _maybe_add_booking_slot_unique_index() -> None:
    """Partial unique index for active exact slot duplicates. Skipped if duplicates exist."""
    import logging

    log = logging.getLogger(__name__)
    if "sqlite" not in settings.database_url:
        log.info(
            "PostgreSQL: consider EXCLUDE constraint or SELECT FOR UPDATE on bookings for slot safety"
        )
        return

    async with engine.begin() as conn:
        index_check = await conn.exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_bookings_active_slot'"
        )
        if index_check.fetchone():
            return

        from collections import defaultdict

        from app.utils.datetime_utils import normalize_slot

        dupes = await conn.exec_driver_sql(
            """
            SELECT id, service_id, start_at
            FROM bookings
            WHERE status IN ('pending', 'confirmed')
            """
        )
        counts: dict[tuple[int, str], int] = defaultdict(int)
        for row in dupes.fetchall():
            _id, service_id, start_raw = row[0], row[1], row[2]
            if start_raw is None:
                continue
            if isinstance(start_raw, str):
                from datetime import datetime as dt_cls

                try:
                    parsed = dt_cls.fromisoformat(start_raw.replace("Z", "+00:00"))
                except ValueError:
                    continue
            else:
                parsed = start_raw
            key = (service_id, normalize_slot(parsed).isoformat())
            counts[key] += 1

        if any(count > 1 for count in counts.values()):
            log.warning(
                "Skipping idx_bookings_active_slot: duplicate slot group(s) exist. "
                "Run: python scripts/find_duplicate_bookings.py",
            )
            return

        await conn.exec_driver_sql(
            """
            CREATE UNIQUE INDEX idx_bookings_active_slot
            ON bookings (service_id, start_at)
            WHERE status IN ('pending', 'confirmed')
            """
        )
        log.info("Created partial unique index idx_bookings_active_slot")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
