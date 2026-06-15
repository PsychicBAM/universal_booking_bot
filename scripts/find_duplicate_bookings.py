#!/usr/bin/env python3
"""Report duplicate or overlapping active bookings (pending/confirmed). Does not delete."""

from __future__ import annotations

import asyncio
import sys
from collections import defaultdict
from datetime import timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import select

from app.database.session import async_session_factory
from app.models import Booking, BookingStatus
from app.repositories import ServiceRepository
from app.utils.datetime_utils import to_local_naive


async def main() -> int:
    async with async_session_factory() as session:
        result = await session.execute(
            select(Booking)
            .where(Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]))
            .order_by(Booking.start_at, Booking.id)
        )
        bookings = list(result.scalars().all())
        buffer_map = await ServiceRepository(session).buffer_minutes_by_id()

    if not bookings:
        print("No active bookings found.")
        return 0

    print(f"Active bookings: {len(bookings)}\n")

    exact: dict[tuple[int, str], list[Booking]] = defaultdict(list)
    for booking in bookings:
        start = to_local_naive(booking.start_at)
        exact[(booking.service_id, start.isoformat())].append(booking)

    exact_dupes = {k: v for k, v in exact.items() if len(v) > 1}
    if exact_dupes:
        print("=== Exact duplicate slots (same service_id + start_at) ===")
        for (service_id, start_iso), group in sorted(exact_dupes.items()):
            ids = ", ".join(f"#{b.id}" for b in group)
            statuses = ", ".join(b.status.value for b in group)
            print(f"  service_id={service_id} start_at={start_iso} bookings=[{ids}] statuses=[{statuses}]")
    else:
        print("=== Exact duplicate slots: none ===")

    overlaps: list[tuple[Booking, Booking]] = []
    for i, a in enumerate(bookings):
        a_start = to_local_naive(a.start_at)
        a_end = to_local_naive(a.end_at) + timedelta(minutes=buffer_map.get(a.service_id, 0))
        for b in bookings[i + 1 :]:
            b_start = to_local_naive(b.start_at)
            b_end = to_local_naive(b.end_at) + timedelta(minutes=buffer_map.get(b.service_id, 0))
            if a_start < b_end and b_start < a_end:
                overlaps.append((a, b))

    print()
    if overlaps:
        print("=== Overlapping active bookings (incl. buffer) ===")
        for a, b in overlaps:
            print(
                f"  #{a.id} (service {a.service_id}, {to_local_naive(a.start_at)}) "
                f"<-> #{b.id} (service {b.service_id}, {to_local_naive(b.start_at)})"
            )
    else:
        print("=== Overlapping active bookings: none ===")

    if exact_dupes or overlaps:
        print("\nNo records were modified. Cancel or archive duplicates manually in admin.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
