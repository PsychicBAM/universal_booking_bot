from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.utils.callbacks import safe_callback_answer

from app.bot.i18n import t
from app.bot.keyboards import (
    ADMIN_MENU_TEXTS,
    BACK_MAIN_TEXTS,
    LANGUAGE_TEXTS,
    admin_menu,
    language_kb,
    main_menu,
)
from app.config import get_settings
from app.database.session import async_session_factory
from app.repositories import ClientRepository

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, is_admin: bool, lang: str) -> None:
    await state.clear()
    settings = get_settings()
    contact = settings.contact_admin_username
    contact_line = t(lang, "support_line", username=contact.lstrip("@")) if contact else ""
    await message.answer(
        f"{t(lang, 'welcome')}\n\n{t(lang, 'welcome_sub')}{contact_line}",
        reply_markup=main_menu(is_admin, lang),
    )


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
async def choose_language(message: Message, lang: str) -> None:
    await message.answer(t(lang, "language_choose"), reply_markup=language_kb())


@router.callback_query(F.data.startswith("lang:"))
async def set_language(callback: CallbackQuery, is_admin: bool) -> None:
    lang = callback.data.split(":")[1]
    settings = get_settings()
    if lang not in settings.supported_languages:
        await safe_callback_answer(callback, t(lang, "unsupported_language"), show_alert=True)
        return
    async with async_session_factory() as session:
        await ClientRepository(session).set_language(callback.from_user.id, lang)
        await session.commit()
    await callback.message.edit_text(t(lang, "language_set"))
    await callback.message.answer(t(lang, "main_menu"), reply_markup=main_menu(is_admin, lang))
    await safe_callback_answer(callback)
