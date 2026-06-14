#!/usr/bin/env python3
"""Compile-check the app and verify core imports."""

from __future__ import annotations

import compileall
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    print("=== Project check ===")

    ok = compileall.compile_dir(ROOT / "app", quiet=1)
    if not ok:
        print("FAIL: compileall reported errors in app/")
        return 1
    print("OK: app/ compiles")

    scripts_ok = compileall.compile_dir(ROOT / "scripts", quiet=1)
    if not scripts_ok:
        print("FAIL: compileall reported errors in scripts/")
        return 1
    print("OK: scripts/ compiles")

    try:
        from app.config import get_settings  # noqa: F401
        from app.services.booking_service import BookingService  # noqa: F401
        from app.utils.datetime_utils import normalize_slot, now_local, to_local_naive  # noqa: F401

        print("OK: core imports load")
    except Exception as exc:
        print(f"FAIL: import error — {exc}")
        return 1

    # Regression: Google busy aware datetimes must compare safely with naive local datetimes
    try:
        from datetime import datetime
        from zoneinfo import ZoneInfo

        aware_utc = datetime(2026, 6, 15, 9, 0, tzinfo=ZoneInfo("UTC"))
        naive_local = to_local_naive(aware_utc)
        if naive_local.tzinfo is not None:
            raise AssertionError("to_local_naive must strip tzinfo")
        day_end = datetime.combine(naive_local.date(), datetime.max.time()).replace(microsecond=0)
        if not (naive_local < day_end):
            raise AssertionError("naive comparison failed")
        _ = now_local() < day_end
        print("OK: aware->naive datetime comparison safe")
    except Exception as exc:
        print(f"FAIL: datetime normalization regression — {exc}")
        return 1

    settings = get_settings()
    sample = normalize_slot.__name__
    print(f"TIMEZONE={settings.timezone}")
    print(f"normalize_slot={sample} (from app.utils.datetime_utils)")

    try:
        import app.main  # noqa: F401

        print("OK: app.main importable")
    except SystemExit:
        print("WARN: app.main exited during import (likely missing BOT_TOKEN in .env)")
    except Exception as exc:
        print(f"FAIL: app.main import — {exc}")
        return 1

    print("=== All checks passed ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
