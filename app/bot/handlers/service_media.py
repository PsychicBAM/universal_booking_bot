from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.utils.callbacks import safe_callback_answer
from app.bot.utils.telegram_ui import safe_edit_text

from app.bot.i18n import t
from app.bot.keyboards import cancel_kb
from app.bot.keyboards.service_media_kb import (
    service_media_cover_kb,
    service_media_delete_kb,
    service_media_menu_kb,
)
from app.bot.states import AdminServiceMediaStates
from app.database.session import async_session_factory
from app.repositories import ServiceMediaRepository, ServiceRepository
from app.services.service_media_service import (
    MediaLimitError,
    add_photo,
    add_video,
    build_admin_service_detail,
    delete_media,
    get_media_stats,
    send_service_presentation,
)

router = Router()


def _media_menu_text(lang: str, photos: int, videos: int, has_cover: bool) -> str:
    cover_line = t(lang, "cover_selected") if has_cover else t(lang, "cover_not_selected")
    return (
        f"{t(lang, 'service_media_title')}\n"
        f"{t(lang, 'photos_count', count=str(photos))}\n"
        f"{t(lang, 'videos_count', count=str(videos))}\n"
        f"{cover_line}"
    )


async def show_media_menu(event: Message | CallbackQuery, service_id: int, lang: str) -> None:
    async with async_session_factory() as session:
        service = await ServiceRepository(session).get_by_id(service_id)
        if not service:
            text = t(lang, "not_found")
            if isinstance(event, CallbackQuery):
                await event.answer(text, show_alert=True)
            else:
                await event.answer(text)
            return
        photos, videos, has_cover = await get_media_stats(session, service_id)
    text = _media_menu_text(lang, photos, videos, has_cover)
    keyboard = service_media_menu_kb(service_id, lang)
    if isinstance(event, CallbackQuery):
        await safe_edit_text(event.message,text, reply_markup=keyboard)
        await event.answer()
    else:
        await event.answer(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("sm:menu:"))
