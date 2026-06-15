"""Serialize booking create/reschedule for SQLite MVP.

Lock scope: one calendar day (all services). Overlap checks are global across
services; the day lock prevents concurrent inserts that could bypass availability.

For PostgreSQL production: prefer row-level locking (SELECT … FOR UPDATE) or an
exclusion constraint on tstzrange(start_at, end_at) for active statuses.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import date

logger = logging.getLogger(__name__)


class BookingLockManager:
    def __init__(self) -> None:
        self._locks: dict[str, asyncio.Lock] = {}
        self._registry_lock = asyncio.Lock()

    def _key_for_day(self, target_date: date) -> str:
        return f"booking:{target_date.isoformat()}"

    async def _get_lock(self, key: str) -> asyncio.Lock:
        async with self._registry_lock:
            lock = self._locks.get(key)
            if lock is None:
                lock = asyncio.Lock()
                self._locks[key] = lock
            return lock

    @asynccontextmanager
    async def hold(self, target_date: date) -> AsyncIterator[str]:
        key = self._key_for_day(target_date)
        lock = await self._get_lock(key)
        logger.info("Booking lock waiting: %s", key)
        async with lock:
            logger.info("Booking lock acquired: %s", key)
            try:
                yield key
            finally:
                logger.info("Booking lock released: %s", key)


booking_lock_manager = BookingLockManager()
