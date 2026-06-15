from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
import logging

from app.bot.utils.callbacks import safe_callback_answer
from app.bot.i18n import t
from app.bot.keyboards import main_menu

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "noop")
async def noop_callback(callback: CallbackQuery) -> None:
    await safe_callback_answer(callback)


async def _expired_session(callback: CallbackQuery, state: FSMContext, is_admin: bool, lang: str) -> None:
    await safe_callback_answer(callback, t(lang, "session_expired"), show_alert=True)
    await state.clear()
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await callback.message.answer(t(lang, "main_menu"), reply_markup=main_menu(is_admin, lang))


@router.callback_query(F.data.regexp(r"^date:\d{4}-\d{2}-\d{2}$"))
async def stale_date_callback(callback: CallbackQuery, state: FSMContext, is_admin: bool, lang: str) -> None:
    await _expired_session(callback, state, is_admin, lang)


@router.callback_query(F.data.regexp(r"^time:\d+$"))
async def stale_time_callback(callback: CallbackQuery, state: FSMContext, is_admin: bool, lang: str) -> None:
    await _expired_session(callback, state, is_admin, lang)


@router.callback_query(F.data == "confirm:yes")
async def stale_confirm_callback(callback: CallbackQuery, state: FSMContext, is_admin: bool, lang: str) -> None:
    await _expired_session(callback, state, is_admin, lang)


@router.callback_query(F.data.startswith("cb:photos:"))
async def stale_photos_callback(callback: CallbackQuery, state: FSMContext, is_admin: bool, lang: str) -> None:
    await _expired_session(callback, state, is_admin, lang)


@router.callback_query(F.data.startswith("cb:video:"))
async def stale_video_callback(callback: CallbackQuery, state: FSMContext, is_admin: bool, lang: str) -> None:
    await _expired_session(callback, state, is_admin, lang)


@router.callback_query(F.data.startswith("cb:loc:"))
async def stale_location_callback(callback: CallbackQuery, state: FSMContext, is_admin: bool, lang: str) -> None:
    await _expired_session(callback, state, is_admin, lang)


@router.callback_query(F.data == "cb:svc_back")
async def stale_back_callback(callback: CallbackQuery, state: FSMContext, is_admin: bool, lang: str) -> None:
    await _expired_session(callback, state, is_admin, lang)


@router.callback_query()
async def unknown_callback_logger(callback: CallbackQuery, lang: str = "ru") -> None:
    logger.warning(
        "UNKNOWN CALLBACK: data=%r from_user=%s",
        callback.data,
        callback.from_user.id if callback.from_user else None,
    )
    await safe_callback_answer(callback, t(lang, "unknown_action_open_again"), show_alert=True)
