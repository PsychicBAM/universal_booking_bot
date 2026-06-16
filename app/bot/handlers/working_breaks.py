from datetime import time

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.handlers.working_hours import show_day_detail
from app.bot.i18n import t
from app.bot.keyboards import SKIP_TEXTS, cancel_kb, skip_cancel_kb
from app.bot.keyboards.working_breaks_kb import (
    working_break_add_choice_kb,
    working_break_delete_confirm_kb,
    working_break_edit_kb,
    working_breaks_day_kb,
    working_break_weekday_pick_kb,
)
from app.bot.states import WorkingBreakStates
from app.bot.utils.callbacks import safe_callback_answer
from app.bot.utils.telegram_ui import safe_edit_text
from app.database.session import async_session_factory
from app.repositories import WorkingBreakRepository, WorkingHoursRepository
from app.services.working_break_service import (
    format_break_line,
    format_breaks_section,
    parse_hhmm,
)

router = Router()

LUNCH_START = time(12, 0)
LUNCH_END = time(13, 0)


def _break_list_text(weekday: int, breaks: list, lang: str) -> str:
    day = t(lang, f"weekday_{weekday}")
    lines = [day, "", t(lang, "working_breaks_title") + ":"]
    if breaks:
        lines.extend(format_break_line(br) for br in breaks)
    else:
        lines.append(t(lang, "working_breaks_empty"))
    return "\n".join(lines)


async def _show_break_list(callback: CallbackQuery, weekday: int, lang: str) -> None:
    async with async_session_factory() as session:
        breaks = await WorkingBreakRepository(session).list_by_weekday(weekday, active_only=False)
    await safe_edit_text(
        callback.message,
        _break_list_text(weekday, breaks, lang),
        reply_markup=working_breaks_day_kb(weekday, breaks, lang),
    )


