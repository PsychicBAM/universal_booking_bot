from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery


async def edit_or_send(callback: CallbackQuery, text: str, reply_markup=None) -> None:
    """Edit callback message or send a new one (needed after photo/video cards)."""
    try:
        await callback.message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest:
        try:
            await callback.message.delete()
        except TelegramBadRequest:
            pass
        await callback.message.answer(text, reply_markup=reply_markup)
