from datetime import datetime
from zoneinfo import ZoneInfo

from app.config import get_settings


def get_tz() -> ZoneInfo:
    return ZoneInfo(get_settings().timezone)


def now_local() -> datetime:
    """Current local time as naive datetime (TIMEZONE from .env)."""
    return datetime.now(get_tz()).replace(tzinfo=None)


def to_local_naive(dt: datetime) -> datetime:
    """Convert any datetime to local naive for DB storage and comparisons."""
    if dt.tzinfo is None:
        normalized = dt
    else:
        normalized = dt.astimezone(get_tz()).replace(tzinfo=None)
    return normalized.replace(second=0, microsecond=0)


def to_aware_local(dt: datetime) -> datetime:
    """Convert DB naive local datetime to timezone-aware for Google Calendar."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=get_tz())
    return dt.astimezone(get_tz())


def normalize_slot(dt: datetime) -> datetime:
    return to_local_naive(dt)


def slots_match(a: datetime, b: datetime) -> bool:
    return normalize_slot(a) == normalize_slot(b)


def slot_from_timestamp(ts: int) -> datetime:
    return to_local_naive(datetime.fromtimestamp(ts, tz=get_tz()))


def slot_to_callback(dt: datetime) -> str:
    return str(int(to_aware_local(dt).timestamp()))


def local_timestamp(dt: datetime) -> int:
    """Epoch seconds for a DB/local naive datetime in configured TIMEZONE."""
    return int(to_aware_local(to_local_naive(dt)).timestamp())
