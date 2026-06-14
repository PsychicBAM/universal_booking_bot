from collections.abc import Callable, Awaitable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, TelegramObject

from app.bot.i18n import CANCEL_TEXTS
from app.bot.keyboards import ALL_MENU_TEXTS


class ClearMenuFsmMiddleware(BaseMiddleware):
    """Clear active FSM when user navigates via main reply-keyboard menu (not Cancel)."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Message) and event.text and event.text in ALL_MENU_TEXTS:
            if event.text in CANCEL_TEXTS:
                return await handler(event, data)
            state: FSMContext | None = data.get("state")
            if state and await state.get_state():
                await state.clear()
        return await handler(event, data)
