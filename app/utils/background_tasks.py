"""Fire-and-forget asyncio tasks that must not crash the bot."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Coroutine
from typing import Any

logger = logging.getLogger(__name__)

_background_tasks: set[asyncio.Task[Any]] = set()


def schedule_background_task(coro: Coroutine[Any, Any, Any], name: str) -> asyncio.Task[Any]:
    """Run *coro* in the background; log and swallow unexpected errors."""

    async def _wrapper() -> None:
        try:
            await coro
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Background task failed: %s", name)

    task = asyncio.create_task(_wrapper(), name=name)
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    return task
