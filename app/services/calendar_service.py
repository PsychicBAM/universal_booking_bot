import logging
import asyncio
import time as perf_time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.repositories import SettingsRepository
from app.utils.datetime_utils import now_local, to_aware_local, to_local_naive

logger = logging.getLogger(__name__)

_busy_ranges_cache: dict[tuple[str, str, str], tuple[float, list[tuple[datetime, datetime]]]] = {}
_calendar_auth_failed = False
_calendar_auth_warned = False


@dataclass(frozen=True)
class CalendarTestResult:
    ok: bool
    message_key: str
    missing: tuple[str, ...] = ()
    detail: str | None = None


def _is_blank_or_placeholder(value: str | None) -> bool:
    if not value:
        return True
    stripped = value.strip()
    return not stripped or stripped.startswith("{{")


class CalendarService:
    """Optional Google Calendar integration. No-op when disabled or misconfigured."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.settings = get_settings()
        self.settings_repo = SettingsRepository(session)

    @staticmethod
    def is_auth_failed() -> bool:
        return _calendar_auth_failed

    @staticmethod
    def _is_refresh_token_error(exc: Exception) -> bool:
        try:
            from google.auth.exceptions import RefreshError

            if isinstance(exc, RefreshError):
                message = str(exc).lower()
                return any(token in message for token in ("invalid_grant", "expired", "revoked"))
        except ImportError:
            pass
        return False

    @staticmethod
    def _mark_auth_failed(action: str) -> None:
        global _calendar_auth_failed, _calendar_auth_warned
        _calendar_auth_failed = True
        if not _calendar_auth_warned:
            _calendar_auth_warned = True
            logger.warning(
                "Google Calendar token expired or revoked. "
                "Re-authorize Google Calendar or disable GOOGLE_CALENDAR_ENABLED. "
                "Booking remains saved."
            )
        else:
            logger.debug(
                "Google Calendar disabled for this runtime due to expired/revoked token (%s)",
                action,
            )

    @property
    def env_enabled(self) -> bool:
        return self.settings.google_calendar_enabled

    async def is_enabled(self) -> bool:
        """Effective sync: env flag AND admin DB toggle."""
        if _calendar_auth_failed:
            return False
        if not self.env_enabled:
            return False
        cal = await self.settings_repo.get_calendar_settings()
        return cal.google_calendar_enabled

    async def get_missing_credentials(self) -> list[str]:
        refresh_token = await self._get_refresh_token()
        missing: list[str] = []
        if _is_blank_or_placeholder(self.settings.google_client_id):
            missing.append("GOOGLE_CLIENT_ID")
        if _is_blank_or_placeholder(self.settings.google_client_secret):
            missing.append("GOOGLE_CLIENT_SECRET")
        if _is_blank_or_placeholder(refresh_token):
            missing.append("GOOGLE_REFRESH_TOKEN")
        return missing

    async def log_startup_status(self) -> None:
        if not self.env_enabled:
            logger.info("Google Calendar: disabled (GOOGLE_CALENDAR_ENABLED=false)")
            return
        missing = await self.get_missing_credentials()
        if missing:
            logger.warning(
                "Google Calendar is enabled but credentials are missing: %s",
                ", ".join(missing),
            )
            return
        db_enabled = (await self.settings_repo.get_calendar_settings()).google_calendar_enabled
        if db_enabled:
            logger.info("Google Calendar: enabled and configured")
        else:
            logger.info(
                "Google Calendar: configured in .env but sync is off in admin settings"
            )

    def _get_credentials(self, refresh_token: str | None) -> Any | None:
        token = refresh_token
        if _is_blank_or_placeholder(token):
            return None
        if _is_blank_or_placeholder(self.settings.google_client_id):
            return None
        if _is_blank_or_placeholder(self.settings.google_client_secret):
            return None
        try:
            from google.oauth2.credentials import Credentials
        except ImportError:
            logger.warning(
                "Google Calendar packages not installed. pip install google-api-python-client"
            )
            return None
        return Credentials(
            token=None,
            refresh_token=token.strip(),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.settings.google_client_id.strip(),
            client_secret=self.settings.google_client_secret.strip(),
        )

    async def _get_calendar_id(self) -> str:
        cal = await self.settings_repo.get_calendar_settings()
        calendar_id = cal.google_calendar_id or self.settings.google_calendar_id
        return calendar_id.strip() or "primary"

    async def _get_refresh_token(self) -> str | None:
        cal = await self.settings_repo.get_calendar_settings()
        db_token = cal.google_refresh_token
        if db_token and not _is_blank_or_placeholder(db_token):
            return db_token.strip()
        env_token = self.settings.google_refresh_token
        if env_token and not _is_blank_or_placeholder(env_token):
            return env_token.strip()
        return None

    def _build_service(self, refresh_token: str | None) -> Any | None:
        creds = self._get_credentials(refresh_token)
        if not creds:
            return None
        try:
            from googleapiclient.discovery import build
        except ImportError:
            logger.warning("Google Calendar packages not installed.")
            return None
        try:
            return build("calendar", "v3", credentials=creds, cache_discovery=False)
        except Exception:
            logger.exception("Failed to build Google Calendar client")
            return None

    def _log_api_error(self, action: str, exc: Exception) -> None:
        if _calendar_auth_failed:
            logger.debug("Google Calendar %s skipped: auth disabled for runtime", action)
            return
        if self._is_refresh_token_error(exc):
            self._mark_auth_failed(action)
            return
        try:
            from googleapiclient.errors import HttpError

            if isinstance(exc, HttpError):
                status = exc.resp.status if exc.resp else "?"
                if status == 401:
                    logger.error(
                        "Google Calendar %s failed: invalid or expired refresh token (401)",
                        action,
                    )
                    return
                if status == 403:
                    logger.error(
                        "Google Calendar %s failed: permission denied (403). "
                        "Check OAuth scopes and calendar access.",
                        action,
                    )
                    return
                if status == 404:
                    logger.warning(
                        "Google Calendar %s failed: calendar or event not found (404)",
                        action,
                    )
                    return
                logger.error(
                    "Google Calendar %s failed: HTTP %s — %s",
                    action,
                    status,
                    exc,
                )
                return
        except ImportError:
            pass
        logger.exception("Google Calendar %s failed", action)

    async def get_busy_ranges(
        self,
        start: datetime,
        end: datetime,
        *,
        timeout_seconds: float | None = None,
    ) -> list[tuple[datetime, datetime]]:
        if not await self.is_enabled():
            return []
        missing = await self.get_missing_credentials()
        if missing:
            logger.debug(
                "Skipping Google Calendar busy check — missing: %s",
                ", ".join(missing),
            )
            return []
        cache_key: tuple[str, str, str] | None = None
        try:
            refresh_token = await self._get_refresh_token()
            service = self._build_service(refresh_token)
            if not service:
                return []
            calendar_id = await self._get_calendar_id()
            start_aware = to_aware_local(start)
            end_aware = to_aware_local(end)
            cache_key = (calendar_id, start_aware.isoformat(), end_aware.isoformat())
            cache_ttl = self.settings.google_calendar_busy_cache_seconds
            now_mono = perf_time.monotonic()
            cached_entry = _busy_ranges_cache.get(cache_key)
            if cached_entry and (now_mono - cached_entry[0]) < cache_ttl:
                logger.debug(
                    "Google busy ranges cache hit: calendar=%s range=%s—%s age=%.1fs",
                    calendar_id,
                    start.date(),
                    end.date(),
                    now_mono - cached_entry[0],
                )
                return list(cached_entry[1])

            body = {
                "timeMin": start_aware.isoformat(),
                "timeMax": end_aware.isoformat(),
                "items": [{"id": calendar_id}],
            }

            def _fetch_busy() -> list[tuple[datetime, datetime]]:
                result = service.freebusy().query(body=body).execute()
                busy = result.get("calendars", {}).get(calendar_id, {}).get("busy", [])
                ranges: list[tuple[datetime, datetime]] = []
                for item in busy:
                    raw_start = datetime.fromisoformat(item["start"].replace("Z", "+00:00"))
                    raw_end = datetime.fromisoformat(item["end"].replace("Z", "+00:00"))
                    ranges.append((to_local_naive(raw_start), to_local_naive(raw_end)))
                return ranges

            timeout = timeout_seconds or self.settings.google_calendar_busy_timeout_seconds
            try:
                ranges = await asyncio.wait_for(asyncio.to_thread(_fetch_busy), timeout=timeout)
            except asyncio.TimeoutError:
                logger.warning(
                    "Google Calendar freebusy timed out after %.1fs (range %s — %s)",
                    timeout,
                    start.date(),
                    end.date(),
                )
                if cached_entry:
                    logger.warning("Using stale Google busy ranges cache after timeout")
                    return list(cached_entry[1])
                return []
            _busy_ranges_cache[cache_key] = (perf_time.monotonic(), ranges)
            if len(_busy_ranges_cache) > 128:
                oldest_key = min(_busy_ranges_cache, key=lambda key: _busy_ranges_cache[key][0])
                _busy_ranges_cache.pop(oldest_key, None)
            return ranges
        except Exception as exc:
            self._log_api_error("freebusy query", exc)
            if cache_key is not None:
                stale = _busy_ranges_cache.get(cache_key)
                if stale:
                    logger.warning("Using stale Google busy ranges cache after API error")
                    return list(stale[1])
            return []

    async def create_event(
        self,
        summary: str,
        start_at: datetime,
        end_at: datetime,
        description: str = "",
        location: str | None = None,
    ) -> str | None:
        if not await self.is_enabled():
            return None
        missing = await self.get_missing_credentials()
        if missing:
            logger.warning(
                "Google Calendar event not created — missing credentials: %s",
                ", ".join(missing),
            )
            return None
        try:
            refresh_token = await self._get_refresh_token()
            service = self._build_service(refresh_token)
            if not service:
                return None
            calendar_id = await self._get_calendar_id()
            start_aware = to_aware_local(start_at)
            end_aware = to_aware_local(end_at)
            event: dict[str, Any] = {
                "summary": summary,
                "description": description,
                "start": {
                    "dateTime": start_aware.isoformat(),
                    "timeZone": self.settings.timezone,
                },
                "end": {
                    "dateTime": end_aware.isoformat(),
                    "timeZone": self.settings.timezone,
                },
            }
            if location:
                event["location"] = location

            def _insert() -> str | None:
                created = service.events().insert(calendarId=calendar_id, body=event).execute()
                return created.get("id")

            timeout = self.settings.google_calendar_api_timeout_seconds
            try:
                event_id = await asyncio.wait_for(asyncio.to_thread(_insert), timeout=timeout)
            except asyncio.TimeoutError:
                logger.warning(
                    "Google Calendar event create timed out after %.1fs",
                    timeout,
                )
                return None
            if event_id:
                logger.info("Google Calendar event created: %s", event_id)
            return event_id
        except Exception as exc:
            self._log_api_error("event create", exc)
            return None

    async def update_event(
        self,
        event_id: str,
        summary: str,
        start_at: datetime,
        end_at: datetime,
        description: str = "",
        location: str | None = None,
    ) -> str | None:
        """Update an existing event. On 404, create a new event and return its id."""
        if not await self.is_enabled() or not event_id:
            return None
        missing = await self.get_missing_credentials()
        if missing:
            logger.warning(
                "Google Calendar event %s not updated — missing credentials",
                event_id,
            )
            return None
        try:
            refresh_token = await self._get_refresh_token()
            service = self._build_service(refresh_token)
            if not service:
                return None
            calendar_id = await self._get_calendar_id()
            start_aware = to_aware_local(start_at)
            end_aware = to_aware_local(end_at)
            body: dict[str, Any] = {
                "summary": summary,
                "description": description,
                "start": {
                    "dateTime": start_aware.isoformat(),
                    "timeZone": self.settings.timezone,
                },
                "end": {
                    "dateTime": end_aware.isoformat(),
                    "timeZone": self.settings.timezone,
                },
            }
            if location:
                body["location"] = location
            else:
                body["location"] = ""

            def _patch() -> str | None:
                service.events().patch(
                    calendarId=calendar_id, eventId=event_id, body=body
                ).execute()
                return event_id

            try:
                return await asyncio.wait_for(
                    asyncio.to_thread(_patch),
                    timeout=self.settings.google_calendar_api_timeout_seconds,
                )
            except asyncio.TimeoutError:
                logger.warning(
                    "Google Calendar event update timed out after %.1fs event_id=%s",
                    self.settings.google_calendar_api_timeout_seconds,
                    event_id,
                )
                return None
            except Exception as patch_exc:
                try:
                    from googleapiclient.errors import HttpError

                    if isinstance(patch_exc, HttpError) and patch_exc.resp and patch_exc.resp.status == 404:
                        logger.warning(
                            "Google Calendar event %s not found; creating new event",
                            event_id,
                        )
                        return await self.create_event(
                            summary=summary,
                            start_at=start_at,
                            end_at=end_at,
                            description=description,
                            location=location,
                        )
                except ImportError:
                    pass
                raise patch_exc
        except Exception as exc:
            self._log_api_error(f"event update ({event_id})", exc)
            return None

    async def delete_event(self, event_id: str) -> None:
        if not await self.is_enabled() or not event_id:
            return
        missing = await self.get_missing_credentials()
        if missing:
            logger.warning(
                "Google Calendar event %s not deleted — missing credentials",
                event_id,
            )
            return
        try:
            refresh_token = await self._get_refresh_token()
            service = self._build_service(refresh_token)
            if not service:
                return
            calendar_id = await self._get_calendar_id()

            def _delete() -> None:
                service.events().delete(calendarId=calendar_id, eventId=event_id).execute()

            timeout = self.settings.google_calendar_api_timeout_seconds
            try:
                await asyncio.wait_for(asyncio.to_thread(_delete), timeout=timeout)
            except asyncio.TimeoutError:
                logger.warning(
                    "Google Calendar event delete timed out after %.1fs event_id=%s",
                    timeout,
                    event_id,
                )
                return
            logger.info("Google Calendar event deleted: %s", event_id)
        except Exception as exc:
            try:
                from googleapiclient.errors import HttpError

                if isinstance(exc, HttpError) and exc.resp and exc.resp.status == 404:
                    logger.warning(
                        "Google Calendar event %s not found (already deleted?)",
                        event_id,
                    )
                    return
            except ImportError:
                pass
            self._log_api_error(f"event delete ({event_id})", exc)

    async def test_connection(self) -> CalendarTestResult:
        if not self.env_enabled:
            return CalendarTestResult(ok=False, message_key="calendar_test_disabled_env")
        if not await self.is_enabled():
            return CalendarTestResult(ok=False, message_key="calendar_test_disabled_db")
        missing = await self.get_missing_credentials()
        if missing:
            return CalendarTestResult(
                ok=False,
                message_key="calendar_test_missing_credentials",
                missing=tuple(missing),
            )
        calendar_id = await self._get_calendar_id()
        try:
            refresh_token = await self._get_refresh_token()
            service = self._build_service(refresh_token)
            if not service:
                return CalendarTestResult(
                    ok=False,
                    message_key="calendar_test_client_build_failed",
                )
            meta = service.calendars().get(calendarId=calendar_id).execute()
            summary = meta.get("summary") or calendar_id
            now = now_local()
            body = {
                "timeMin": to_aware_local(now).isoformat(),
                "timeMax": to_aware_local(now + timedelta(hours=1)).isoformat(),
                "items": [{"id": calendar_id}],
            }
            service.freebusy().query(body=body).execute()
            return CalendarTestResult(
                ok=True,
                message_key="calendar_test_success",
                detail=summary,
            )
        except Exception as exc:
            self._log_api_error("connection test", exc)
            detail = str(exc)
            if self._is_refresh_token_error(exc):
                return CalendarTestResult(
                    ok=False,
                    message_key="calendar_test_invalid_token",
                )
            try:
                from googleapiclient.errors import HttpError

                if isinstance(exc, HttpError) and exc.resp:
                    if exc.resp.status == 401:
                        return CalendarTestResult(
                            ok=False,
                            message_key="calendar_test_invalid_token",
                        )
                    if exc.resp.status == 403:
                        return CalendarTestResult(
                            ok=False,
                            message_key="calendar_test_permission_denied",
                        )
                    if exc.resp.status == 404:
                        return CalendarTestResult(
                            ok=False,
                            message_key="calendar_test_invalid_calendar_id",
                            detail=calendar_id,
                        )
                    detail = f"HTTP {exc.resp.status}"
            except ImportError:
                pass
            return CalendarTestResult(
                ok=False,
                message_key="calendar_test_failed",
                detail=detail,
            )