@router.callback_query(F.data.regexp(r"^br:list:\d+$"))
async def br_list(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    await safe_callback_answer(callback)
    weekday = int(callback.data.split(":")[2])
    await _show_break_list(callback, weekday, lang)


async def _show_add_choice(callback: CallbackQuery, weekday: int, lang: str) -> None:
    async with async_session_factory() as session:
        existing = await WorkingBreakRepository(session).list_by_weekday(weekday, active_only=False)
    show_preset = len(existing) == 0
    await safe_edit_text(
        callback.message,
        t(lang, "working_break_add_prompt"),
        reply_markup=working_break_add_choice_kb(weekday, lang, show_preset=show_preset),
    )


@router.callback_query(F.data.regexp(r"^br:add:\d+$"))
async def br_add_start(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    await safe_callback_answer(callback)
    weekday = int(callback.data.split(":")[2])
    await _show_add_choice(callback, weekday, lang)


@router.callback_query(F.data.regexp(r"^br:preset:lunch:\d+$"))
async def br_add_lunch_preset(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    weekday = int(callback.data.split(":")[3])
    async with async_session_factory() as session:
        repo = WorkingBreakRepository(session)
        wh_repo = WorkingHoursRepository(session)
        try:
            title = t(lang, "working_break_lunch_title")
            await repo.create_break(
                weekday,
                LUNCH_START,
                LUNCH_END,
                title=title,
                working_hours_repo=wh_repo,
            )
            await session.commit()
        except ValueError as exc:
            await safe_callback_answer(callback, _validation_message(lang, exc.args[0]), show_alert=True)
            return
    await safe_callback_answer(callback, t(lang, "working_break_added"))
    await show_day_detail(callback, weekday, lang)


@router.callback_query(F.data.regexp(r"^br:manual:\d+$"))
async def br_add_manual(callback: CallbackQuery, state: FSMContext, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    await safe_callback_answer(callback)
    weekday = int(callback.data.split(":")[2])
    await state.update_data(br_weekday=weekday, flow_origin="admin")
    await state.set_state(WorkingBreakStates.entering_start)
    await callback.message.answer(t(lang, "working_break_start_prompt"), reply_markup=cancel_kb(lang))


@router.callback_query(F.data == "br:add")
async def br_add_pick_weekday(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    await safe_callback_answer(callback)
    await safe_edit_text(
        callback.message,
        t(lang, "working_break_choose_weekday"),
        reply_markup=working_break_weekday_pick_kb(lang),
    )


@router.callback_query(F.data.regexp(r"^br:pick_day:\d+$"))
async def br_pick_weekday(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    await safe_callback_answer(callback)
    weekday = int(callback.data.split(":")[2])
    await _show_add_choice(callback, weekday, lang)


@router.callback_query(F.data.regexp(r"^br:edit:\d+$"))
async def br_edit_menu(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    await safe_callback_answer(callback)
    break_id = int(callback.data.split(":")[2])
    async with async_session_factory() as session:
        br = await WorkingBreakRepository(session).get_by_id(break_id)
    if not br:
        await safe_callback_answer(callback, t(lang, "working_break_not_found"), show_alert=True)
        return
    text = f"{format_break_line(br)}\n\n{t(lang, 'working_break_edit_prompt')}"
    await safe_edit_text(callback.message, text, reply_markup=working_break_edit_kb(br, lang))


@router.callback_query(F.data.regexp(r"^br:edit_time:\d+$"))
async def br_edit_time_start(callback: CallbackQuery, state: FSMContext, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    await safe_callback_answer(callback)
    break_id = int(callback.data.split(":")[2])
    await state.update_data(br_break_id=break_id, flow_origin="admin")
    await state.set_state(WorkingBreakStates.editing_start)
    await callback.message.answer(t(lang, "working_break_start_prompt"), reply_markup=cancel_kb(lang))


@router.callback_query(F.data.regexp(r"^br:edit_title:\d+$"))
async def br_edit_title_start(callback: CallbackQuery, state: FSMContext, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    await safe_callback_answer(callback)
    break_id = int(callback.data.split(":")[2])
    await state.update_data(br_break_id=break_id, flow_origin="admin")
    await state.set_state(WorkingBreakStates.editing_title)
    await callback.message.answer(
        t(lang, "working_break_title_prompt"),
        reply_markup=skip_cancel_kb(lang),
    )


@router.callback_query(F.data.regexp(r"^br:toggle:\d+$"))
async def br_toggle(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    break_id = int(callback.data.split(":")[2])
    async with async_session_factory() as session:
        repo = WorkingBreakRepository(session)
        br = await repo.get_by_id(break_id)
        if not br:
            await safe_callback_answer(callback, t(lang, "working_break_not_found"), show_alert=True)
            return
        await repo.update_break(break_id, is_active=not br.is_active)
        await session.commit()
        br = await repo.get_by_id(break_id)
    await safe_callback_answer(callback, t(lang, "working_break_updated"))
    await safe_edit_text(callback.message, format_break_line(br), reply_markup=working_break_edit_kb(br, lang))


@router.callback_query(F.data.regexp(r"^br:delete:\d+$"))
async def br_delete_confirm(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    await safe_callback_answer(callback)
    break_id = int(callback.data.split(":")[2])
    async with async_session_factory() as session:
        br = await WorkingBreakRepository(session).get_by_id(break_id)
    if not br:
        await safe_callback_answer(callback, t(lang, "working_break_not_found"), show_alert=True)
        return
    await safe_edit_text(
        callback.message,
        t(lang, "working_break_delete_confirm"),
        reply_markup=working_break_delete_confirm_kb(break_id, br.weekday, lang),
    )


@router.callback_query(F.data.regexp(r"^br:delete:yes:\d+$"))
async def br_delete_yes(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    break_id = int(callback.data.split(":")[3])
    async with async_session_factory() as session:
        repo = WorkingBreakRepository(session)
        br = await repo.get_by_id(break_id)
        if not br:
            await safe_callback_answer(callback, t(lang, "working_break_not_found"), show_alert=True)
            return
        weekday = br.weekday
        await repo.delete_break(break_id)
        await session.commit()
    await safe_callback_answer(callback, t(lang, "working_break_deleted"))
    await show_day_detail(callback, weekday, lang)


@router.callback_query(F.data.regexp(r"^br:back:weekday:\d+$"))
async def br_back_weekday(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    await safe_callback_answer(callback)
    weekday = int(callback.data.split(":")[3])
    await show_day_detail(callback, weekday, lang)


def _validation_message(lang: str, code: str) -> str:
    if code == "invalid_time":
        return t(lang, "working_break_invalid_time")
    if code in ("invalid_range", "outside_hours", "day_off", "duplicate_break"):
        return t(lang, "working_break_invalid_range")
    return t(lang, "working_break_invalid_range")


async def _save_new_break(message: Message, state: FSMContext, lang: str, title: str | None) -> None:
    data = await state.get_data()
    weekday = data["br_weekday"]
    start = parse_hhmm(data["br_start"])
    end = parse_hhmm(data["br_end"])
    async with async_session_factory() as session:
        repo = WorkingBreakRepository(session)
        wh_repo = WorkingHoursRepository(session)
        try:
            await repo.create_break(weekday, start, end, title=title, working_hours_repo=wh_repo)
            await session.commit()
        except ValueError as exc:
            await message.answer(_validation_message(lang, exc.args[0]))
            return
    await state.clear()
    await message.answer(t(lang, "working_break_added"))
    from app.bot.handlers.working_hours import send_day_detail_message

    await send_day_detail_message(message, weekday, lang)


@router.message(WorkingBreakStates.entering_start, F.text)
async def br_enter_start(message: Message, state: FSMContext, lang: str) -> None:
    try:
        parse_hhmm(message.text.strip())
    except ValueError:
        await message.answer(t(lang, "working_break_invalid_time"))
        return
    await state.update_data(br_start=message.text.strip())
    await state.set_state(WorkingBreakStates.entering_end)
    await message.answer(t(lang, "working_break_end_prompt"), reply_markup=cancel_kb(lang))


@router.message(WorkingBreakStates.entering_end, F.text)
async def br_enter_end(message: Message, state: FSMContext, lang: str) -> None:
    data = await state.get_data()
    try:
        start = parse_hhmm(data["br_start"])
        end = parse_hhmm(message.text.strip())
        if start >= end:
            await message.answer(t(lang, "working_break_invalid_range"))
            return
    except ValueError:
        await message.answer(t(lang, "working_break_invalid_time"))
        return
    await state.update_data(br_end=message.text.strip())
    await state.set_state(WorkingBreakStates.entering_title)
    await message.answer(t(lang, "working_break_title_prompt"), reply_markup=skip_cancel_kb(lang))


@router.message(WorkingBreakStates.entering_title, F.text.in_(SKIP_TEXTS))
async def br_enter_title_skip(message: Message, state: FSMContext, lang: str) -> None:
    await _save_new_break(message, state, lang, title=None)


@router.message(WorkingBreakStates.entering_title, F.text)
async def br_enter_title(message: Message, state: FSMContext, lang: str) -> None:
    title = message.text.strip() or None
    await _save_new_break(message, state, lang, title=title)


@router.message(WorkingBreakStates.editing_start, F.text)
async def br_edit_start(message: Message, state: FSMContext, lang: str) -> None:
    try:
        parse_hhmm(message.text.strip())
    except ValueError:
        await message.answer(t(lang, "working_break_invalid_time"))
        return
    await state.update_data(br_start=message.text.strip())
    await state.set_state(WorkingBreakStates.editing_end)
    await message.answer(t(lang, "working_break_end_prompt"), reply_markup=cancel_kb(lang))


@router.message(WorkingBreakStates.editing_end, F.text)
async def br_edit_end(message: Message, state: FSMContext, lang: str) -> None:
    data = await state.get_data()
    break_id = data["br_break_id"]
    try:
        start = parse_hhmm(data["br_start"])
        end = parse_hhmm(message.text.strip())
        if start >= end:
            await message.answer(t(lang, "working_break_invalid_range"))
            return
    except ValueError:
        await message.answer(t(lang, "working_break_invalid_time"))
        return
    async with async_session_factory() as session:
        repo = WorkingBreakRepository(session)
        wh_repo = WorkingHoursRepository(session)
        try:
            br = await repo.update_break(
                break_id,
                start_time=start,
                end_time=end,
                working_hours_repo=wh_repo,
            )
            await session.commit()
        except ValueError as exc:
            await message.answer(_validation_message(lang, exc.args[0]))
            return
    await state.clear()
    await message.answer(t(lang, "working_break_updated"))
    if br:
        await message.answer(format_break_line(br), reply_markup=working_break_edit_kb(br, lang))


@router.message(WorkingBreakStates.editing_title, F.text.in_(SKIP_TEXTS))
async def br_edit_title_skip(message: Message, state: FSMContext, lang: str) -> None:
    await _update_break_title(message, state, lang, title=None)


@router.message(WorkingBreakStates.editing_title, F.text)
async def br_edit_title_save(message: Message, state: FSMContext, lang: str) -> None:
    title = message.text.strip() or None
    await _update_break_title(message, state, lang, title=title)


async def _update_break_title(message: Message, state: FSMContext, lang: str, title: str | None) -> None:
    data = await state.get_data()
    break_id = data["br_break_id"]
    async with async_session_factory() as session:
        repo = WorkingBreakRepository(session)
        br = await repo.update_break(break_id, title=title)
        await session.commit()
    await state.clear()
    await message.answer(t(lang, "working_break_updated"))
    if br:
        await message.answer(format_break_line(br), reply_markup=working_break_edit_kb(br, lang))
