import logging

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message

logger = logging.getLogger(__name__)


def _is_not_modified_error(exc: TelegramBadRequest) -> bool:
    return "message is not modified" in str(exc).lower()


async def safe_edit_text(
    message: Message,
    text: str,
    reply_markup=None,
    parse_mode: str | None = None,
    **kwargs,
):
    """Edit message text; ignore Telegram 'message is not modified' errors."""
    try:
        return await message.edit_text(
            text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
            **kwargs,
        )
    except TelegramBadRequest as exc:
        if _is_not_modified_error(exc):
            logger.debug("Message not modified, skipping edit_text")
            return None
        raise


async def safe_edit_caption(
    message: Message,
    caption: str,
    reply_markup=None,
    parse_mode: str | None = None,
    **kwargs,
):
    """Edit message caption; ignore Telegram 'message is not modified' errors."""
    try:
        return await message.edit_caption(
            caption=caption,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
            **kwargs,
        )
    except TelegramBadRequest as exc:
        if _is_not_modified_error(exc):
            logger.debug("Message not modified, skipping edit_caption")
            return None
        raise


async def edit_or_send(
    callback: CallbackQuery,
    text: str,
    reply_markup=None,
    *,
    parse_mode: str | None = None,
) -> None:
    """Edit callback message or send a new one (needed after photo/video cards)."""
    try:
        await safe_edit_text(callback.message, text, reply_markup=reply_markup, parse_mode=parse_mode)
        return
    except TelegramBadRequest:
        try:
            await callback.message.delete()
        except TelegramBadRequest:
            pass
        await callback.message.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)
