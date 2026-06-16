import re
from datetime import time

from app.bot.i18n import t, weekday_name
from app.models import WorkingBreak
from app.repositories import WorkingBreakRepository, WorkingHoursRepository

_TIME_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


def parse_hhmm(value: str) -> time:
    value = value.strip()
    match = _TIME_RE.match(value)
    if not match:
        raise ValueError("invalid_time")
    return time(int(match.group(1)), int(match.group(2)))


def validate_time_range(start: time, end: time) -> None:
    if start >= end:
        raise ValueError("invalid_range")


async def validate_break_for_day(
    working_hours_repo: WorkingHoursRepository,
    weekday: int,
    start: time,
    end: time,
) -> None:
    validate_time_range(start, end)
    wh = await working_hours_repo.get_by_day(weekday)
    if not wh:
        raise ValueError("day_off")
    if start < wh.start_time or end > wh.end_time:
        raise ValueError("outside_hours")


def format_break_line(br: WorkingBreak) -> str:
    time_part = f"{br.start_time:%H:%M}–{br.end_time:%H:%M}"
    if br.title:
        return f"🍽 {time_part} — {br.title}"
    return f"🍽 {time_part}"


def format_breaks_section(breaks: list[WorkingBreak], lang: str) -> str:
    if not breaks:
        return t(lang, "working_breaks_empty")
    return "\n".join(format_break_line(br) for br in breaks)


def format_breaks_summary(breaks: list[WorkingBreak], lang: str) -> str:
    if not breaks:
        return t(lang, "working_breaks_summary_none")
    parts = [f"{br.start_time:%H:%M}–{br.end_time:%H:%M}" for br in breaks]
    return f"{t(lang, 'working_breaks_summary_label')} {', '.join(parts)}"


async def breaks_by_weekday(
    break_repo: WorkingBreakRepository, *, active_only: bool = True
) -> dict[int, list[WorkingBreak]]:
    all_breaks = await break_repo.list_all(active_only=active_only)
    grouped: dict[int, list[WorkingBreak]] = {day: [] for day in range(7)}
    for br in all_breaks:
        grouped[br.weekday].append(br)
    return grouped


def format_schedule_day_with_breaks(
    lang: str,
    day: int,
    start: str,
    end: str,
    breaks: list[WorkingBreak],
) -> str:
    day_label = weekday_name(lang, day, short=True)
    breaks_summary = format_breaks_summary(breaks, lang)
    return f"{day_label}: {start}–{end} · {breaks_summary}"
