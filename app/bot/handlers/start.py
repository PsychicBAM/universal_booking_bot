from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.utils.callbacks import safe_callback_answer
from app.bot.utils.telegram_ui import safe_edit_text

from app.bot.i18n import t
from app.bot.keyboards import (
    ADMIN_MENU_TEXTS,
    BACK_MAIN_TEXTS,
    LANGUAGE_TEXTS,
    admin_menu,
    language_kb,
    main_menu,
)
from app.database.session import async_session_factory
from app.repositories import ClientRepository
from app.services.language_service import effective_lang, parse_enabled_languages_value
from app.services.start_screen_service import deliver_start_screen

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, is_admin: bool, lang: str) -> None:
    await state.clear()
    await deliver_start_screen(message, is_admin=is_admin, lang=lang)


@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext, is_admin: bool, lang: str) -> None:
    await state.clear()
    if not is_admin:
        await message.answer(t(lang, "access_denied"))
        return
    await message.answer(t(lang, "admin_panel"), reply_markup=admin_menu(lang))


@router.message(F.text.in_(ADMIN_MENU_TEXTS))
async def open_admin(message: Message, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await message.answer(t(lang, "access_denied"))
        return
    await message.answer(t(lang, "admin_panel"), reply_markup=admin_menu(lang))


@router.message(F.text.in_(BACK_MAIN_TEXTS))
async def back_main(message: Message, is_admin: bool, lang: str) -> None:
    await message.answer(t(lang, "main_menu"), reply_markup=main_menu(is_admin, lang))


@router.message(F.text.in_(LANGUAGE_TEXTS))
async def choose_language(
    message: Message,
    is_admin: bool,
    lang: str,
    language_switching_enabled: bool,
    enabled_languages: list[str],
) -> None:
    if not language_switching_enabled:
        forced = effective_lang(lang, enabled_languages, lang)
        await message.answer(t(forced, "language_switching_disabled"), reply_markup=main_menu(is_admin, forced))
        return
    await message.answer(t(lang, "language_choose"), reply_markup=language_kb(enabled_languages))


@router.callback_query(F.data.startswith("lang:"))
async def set_language(
    callback: CallbackQuery,
    is_admin: bool,
    lang: str,
    language_switching_enabled: bool,
    enabled_languages: list[str],
) -> None:
    new_lang = callback.data.split(":")[1]
    codes = parse_enabled_languages_value(",".join(enabled_languages))
    if not language_switching_enabled or new_lang not in codes:
        forced = effective_lang(lang, codes, lang)
        await safe_callback_answer(callback, t(forced, "language_switching_disabled"), show_alert=True)
        await callback.message.answer(t(forced, "main_menu"), reply_markup=main_menu(is_admin, forced))
        return
    async with async_session_factory() as session:
        await ClientRepository(session).set_language(callback.from_user.id, new_lang)
        await session.commit()
    await safe_edit_text(callback.message, t(new_lang, "language_set"))
    await callback.message.answer(t(new_lang, "main_menu"), reply_markup=main_menu(is_admin, new_lang))
    await safe_callback_answer(callback)
