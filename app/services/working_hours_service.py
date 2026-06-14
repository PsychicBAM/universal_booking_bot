from dataclasses import dataclass
from datetime import date, time, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import WorkingHours
from app.repositories import UnavailableRepository, WorkingHoursRepository
from app.utils.datetime_utils import now_local


@dataclass(frozen=True)
class DaySchedule:
    day_of_week: int
    is_working: bool
    start_time: time | None = None
    end_time: time | None = None


DAY_TIME_PRESETS: list[tuple[time, time]] = [
    (time(9, 0), time(18, 0)),
    (time(10, 0), time(19, 0)),
    (time(10, 0), time(20, 0)),
    (time(8, 0), time(17, 0)),
    (time(12, 0), time(20, 0)),
]

WEEKLY_PRESET_KEYS = (
    "monfri_9_18",
    "monfri_10_19",
    "everyday_10_20",
    "satsun_off",
    "everyday_off",
)


async def get_weekly_schedule(session: AsyncSession) -> list[DaySchedule]:
    repo = WorkingHoursRepository(session)
    schedules: list[DaySchedule] = []
    for day in range(7):
        row = await repo.get_day_row(day)
        if row and row.is_active:
            schedules.append(DaySchedule(day, True, row.start_time, row.end_time))
        else:
            schedules.append(DaySchedule(day, False))
    return schedules


async def get_day_schedule(session: AsyncSession, day: int) -> DaySchedule:
    schedules = await get_weekly_schedule(session)
    return schedules[day]


async def set_day_working_hours(
    session: AsyncSession, day: int, start_time: time, end_time: time
) -> None:
    await WorkingHoursRepository(session).upsert_day(day, start_time, end_time)


async def set_day_off(session: AsyncSession, day: int) -> None:
    await WorkingHoursRepository(session).disable_day(day)


async def toggle_day(session: AsyncSession, day: int) -> DaySchedule:
    schedule = await get_day_schedule(session, day)
    if schedule.is_working:
        await set_day_off(session, day)
        return DaySchedule(day, False)
    await set_day_working_hours(session, day, time(9, 0), time(18, 0))
    return await get_day_schedule(session, day)


async def apply_weekly_preset(session: AsyncSession, preset_key: str) -> None:
    repo = WorkingHoursRepository(session)
    if preset_key == "monfri_9_18":
        for day in range(5):
            await repo.upsert_day(day, time(9, 0), time(18, 0))
        for day in (5, 6):
            await repo.disable_day(day)
    elif preset_key == "monfri_10_19":
        for day in range(5):
            await repo.upsert_day(day, time(10, 0), time(19, 0))
        for day in (5, 6):
            await repo.disable_day(day)
    elif preset_key == "everyday_10_20":
        for day in range(7):
            await repo.upsert_day(day, time(10, 0), time(20, 0))
    elif preset_key == "satsun_off":
        for day in (5, 6):
            await repo.disable_day(day)
    elif preset_key == "everyday_off":
        for day in range(7):
            await repo.disable_day(day)


async def make_next_7_days_unavailable(session: AsyncSession) -> int:
    repo = UnavailableRepository(session)
    today = now_local().date()
    count = 0
    for offset in range(7):
        await repo.add_date(today + timedelta(days=offset))
        count += 1
    return count
