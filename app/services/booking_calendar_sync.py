"""Background Google Calendar sync — must not block Telegram callbacks."""

from __future__ import annotations

import logging
import time

from app.database.session import async_session_factory
from app.models import BookingStatus
from app.services.booking_service import BookingService
from app.services.calendar_service import CalendarService, log_calendar_failure
from app.utils.background_tasks import schedule_background_task
from app.utils.perf_logging import log_action_timing

logger = logging.getLogger(__name__)


async def _run_calendar_sync_create(booking_id: int) -> None:
    if CalendarService.is_auth_failed():
        logger.debug("Google Calendar sync skipped: auth disabled for runtime booking_id=%s", booking_id)
        return
    t_total = time.perf_counter()
    t_calendar = 0.0
    try:
        async with async_session_factory() as session:
            service = BookingService(session)
            booking = await service.booking_repo.get_by_id(booking_id)
            if not booking or booking.status != BookingStatus.CONFIRMED:
                return
            t0 = time.perf_counter()
            await service.sync_calendar_for_booking(booking)
            t_calendar = time.perf_counter() - t0
    except Exception as exc:
        log_calendar_failure(logger, "background sync", exc, booking_id=booking_id)
        return
    log_action_timing(
        "google calendar sync",
        booking_id=booking_id,
        calendar=t_calendar,
        total=time.perf_counter() - t_total,
    )


async def _run_calendar_sync_update(booking_id: int) -> None:
    if CalendarService.is_auth_failed():
        logger.debug("Google Calendar update skipped: auth disabled for runtime booking_id=%s", booking_id)
        return
    t_total = time.perf_counter()
    t_calendar = 0.0
    try:
        async with async_session_factory() as session:
            service = BookingService(session)
            booking = await service.booking_repo.get_by_id(booking_id)
            if not booking or booking.status != BookingStatus.CONFIRMED:
                return
            t0 = time.perf_counter()
            await service.update_calendar_for_booking(booking)
            t_calendar = time.perf_counter() - t0
    except Exception as exc:
        log_calendar_failure(logger, "background update", exc, booking_id=booking_id)
        return
    log_action_timing(
        "google calendar update",
        booking_id=booking_id,
        calendar=t_calendar,
        total=time.perf_counter() - t_total,
    )


async def _run_calendar_sync_delete(booking_id: int, event_id: str) -> None:
    if CalendarService.is_auth_failed():
        logger.debug(
            "Google Calendar delete skipped: auth disabled for runtime booking_id=%s",
            booking_id,
        )
        return
    t_total = time.perf_counter()
    t_calendar = 0.0
    try:
        async with async_session_factory() as session:
            service = BookingService(session)
            t0 = time.perf_counter()
            await service.delete_calendar_event(event_id)
            t_calendar = time.perf_counter() - t0
    except Exception as exc:
        log_calendar_failure(logger, "background delete", exc, booking_id=booking_id)
        return
    log_action_timing(
        "google calendar delete",
        booking_id=booking_id,
        calendar=t_calendar,
        total=time.perf_counter() - t_total,
    )


def schedule_calendar_sync_create(booking_id: int) -> None:
    schedule_background_task(
        _run_calendar_sync_create(booking_id),
        f"calendar_sync_create:{booking_id}",
    )


def schedule_calendar_sync_update(booking_id: int) -> None:
    schedule_background_task(
        _run_calendar_sync_update(booking_id),
        f"calendar_sync_update:{booking_id}",
    )


def schedule_calendar_sync_delete(booking_id: int, event_id: str) -> None:
    schedule_background_task(
        _run_calendar_sync_delete(booking_id, event_id),
        f"calendar_sync_delete:{booking_id}",
    )
