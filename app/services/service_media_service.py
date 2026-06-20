from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InputMediaPhoto
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.i18n import t
from app.bot.keyboards.service_media_kb import client_service_card_kb
from app.models import Service, ServiceMedia
from app.repositories import (
    MAX_SERVICE_PHOTOS,
    MAX_SERVICE_VIDEOS,
    ServiceLocationRepository,
    ServiceMediaRepository,
)
from app.utils.formatting import format_service, format_service_admin

logger = logging.getLogger(__name__)

TELEGRAM_CAPTION_LIMIT = 1024


class MediaLimitError(Exception):
    pass


def _cover_photo(media_items: list[ServiceMedia]) -> ServiceMedia | None:
    photos = [m for m in media_items if m.media_type == "photo"]
    if not photos:
        return None
    return next((p for p in photos if p.is_cover), photos[0])


def _service_video(media_items: list[ServiceMedia]) -> ServiceMedia | None:
    return next((m for m in media_items if m.media_type == "video"), None)


def _service_card_kb(service: Service, lang: str, *, photos_count: int, videos_count: int, show_media: bool):
    return client_service_card_kb(
        service.id,
        lang,
        has_photos=photos_count > 0 and show_media,
        has_video=videos_count > 0 and show_media,
        service_type=service.service_type,
    )


async def get_media_stats(session: AsyncSession, service_id: int) -> tuple[int, int, bool]:
    repo = ServiceMediaRepository(session)
    photos = await repo.count_photos(service_id)
    videos = await repo.count_videos(service_id)
    cover = await repo.get_cover_photo(service_id)
    return photos, videos, cover is not None


async def add_photo(session: AsyncSession, service_id: int, file_id: str) -> ServiceMedia:
    repo = ServiceMediaRepository(session)
    if await repo.count_photos(service_id) >= MAX_SERVICE_PHOTOS:
        raise MediaLimitError()
    photos = await repo.list_photos(service_id)
    is_cover = len(photos) == 0
    return await repo.add(
        service_id,
        "photo",
        file_id,
        is_cover=is_cover,
        position=len(photos),
    )


async def add_video(session: AsyncSession, service_id: int, file_id: str) -> ServiceMedia:
    repo = ServiceMediaRepository(session)
    if await repo.count_videos(service_id) >= MAX_SERVICE_VIDEOS:
        raise MediaLimitError()
    return await repo.add(service_id, "video", file_id, position=0)


async def delete_media(session: AsyncSession, media_id: int) -> bool:
    repo = ServiceMediaRepository(session)
    media = await repo.get_by_id(media_id)
    if not media:
        return False
    service_id = media.service_id
    was_cover = media.is_cover and media.media_type == "photo"
    await repo.delete(media)
    if was_cover:
        photos = await repo.list_photos(service_id)
        if photos:
            await repo.set_cover(photos[0].id, service_id)
    return True


async def send_service_card_with_media(
    bot: Bot,
    chat_id: int,
    service: Service,
    media_items: list[ServiceMedia],
    lang: str,
    *,
    photos_count: int,
    videos_count: int,
    force_show: bool = False,
    media_mode: str = "open",
) -> None:
    """
    Send a connected service card when possible (photo/video + full caption + buttons).
    media_mode: open | photos | video | card_only
    """
    show_media = force_show or service.show_media_to_clients
    card_text = format_service(service, lang)
    kb = _service_card_kb(service, lang, photos_count=photos_count, videos_count=videos_count, show_media=show_media)

    if media_mode == "photos" and show_media:
        photos = [m for m in media_items if m.media_type == "photo"]
        if photos:
            await _send_photo_gallery(bot, chat_id, photos, service.id)
        await _send_connected_card(
            bot, chat_id, service, card_text, kb,
            cover=_cover_photo(media_items),
            video=_service_video(media_items) if not _cover_photo(media_items) else None,
        )
        return

    if media_mode == "video" and show_media:
        video = _service_video(media_items)
        if video:
            await _send_plain_video(bot, chat_id, video, service.id)
        await _send_connected_card(
            bot, chat_id, service, card_text, kb,
            cover=_cover_photo(media_items),
            video=video if not _cover_photo(media_items) else None,
        )
        return

    if media_mode == "card_only" or not show_media:
        if force_show and not media_items:
            await bot.send_message(chat_id, t(lang, "preview_not_available"))
        await _send_connected_card(bot, chat_id, service, card_text, kb)
        return

    # open — one connected card; cover photo preferred, else video, else text
    cover = _cover_photo(media_items)
    video = _service_video(media_items)
    if not cover and not video and force_show and not media_items:
        await bot.send_message(chat_id, t(lang, "preview_not_available"))
    if cover:
        await _send_connected_card(bot, chat_id, service, card_text, kb, cover=cover)
    elif video:
        await _send_connected_card(bot, chat_id, service, card_text, kb, video=video)
    else:
        await _send_connected_card(bot, chat_id, service, card_text, kb)


