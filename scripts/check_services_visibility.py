#!/usr/bin/env python3
"""Report services grouped by visibility state (active / disabled / archived)."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.database.session import async_session_factory, init_db
from app.repositories import ServiceRepository


def _classify(service) -> str:
    if service.archived_at is not None:
        return "archived"
    if service.is_active:
        return "active_visible"
    return "disabled_non_archived"


async def main() -> None:
    await init_db()
    async with async_session_factory() as session:
        services = await ServiceRepository(session).list_all()

    groups: dict[str, list] = {
        "active_visible": [],
        "disabled_non_archived": [],
        "archived": [],
    }
    for service in services:
        groups[_classify(service)].append(service)

    print("=== Services visibility report ===\n")
    headers = ("id", "name", "is_active", "archived_at", "show_media_to_clients")

    for title, key in (
        ("Active (client-visible)", "active_visible"),
        ("Disabled, non-archived (disabled services screen)", "disabled_non_archived"),
        ("Archived", "archived"),
    ):
        print(title)
        print("-" * len(title))
        items = groups[key]
        if not items:
            print("  (none)")
        else:
            print("\t".join(headers))
            for s in items:
                archived = s.archived_at.isoformat() if s.archived_at else ""
                name = s.name.encode("ascii", errors="replace").decode("ascii")
                print(f"{s.id}\t{name}\t{s.is_active}\t{archived}\t{s.show_media_to_clients}")
        print()

    print(f"Total: {len(services)}")


if __name__ == "__main__":
    asyncio.run(main())
