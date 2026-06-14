from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: str = Field(..., alias="BOT_TOKEN")
    admin_ids: list[int] = Field(default_factory=list, alias="ADMIN_IDS")
    database_url: str = Field(
        "sqlite+aiosqlite:///data/booking_bot.db",
        alias="DATABASE_URL",
    )
    timezone: str = Field("Europe/Moscow", alias="TIMEZONE")
    default_slot_step_minutes: int = Field(30, alias="DEFAULT_SLOT_STEP_MINUTES")
    booking_days_ahead: int = Field(30, alias="BOOKING_DAYS_AHEAD")
    booking_first_page_days: int = Field(14, alias="BOOKING_FIRST_PAGE_DAYS")
    availability_timeout_seconds: float = Field(8.0, alias="AVAILABILITY_TIMEOUT_SECONDS")
    google_calendar_busy_timeout_seconds: float = Field(5.0, alias="GOOGLE_CALENDAR_BUSY_TIMEOUT_SECONDS")
    cancel_booking_hours_before: int = Field(2, alias="CANCEL_BOOKING_HOURS_BEFORE")
    reschedule_booking_hours_before: int | None = Field(None, alias="RESCHEDULE_BOOKING_HOURS_BEFORE")
    contact_admin_username: str = Field("", alias="CONTACT_ADMIN_USERNAME")
    default_language: str = Field("ru", alias="DEFAULT_LANGUAGE")
    supported_languages: list[str] = Field(default_factory=lambda: ["ru", "en"], alias="SUPPORTED_LANGUAGES")

    google_calendar_enabled: bool = Field(False, alias="GOOGLE_CALENDAR_ENABLED")
    google_client_id: str = Field("", alias="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field("", alias="GOOGLE_CLIENT_SECRET")
    google_redirect_uri: str = Field("", alias="GOOGLE_REDIRECT_URI")
    google_refresh_token: str = Field("", alias="GOOGLE_REFRESH_TOKEN")
    google_calendar_id: str = Field("primary", alias="GOOGLE_CALENDAR_ID")

    reminders_enabled: bool = Field(True, alias="REMINDERS_ENABLED")
    client_reminder_1_minutes: int = Field(1440, alias="CLIENT_REMINDER_1_MINUTES")
    client_reminder_2_minutes: int = Field(120, alias="CLIENT_REMINDER_2_MINUTES")
    admin_reminder_minutes: int = Field(60, alias="ADMIN_REMINDER_MINUTES")
    reminder_test_mode: bool = Field(False, alias="REMINDER_TEST_MODE")
    test_client_reminder_minutes: int = Field(5, alias="TEST_CLIENT_REMINDER_MINUTES")
    test_admin_reminder_minutes: int = Field(3, alias="TEST_ADMIN_REMINDER_MINUTES")

    @field_validator("supported_languages", mode="before")
    @classmethod
    def parse_supported_languages(cls, value: object) -> list[str]:
        if value is None or value == "":
            return ["ru", "en"]
        if isinstance(value, list):
            return [str(v).strip() for v in value]
        return [part.strip() for part in str(value).split(",") if part.strip()]

    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, value: object) -> list[int]:
        if value is None or value == "":
            return []
        if isinstance(value, list):
            return [int(v) for v in value]
        return [int(part.strip()) for part in str(value).split(",") if part.strip()]

    def effective_reschedule_hours_before(self) -> int:
        if self.reschedule_booking_hours_before is not None:
            return self.reschedule_booking_hours_before
        return self.cancel_booking_hours_before


@lru_cache
def get_settings() -> Settings:
    return Settings()
