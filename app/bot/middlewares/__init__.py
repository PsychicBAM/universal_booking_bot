from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.config import get_settings
from app.database.session import async_session_factory
from app.repositories import ClientRepository


class AdminMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        admin_ids = get_settings().admin_ids
        data["is_admin"] = bool(user and user.id in admin_ids)
        return await handler(event, data)


class LanguageMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        settings = get_settings()
        lang = settings.default_language
        if user:
            async with async_session_factory() as session:
                client = await ClientRepository(session).get_by_telegram_id(user.id)
                if client and client.language:
                    lang = client.language
        if lang not in settings.supported_languages:
            lang = settings.default_language
        data["lang"] = lang
        return await handler(event, data)
