import logging

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery

logger = logging.getLogger(__name__)


async def safe_callback_answer(
    callback: CallbackQuery,
    text: str | None = None,
    show_alert: bool = False,
) -> None:
    """Answer callback query; ignore expired/invalid query IDs."""
    try:
        await callback.answer(text=text, show_alert=show_alert)
    except TelegramBadRequest as exc:
        err = str(exc).lower()
        if "query is too old" in err or "query id is invalid" in err:
            logger.warning(
                "Callback answer skipped (expired): data=%s user_id=%s",
                callback.data,
                callback.from_user.id if callback.from_user else None,
            )
            return
        raise


async def answer_callback_early(callback: CallbackQuery) -> None:
    """Acknowledge callback immediately with no text."""
    await safe_callback_answer(callback)
