from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.config import get_settings
from app.database.session import async_session_factory
from app.repositories import ClientRepository
from app.services.language_service import (
    effective_lang,
    get_effective_default_language,
    refresh_enabled_languages_cache,
)


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
        user_lang: str | None = None

        async with async_session_factory() as session:
            enabled = await refresh_enabled_languages_cache(session)
            default_lang = await get_effective_default_language(session)
            if user:
                client = await ClientRepository(session).get_by_telegram_id(user.id)
                if client and client.language:
                    user_lang = client.language

        lang = effective_lang(user_lang, enabled, default_lang)
        data["lang"] = lang
        data["enabled_languages"] = enabled
        data["language_switching_enabled"] = len(enabled) > 1
        return await handler(event, data)
