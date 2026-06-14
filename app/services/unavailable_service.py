from dataclasses import dataclass
from datetime import date, time, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import UnavailableRepository
from app.utils.datetime_utils import now_local

TIME_RANGE_PRESETS: list[tuple[time, time]] = [
    (time(9, 0), time(12, 0)),
    (time(12, 0), time(15, 0)),
    (time(15, 0), time(18, 0)),
    (time(18, 0), time(21, 0)),
]

DATE_PICKER_OFFSETS = tuple(range(7))


@dataclass(frozen=True)
class UnavailableItem:
    id: int
    kind: str
    target_date: date
    start_time: time | None = None
    end_time: time | None = None


async def block_full_day(session: AsyncSession, target_date: date) -> None:
    await UnavailableRepository(session).add_date(target_date)


async def block_time_range(
    session: AsyncSession, target_date: date, start_time: time, end_time: time
) -> None:
    await UnavailableRepository(session).add_time_range(target_date, start_time, end_time)


async def block_tomorrow(session: AsyncSession) -> date:
    target = now_local().date() + timedelta(days=1)
    await block_full_day(session, target)
    return target


async def block_next_7_days(session: AsyncSession) -> int:
    repo = UnavailableRepository(session)
    today = now_local().date()
    count = 0
    for offset in range(7):
        await repo.add_date(today + timedelta(days=offset))
        count += 1
    return count


async def list_upcoming_unavailable(session: AsyncSession) -> list[UnavailableItem]:
    repo = UnavailableRepository(session)
    today = now_local().date()
    items: list[UnavailableItem] = []
    for row in await repo.list_upcoming_dates(today):
        items.append(UnavailableItem(row.id, "date", row.target_date))
    for row in await repo.list_upcoming_time_ranges(today):
        items.append(
            UnavailableItem(row.id, "time", row.target_date, row.start_time, row.end_time)
        )
    items.sort(key=lambda item: (item.target_date, item.kind != "date", item.start_time or time.min))
    return items


async def delete_unavailable(session: AsyncSession, kind: str, item_id: int) -> bool:
    repo = UnavailableRepository(session)
    if kind == "date":
        return await repo.delete_date(item_id)
    if kind == "time":
        return await repo.delete_time_range(item_id)
    return False


async def is_date_unavailable(session: AsyncSession, target_date: date) -> bool:
    return await UnavailableRepository(session).is_date_unavailable(target_date)


def date_from_offset(offset: int) -> date:
    return now_local().date() + timedelta(days=offset)