async def media_menu(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    service_id = int(callback.data.split(":")[-1])
    await show_media_menu(callback, service_id, lang)


@router.callback_query(F.data.startswith("sm:back:"))
async def media_back(callback: CallbackQuery, is_admin: bool, lang: str, state: FSMContext) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    await state.clear()
    service_id = int(callback.data.split(":")[-1])
    async with async_session_factory() as session:
        service = await ServiceRepository(session).get_by_id(service_id)
        if not service:
            await safe_callback_answer(callback, t(lang, "not_found"), show_alert=True)
            return
        text, kb = await build_admin_service_detail(session, service, lang)
    await safe_edit_text(callback.message,text, reply_markup=kb)
    await safe_callback_answer(callback)


@router.callback_query(F.data.startswith("sm:show:"))
async def toggle_show_media(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    service_id = int(callback.data.split(":")[-1])
    async with async_session_factory() as session:
        service = await ServiceRepository(session).get_by_id(service_id)
        if not service:
            await safe_callback_answer(callback, t(lang, "not_found"), show_alert=True)
            return
        service.show_media_to_clients = not service.show_media_to_clients
        await session.commit()
        text, kb = await build_admin_service_detail(session, service, lang)
    msg = t(lang, "media_display_enabled" if service.show_media_to_clients else "media_display_disabled")
    await safe_callback_answer(callback, msg)
    await safe_edit_text(callback.message,text, reply_markup=kb)


@router.callback_query(F.data.startswith("sm:add:ph:"))
async def start_add_photo(callback: CallbackQuery, is_admin: bool, lang: str, state: FSMContext) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    service_id = int(callback.data.split(":")[-1])
    await state.update_data(flow_origin="admin", media_service_id=service_id)
    await state.set_state(AdminServiceMediaStates.uploading_photo)
    await safe_callback_answer(callback)
    await callback.message.answer(t(lang, "upload_photo_prompt"), reply_markup=cancel_kb(lang))


@router.callback_query(F.data.startswith("sm:add:vd:"))
async def start_add_video(callback: CallbackQuery, is_admin: bool, lang: str, state: FSMContext) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    service_id = int(callback.data.split(":")[-1])
    await state.update_data(flow_origin="admin", media_service_id=service_id)
    await state.set_state(AdminServiceMediaStates.uploading_video)
    await safe_callback_answer(callback)
    await callback.message.answer(t(lang, "upload_video_prompt"), reply_markup=cancel_kb(lang))


@router.message(AdminServiceMediaStates.uploading_photo, F.photo)
async def receive_photo(message: Message, is_admin: bool, lang: str, state: FSMContext) -> None:
    if not is_admin:
        return
    data = await state.get_data()
    service_id = data.get("media_service_id")
    if not service_id:
        await state.clear()
        return
    file_id = message.photo[-1].file_id
    try:
        async with async_session_factory() as session:
            await add_photo(session, service_id, file_id)
            await session.commit()
    except MediaLimitError:
        await message.answer(t(lang, "max_media_reached"))
        return
    await state.clear()
    await message.answer(t(lang, "media_added"))
    await show_media_menu(message, service_id, lang)


@router.message(AdminServiceMediaStates.uploading_video, F.video)
async def receive_video(message: Message, is_admin: bool, lang: str, state: FSMContext) -> None:
    if not is_admin:
        return
    data = await state.get_data()
    service_id = data.get("media_service_id")
    if not service_id:
        await state.clear()
        return
    file_id = message.video.file_id
    try:
        async with async_session_factory() as session:
            await add_video(session, service_id, file_id)
            await session.commit()
    except MediaLimitError:
        await message.answer(t(lang, "max_media_reached"))
        return
    await state.clear()
    await message.answer(t(lang, "media_added"))
    await show_media_menu(message, service_id, lang)


@router.message(AdminServiceMediaStates.uploading_photo)
async def wrong_photo_upload(message: Message, lang: str) -> None:
    await message.answer(t(lang, "upload_photo_prompt"), reply_markup=cancel_kb(lang))


@router.message(AdminServiceMediaStates.uploading_video)
async def wrong_video_upload(message: Message, lang: str) -> None:
    await message.answer(t(lang, "upload_video_prompt"), reply_markup=cancel_kb(lang))


@router.callback_query(F.data.startswith("sm:cover:") & ~F.data.startswith("sm:cover:set:"))
async def choose_cover_list(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    service_id = int(callback.data.split(":")[-1])
    async with async_session_factory() as session:
        photos = await ServiceMediaRepository(session).list_photos(service_id)
    if not photos:
        await safe_callback_answer(callback, t(lang, "no_photos_for_cover"), show_alert=True)
        return
    photo_ids = [(n, p.id) for n, p in enumerate(photos, start=1)]
    await safe_edit_text(callback.message,
        t(lang, "choose_cover"),
        reply_markup=service_media_cover_kb(service_id, photo_ids, lang),
    )
    await safe_callback_answer(callback)


@router.callback_query(F.data.startswith("sm:cover:set:"))
async def set_cover(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    media_id = int(callback.data.split(":")[-1])
    async with async_session_factory() as session:
        repo = ServiceMediaRepository(session)
        media = await repo.get_by_id(media_id)
        if not media:
            await safe_callback_answer(callback, t(lang, "not_found"), show_alert=True)
            return
        await repo.set_cover(media_id, media.service_id)
        await session.commit()
        service_id = media.service_id
        photos, videos, has_cover = await get_media_stats(session, service_id)
    await safe_callback_answer(callback, t(lang, "cover_set"))
    await safe_edit_text(callback.message,
        _media_menu_text(lang, photos, videos, has_cover),
        reply_markup=service_media_menu_kb(service_id, lang),
    )


@router.callback_query(F.data.regexp(r"^sm:del:\d+$"))
async def delete_media_list(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    service_id = int(callback.data.split(":")[-1])
    async with async_session_factory() as session:
        items_raw = await ServiceMediaRepository(session).list_for_service(service_id)
    if not items_raw:
        await safe_callback_answer(callback, t(lang, "no_media"), show_alert=True)
        return
    photo_n = 0
    video_n = 0
    items: list[tuple[str, int, int]] = []
    for item in items_raw:
        if item.media_type == "photo":
            photo_n += 1
            items.append(("media_photo_n", photo_n, item.id))
        else:
            video_n += 1
            items.append(("media_video_n", video_n, item.id))
    await safe_edit_text(callback.message,
        t(lang, "delete_media"),
        reply_markup=service_media_delete_kb(service_id, items, lang),
    )
    await safe_callback_answer(callback)


@router.callback_query(F.data.startswith("sm:del:go:"))
async def delete_media_item(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    media_id = int(callback.data.split(":")[-1])
    async with async_session_factory() as session:
        repo = ServiceMediaRepository(session)
        media = await repo.get_by_id(media_id)
        if not media:
            await safe_callback_answer(callback, t(lang, "not_found"), show_alert=True)
            return
        service_id = media.service_id
        await delete_media(session, media_id)
        await session.commit()
        photos, videos, has_cover = await get_media_stats(session, service_id)
    await safe_callback_answer(callback, t(lang, "media_deleted"))
    await safe_edit_text(callback.message,
        _media_menu_text(lang, photos, videos, has_cover),
        reply_markup=service_media_menu_kb(service_id, lang),
    )


@router.callback_query(F.data.startswith("sm:preview:"))
async def preview_media(callback: CallbackQuery, is_admin: bool, lang: str, bot: Bot) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    service_id = int(callback.data.split(":")[-1])
    async with async_session_factory() as session:
        service = await ServiceRepository(session).get_by_id(service_id)
        if not service:
            await safe_callback_answer(callback, t(lang, "not_found"), show_alert=True)
            return
        media_items = await ServiceMediaRepository(session).list_for_service(service_id)
        photos = await ServiceMediaRepository(session).count_photos(service_id)
        videos = await ServiceMediaRepository(session).count_videos(service_id)
    await safe_callback_answer(callback)
    await send_service_presentation(
        bot,
        callback.message.chat.id,
        service,
        media_items,
        lang,
        photos_count=photos,
        videos_count=videos,
        force_show=True,
        media_mode="open" if media_items else "card_only",
    )
