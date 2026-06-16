"""Group booking slots into morning / day / evening periods."""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Literal

from app.bot.i18n import t
from app.utils.formatting import format_date

Period = Literal["morning", "day", "evening"]

PERIOD_ORDER: tuple[Period, ...] = ("morning", "day", "evening")


def slot_period(slot: datetime) -> Period:
    slot_time = slot.time()
    if time(5, 0) <= slot_time <= time(11, 59, 59):
        return "morning"
    if time(12, 0) <= slot_time <= time(17, 59, 59):
        return "day"
    return "evening"


def group_slots_by_period(slots: list[datetime]) -> dict[Period, list[datetime]]:
    grouped: dict[Period, list[datetime]] = {period: [] for period in PERIOD_ORDER}
    for slot in slots:
        grouped[slot_period(slot)].append(slot)
    return grouped


def non_empty_periods(grouped: dict[Period, list[datetime]]) -> list[Period]:
    return [period for period in PERIOD_ORDER if grouped[period]]


def build_period_screen_text(
    target_date: date,
    grouped: dict[Period, list[datetime]],
    lang: str,
) -> str:
    lines = [
        f"📅 {format_date(target_date)}",
        "",
        t(lang, "booking_choose_time_period"),
        "",
    ]
    for period in PERIOD_ORDER:
        count = len(grouped[period])
        if count:
            lines.append(
                f"{t(lang, f'booking_period_{period}')} — "
                f"{t(lang, 'booking_slots_count', count=count)}"
            )
    return "\n".join(lines)


def build_time_grid_text(target_date: date, period: Period, lang: str) -> str:
    return "\n".join(
        [
            t(lang, f"booking_period_{period}"),
            f"📅 {format_date(target_date)}",
            t(lang, "booking_choose_time_in_period"),
        ]
    )
