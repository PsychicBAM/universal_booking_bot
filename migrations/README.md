"""Initial schema is created via SQLAlchemy metadata in app.database.session.init_db.

SQLite additive migrations run in app.database.session._migrate_sqlite_columns().

## Booking slot safety

SQLite MVP uses:
- asyncio day-lock (`app.services.booking_lock`)
- final overlap check in `BookingService._assert_slot_available_for_write()`
- optional partial unique index `idx_bookings_active_slot` (skipped if duplicates already exist)

## PostgreSQL (future)

Prefer one or more of:
- `SELECT … FOR UPDATE` on overlapping bookings inside a transaction
- `EXCLUDE USING gist` on `tstzrange(start_at, end_at)` for active statuses
- partial unique index on `(service_id, start_at) WHERE status IN ('pending','confirmed')`

Run `python scripts/find_duplicate_bookings.py` before adding constraints on existing data.

"""
