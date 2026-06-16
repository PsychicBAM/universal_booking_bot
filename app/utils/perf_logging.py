"""Structured timing logs for user-facing operations."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

SLOW_ACTION_THRESHOLD_SECONDS = 2.0


def _format_value(value: float | int | str) -> str:
    if isinstance(value, float):
        return f"{value:.2f}s"
    return str(value)


def log_action_timing(
    label: str,
    *,
    total: float,
    warn_threshold: float = SLOW_ACTION_THRESHOLD_SECONDS,
    **parts: float | int | str,
) -> None:
    detail = " ".join(f"{key}={_format_value(value)}" for key, value in parts.items())
    message = f"{label} timing: {detail} total={total:.2f}s".strip()
    if total > warn_threshold:
        logger.warning(message)
    else:
        logger.info(message)
