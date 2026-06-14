"""User language lookup for notifications outside request middleware."""

from app.config import get_settings
from app.database.session import async_session_factory
from app.repositories import ClientRepository


async def get_user_language(telegram_id: int) -> str:
    settings = get_settings()
    async with async_session_factory() as session:
        client = await ClientRepository(session).get_by_telegram_id(telegram_id)
        if client and client.language and client.language in settings.supported_languages:
            return client.language
    return settings.default_language
