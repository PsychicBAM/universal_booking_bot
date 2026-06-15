from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.handlers.unavailable import _format_item_line
from app.bot.handlers.working_hours import format_schedule_text
from app.bot.i18n import t
from app.bot.keyboards import ADMIN_SCHEDULE_TEXTS, admin_menu
from app.bot.keyboards.schedule_kb import schedule_main_kb, schedule_quick_kb
from app.bot.utils.callbacks import safe_callback_answer
from app.bot.utils.telegram_ui import edit_or_send, safe_edit_text
from app.database.session import async_session_factory
from app.services.unavailable_service import list_upcoming_unavailable
from app.services.working_hours_service import get_weekly_schedule

router = Router()


async def build_schedule_main_text(lang: str) -> str:
    async with async_session_factory() as session:
        schedules = await get_weekly_schedule(session)
        items = await list_upcoming_unavailable(session)

    lines = [t(lang, "schedule_title"), "", t(lang, "schedule_wh_section")]
    lines.append(format_schedule_text(schedules, lang))
    lines.extend(["", t(lang, "schedule_unav_section")])
    if items:
        for item in items[:7]:
            lines.append(_format_item_line(item, lang))
        if len(items) > 7:
            lines.append(t(lang, "schedule_unav_more", count=str(len(items) - 7)))
    else:
        lines.append(t(lang, "schedule_unav_empty"))
    return "\n".join(lines)


async def show_schedule_main(event: Message | CallbackQuery, lang: str) -> None:
    text = await build_schedule_main_text(lang)
    keyboard = schedule_main_kb(lang)
    if isinstance(event, CallbackQuery):
        await edit_or_send(event, text, reply_markup=keyboard)
    else:
        await event.answer(text, reply_markup=keyboard)


@router.message(F.text.in_(ADMIN_SCHEDULE_TEXTS))
async def open_schedule_from_reply(
    message: Message,
    state: FSMContext,
    is_admin: bool,
    lang: str,
) -> None:
    if not is_admin:
        return
    if await state.get_state():
        await state.clear()
    await show_schedule_main(message, lang)


@router.callback_query(F.data == "sch:main")
async def schedule_main_callback(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    await safe_callback_answer(callback)
    await show_schedule_main(callback, lang)


@router.callback_query(F.data == "sch:back")
async def schedule_back_admin(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    await safe_callback_answer(callback)
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(t(lang, "admin_panel"), reply_markup=admin_menu(lang))


@router.callback_query(F.data == "sch:quick")
async def schedule_quick_callback(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    await safe_callback_answer(callback)
    await safe_edit_text(
        callback.message,
        t(lang, "schedule_quick_title"),
        reply_markup=schedule_quick_kb(lang),
    )
