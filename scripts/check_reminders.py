#!/usr/bin/env python3
"""Verify reminder configuration, model fields, and i18n keys."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    errors: list[str] = []

    try:
        from app.config import get_settings
        from app.services.reminder_settings import reminder_config_from_settings
        from app.services.reminder_service import ReminderService

        settings = get_settings()
        config = reminder_config_from_settings(settings)
        assert config.client_reminder_1_minutes > 0, "client_reminder_1_minutes must be positive"
        assert config.client_reminder_2_minutes > 0, "client_reminder_2_minutes must be positive"
        assert config.admin_reminder_minutes > 0, "admin_reminder_minutes must be positive"
        print("OK: reminder config loads from .env")
        print(f"  enabled={config.enabled} test_mode={config.test_mode}")
        print(f"  client_r1={config.client_reminder_1_minutes}m client_r2={config.client_reminder_2_minutes}m")
        print(f"  admin={config.admin_reminder_minutes}m")
        print("OK: ReminderService imports")
    except Exception as exc:
        errors.append(f"config/service import: {exc}")

    try:
        from app.models import Booking

        for field in (
            "client_reminder_1_sent_at",
            "client_reminder_2_sent_at",
            "admin_reminder_sent_at",
        ):
            if not hasattr(Booking, field):
                errors.append(f"Booking model missing field: {field}")
        if not errors:
            print("OK: booking reminder fields exist on model")
    except Exception as exc:
        errors.append(f"model check: {exc}")

    try:
        from app.bot.i18n import TEXTS, t

        for lang in TEXTS:
            for key in ("reminder_client", "reminder_admin"):
                if key not in TEXTS[lang]:
                    errors.append(f"missing i18n key {key!r} for lang {lang!r}")
                else:
                    t(lang, key, service_name="Test", date_time="01.01.2026 10:00")
        t("en", "reminder_admin", service_name="Test", date_time="01.01.2026 10:00", client_name="A", client_phone="+1")
        if not errors:
            print("OK: reminder translation keys exist (ru/en)")
    except Exception as exc:
        errors.append(f"i18n check: {exc}")

    if errors:
        print("FAILED:")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("All reminder checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