async def send_service_presentation(
    bot: Bot,
    chat_id: int,
    service: Service,
    media_items: list[ServiceMedia],
    lang: str,
    *,
    photos_count: int,
    videos_count: int,
    force_show: bool = False,
    media_mode: str = "open",
) -> None:
    """Alias for send_service_card_with_media (used by handlers)."""
    await send_service_card_with_media(
        bot,
        chat_id,
        service,
        media_items,
        lang,
        photos_count=photos_count,
        videos_count=videos_count,
        force_show=force_show,
        media_mode=media_mode,
    )


async def _send_connected_card(
    bot: Bot,
    chat_id: int,
    service: Service,
    card_text: str,
    reply_markup,
    *,
    cover: ServiceMedia | None = None,
    video: ServiceMedia | None = None,
) -> None:
    if cover:
        if len(card_text) <= TELEGRAM_CAPTION_LIMIT:
            try:
                await bot.send_photo(
                    chat_id,
                    cover.telegram_file_id,
                    caption=card_text,
                    reply_markup=reply_markup,
                )
                return
            except TelegramBadRequest as exc:
                logger.warning("Connected photo card failed (service_id=%s): %s", service.id, exc)
        await _send_photo_then_text_card(bot, chat_id, service, cover, card_text, reply_markup)
        return

    if video:
        if len(card_text) <= TELEGRAM_CAPTION_LIMIT:
            try:
                await bot.send_video(
                    chat_id,
                    video.telegram_file_id,
                    caption=card_text,
                    reply_markup=reply_markup,
                )
                return
            except TelegramBadRequest as exc:
                logger.warning("Connected video card failed (service_id=%s): %s", service.id, exc)
        await _send_video_then_text_card(bot, chat_id, service, video, card_text, reply_markup)
        return

    await bot.send_message(chat_id, card_text, reply_markup=reply_markup)


async def _send_photo_then_text_card(
    bot: Bot,
    chat_id: int,
    service: Service,
    cover: ServiceMedia,
    card_text: str,
    reply_markup,
) -> None:
    try:
        short = service.name if len(service.name) <= TELEGRAM_CAPTION_LIMIT else service.name[:TELEGRAM_CAPTION_LIMIT]
        await bot.send_photo(chat_id, cover.telegram_file_id, caption=short)
    except TelegramBadRequest as exc:
        logger.warning("Photo fallback send failed (service_id=%s): %s", service.id, exc)
    await bot.send_message(chat_id, card_text, reply_markup=reply_markup)


async def _send_video_then_text_card(
    bot: Bot,
    chat_id: int,
    service: Service,
    video: ServiceMedia,
    card_text: str,
    reply_markup,
) -> None:
    try:
        short = service.name if len(service.name) <= TELEGRAM_CAPTION_LIMIT else service.name[:TELEGRAM_CAPTION_LIMIT]
        await bot.send_video(chat_id, video.telegram_file_id, caption=short)
    except TelegramBadRequest as exc:
        logger.warning("Video fallback send failed (service_id=%s): %s", service.id, exc)
    await bot.send_message(chat_id, card_text, reply_markup=reply_markup)


async def _send_photo_gallery(bot: Bot, chat_id: int, photos: list[ServiceMedia], service_id: int) -> None:
    try:
        if len(photos) == 1:
            await bot.send_photo(chat_id, photos[0].telegram_file_id)
        else:
            group = [InputMediaPhoto(media=p.telegram_file_id) for p in photos[:10]]
            await bot.send_media_group(chat_id, group)
    except TelegramBadRequest as exc:
        logger.warning("Photo gallery failed (service_id=%s): %s", service_id, exc)


async def _send_plain_video(bot: Bot, chat_id: int, video: ServiceMedia, service_id: int) -> None:
    try:
        await bot.send_video(chat_id, video.telegram_file_id)
    except TelegramBadRequest as exc:
        logger.warning("Plain video send failed (service_id=%s): %s", service_id, exc)


async def build_admin_service_detail(session: AsyncSession, service: Service, lang: str):
    from app.bot.keyboards import admin_service_detail_kb
    from app.bot.utils.service_helpers import service_detail_source
    from app.models import SERVICE_TYPE_ORDER
    from app.services.service_modes_service import load_service_modes

    repo = ServiceMediaRepository(session)
    photos = await repo.count_photos(service.id)
    videos = await repo.count_videos(service.id)
    locations_count = await ServiceLocationRepository(session).count_for_service(service.id)
    modes = await load_service_modes(session)
    text = format_service_admin(
        service,
        lang,
        photos_count=photos,
        videos_count=videos,
        locations_count=locations_count,
    )
    kb = admin_service_detail_kb(
        service.id,
        service.is_active,
        lang,
        archived=service.archived_at is not None,
        show_media_to_clients=service.show_media_to_clients,
        detail_source=service_detail_source(service),
        show_type_change=modes.booking_enabled and modes.order_enabled,
        is_order_type=service.service_type == SERVICE_TYPE_ORDER,
    )
    return text, kb
