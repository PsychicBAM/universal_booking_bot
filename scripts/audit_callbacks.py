#!/usr/bin/env python3
"""Audit callback prefixes registered in handlers and parser safety."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

HANDLERS_DIR = ROOT / "app" / "bot" / "handlers"

# Prefixes that must be handled somewhere in handlers (substring in handler source).
REQUIRED_PREFIXES = (
    "adm_confirm:",
    "adm_cancel:",
    "adm_msg:",
    "adm_att:",
    "adm_book:",
    "adm_cli:",
    "ord:",
    "myord:",
    "my:view:",
    "my:cancel:",
    "cb:book:",
    "cb:order:",
    "confirm:yes",
    "att:",
    "myact:",
    "unknown_action_open_again",
)

# Stale/malformed samples — parsers must not raise uncaught ValueError for these.
STALE_CALLBACKS = (
    "adm_confirm:abc",
    "adm_confirm:999999",
    "adm_cancel:abc",
    "adm_msg:abc",
    "adm_book:view:abc",
    "adm_cli:all",
    "adm_cli:view:all",
    "adm_cli:hist:123:all:0:0",
    "adm_cli:bad:bad:bad",
    "my:view:abc",
    "myord:view:abc",
    "myord:view:999999",
    "cb:book:abc",
    "time:not_timestamp",
    "bk:period:unknown",
    "adm_att:send:abc",
    "unknown:callback:data",
)


def _handler_blob() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in HANDLERS_DIR.glob("*.py"))


def _extract_callback_prefixes(blob: str) -> set[str]:
    prefixes: set[str] = set()
    for match in re.finditer(r'F\.data\.(?:startswith|regexp)\(\s*r?["\']([^"\']+)["\']', blob):
        prefixes.add(match.group(1))
    for match in re.finditer(r'F\.data\s*==\s*r?["\']([^"\']+)["\']', blob):
        prefixes.add(match.group(1))
    return prefixes


def _test_parsers_safe() -> list[str]:
    errors: list[str] = []
    from app.services.admin_bookings_service import (
        parse_admin_confirm_callback,
        parse_admin_simple_booking_id,
        parse_booking_detail_source,
    )

    for data in STALE_CALLBACKS:
        if data.startswith("adm_confirm:"):
            try:
                parse_admin_confirm_callback(data)
            except ValueError:
                pass
            except Exception as exc:
                errors.append(f"{data!r} adm_confirm parser raised {exc!r}")
        if data.startswith(("adm_cancel:", "adm_msg:")):
            prefix = "adm_cancel:" if data.startswith("adm_cancel:") else "adm_msg:"
            try:
                parse_admin_simple_booking_id(data, prefix)
            except Exception as exc:
                errors.append(f"{data!r} simple id parser raised {exc!r}")
        if data.startswith("adm_book:view:"):
            try:
                booking_id, source = parse_booking_detail_source(data)
                if booking_id is not None and source is None:
                    errors.append(f"{data!r} booking view parse returned id without source")
            except Exception as exc:
                errors.append(f"{data!r} booking view parser raised {exc!r}")
    return errors


def main() -> int:
    print("=== Callback audit ===")
    failures = 0
    blob = _handler_blob()
    prefixes = _extract_callback_prefixes(blob)

    missing = [p for p in REQUIRED_PREFIXES if p not in blob]
    if missing:
        failures += len(missing)
        print(f"FAIL: missing handler references: {', '.join(missing)}")
    else:
        print(f"OK: required callback prefixes present ({len(REQUIRED_PREFIXES)})")

    if "unknown_callback_logger" not in blob or "unknown_action_open_again" not in blob:
        print("FAIL: unknown callback fallback handler missing")
        failures += 1
    else:
        print("OK: unknown callback fallback registered")

    # Prefix conflict heuristic: identical exact-match handlers.
    exact = re.findall(r'F\.data\s*==\s*r?["\']([^"\']+)["\']', blob)
    dupes = sorted({x for x in exact if exact.count(x) > 1})
    if dupes:
        print(f"WARN: duplicate exact callback handlers: {dupes[:10]}")
    else:
        print("OK: no duplicate exact callback handlers detected")

    parser_errors = _test_parsers_safe()
    if parser_errors:
        failures += len(parser_errors)
        for err in parser_errors:
            print(f"FAIL: {err}")
    else:
        print(f"OK: stale callback parsers safe ({len(STALE_CALLBACKS)} samples)")

    print(f"INFO: discovered {len(prefixes)} unique callback patterns in handlers")
    if failures:
        print(f"=== Callback audit: {failures} issue(s) ===")
        return 1
    print("=== Callback audit passed ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
