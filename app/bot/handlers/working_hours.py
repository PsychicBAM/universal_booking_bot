import re

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.utils.callbacks import safe_callback_answer

from app.bot.i18n import CANCEL_TEXTS, t, weekday_name
from app.bot.keyboards import ADMIN_WH_TEXTS, admin_menu, cancel_kb
from app.bot.keyboards.working_hours_kb import (
    working_hours_day_kb,
    working_hours_main_kb,
    working_hours_presets_kb,
    working_hours_time_presets_kb,
    working_hours_week_off_confirm_kb,
)
from app.bot.states import AdminWorkingHoursStates
from app.database.session import async_session_factory
from app.services.working_hours_service import (
    DAY_TIME_PRESETS,
    DaySchedule,
    apply_weekly_preset,
    get_day_schedule,
    get_weekly_schedule,
    make_next_7_days_unavailable,
    set_day_working_hours,
    toggle_day,
)
from app.utils.formatting import parse_time

router = Router()

TIME_RANGE_RE = re.compile(r"^(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})$")


def format_schedule_text(schedules: list[DaySchedule], lang: str) -> str:
    lines = [t(lang, "wh_current_schedule")]
    for schedule in schedules:
        day = weekday_name(lang, schedule.day_of_week)
        if schedule.is_working and schedule.start_time and schedule.end_time:
            lines.append(
                t(
                    lang,
                    "wh_day_line_working",
                    day=day,
                    start=schedule.start_time.strftime("%H:%M"),
                    end=schedule.end_time.strftime("%H:%M"),
                )
            )
        else:
            lines.append(t(lang, "wh_day_line_off", day=day))
    return "\n".join(lines)


def format_day_detail(schedule: DaySchedule, lang: str) -> str:
    day = weekday_name(lang, schedule.day_of_week)
    if schedule.is_working and schedule.start_time and schedule.end_time:
        return t(
            lang,
            "wh_day_detail_working",
            day=day,
            start=schedule.start_time.strftime("%H:%M"),
            end=schedule.end_time.strftime("%H:%M"),
        )
    return t(lang, "wh_day_detail_off", day=day)


async def build_working_hours_main_text(lang: str) -> str:
    async with async_session_factory() as session:
        schedules = await get_weekly_schedule(session)
    return f"{t(lang, 'wh_title')}\n\n{format_schedule_text(schedules, lang)}"


async def show_working_hours_menu(event: Message | CallbackQuery, lang: str) -> None:
    text = await build_working_hours_main_text(lang)
    keyboard = working_hours_main_kb(lang)
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=keyboard)
    else:
        await event.answer(text, reply_markup=keyboard)


async def send_working_hours_main(message: Message, lang: str) -> None:
    await show_working_hours_menu(message, lang)


@router.message(F.text.in_(ADMIN_WH_TEXTS))
async def open_working_hours_from_reply(
    message: Message,
    state: FSMContext,
    is_admin: bool,
    lang: str,
) -> None:
    if not is_admin:
        return
    if await state.get_state():
        await state.clear()
    await show_working_hours_menu(message, lang)


@router.callback_query(F.data == "wh:list")
async def wh_list(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    await show_working_hours_menu(callback, lang)
    await safe_callback_answer(callback)


@router.callback_query(F.data == "wh:back")
async def wh_back_admin(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    await callback.message.delete()
    await callback.message.answer(t(lang, "admin_panel"), reply_markup=admin_menu(lang))
    await safe_callback_answer(callback)


@router.callback_query(F.data.regexp(r"^wh:day:\d+$"))
async def wh_day_detail(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    day = int(callback.data.split(":")[2])
    async with async_session_factory() as session:
        schedule = await get_day_schedule(session, day)
    await callback.message.edit_text(
        format_day_detail(schedule, lang),
        reply_markup=working_hours_day_kb(day, schedule.is_working, lang),
    )
    await safe_callback_answer(callback)


@router.callback_query(F.data.regexp(r"^wh:day:toggle:\d+$"))
async def wh_day_toggle(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    day = int(callback.data.split(":")[3])
    async with async_session_factory() as session:
        await toggle_day(session, day)
        await session.commit()
        schedule = await get_day_schedule(session, day)
    await callback.message.edit_text(
        format_day_detail(schedule, lang),
        reply_markup=working_hours_day_kb(day, schedule.is_working, lang),
    )
    await safe_callback_answer(callback, t(lang, "wh_updated"))


@router.callback_query(F.data.regexp(r"^wh:day:time:\d+$"))
async def wh_day_time_presets(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    day = int(callback.data.split(":")[3])
    await callback.message.edit_text(
        t(lang, "wh_choose_time"),
        reply_markup=working_hours_time_presets_kb(day, lang),
    )
    await safe_callback_answer(callback)


@router.callback_query(F.data.regexp(r"^wh:ds:\d+:\d+$"))
async def wh_day_set_preset(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    _, _, day_s, idx_s = callback.data.split(":")
    day = int(day_s)
    idx = int(idx_s)
    start, end = DAY_TIME_PRESETS[idx]
    async with async_session_factory() as session:
        await set_day_working_hours(session, day, start, end)
        await session.commit()
        schedule = await get_day_schedule(session, day)
    await callback.message.edit_text(
        format_day_detail(schedule, lang),
        reply_markup=working_hours_day_kb(day, schedule.is_working, lang),
    )
    await safe_callback_answer(callback, t(lang, "wh_updated"))


@router.callback_query(F.data.regexp(r"^wh:day:manual:\d+$"))
async def wh_day_manual_start(callback: CallbackQuery, state: FSMContext, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    day = int(callback.data.split(":")[3])
    await state.update_data(wh_day=day, flow_origin="admin", wh_cancel_to="schedule")
    await state.set_state(AdminWorkingHoursStates.manual_time)
    await callback.message.answer(t(lang, "wh_manual_prompt"), reply_markup=cancel_kb(lang))
    await safe_callback_answer(callback)


@router.message(AdminWorkingHoursStates.manual_time, F.text)
async def wh_day_manual_save(message: Message, state: FSMContext, lang: str) -> None:
    text = message.text.strip().replace("–", "-")
    match = TIME_RANGE_RE.match(text)
    if not match:
        await message.answer(t(lang, "wh_invalid_time_format"))
        return
    start = parse_time(match.group(1))
    end = parse_time(match.group(2))
    if not start or not end or start >= end:
        await message.answer(t(lang, "wh_invalid_time_format"))
        return
    data = await state.get_data()
    day = data["wh_day"]
    async with async_session_factory() as session:
        await set_day_working_hours(session, day, start, end)
        await session.commit()
        schedule = await get_day_schedule(session, day)
    await state.clear()
    await message.answer(
        format_day_detail(schedule, lang),
        reply_markup=working_hours_day_kb(day, schedule.is_working, lang),
    )


@router.callback_query(F.data == "wh:presets")
async def wh_presets_menu(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    await callback.message.edit_text(
        t(lang, "wh_presets_title"),
        reply_markup=working_hours_presets_kb(lang),
    )
    await safe_callback_answer(callback)


@router.callback_query(F.data.startswith("wh:preset:"))
async def wh_apply_preset(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    preset_key = callback.data.removeprefix("wh:preset:")
    async with async_session_factory() as session:
        await apply_weekly_preset(session, preset_key)
        await session.commit()
    await safe_callback_answer(callback, t(lang, "wh_preset_applied"))
    await show_working_hours_menu(callback, lang)


@router.callback_query(F.data == "wh:week_off")
async def wh_week_off_confirm(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    await callback.message.edit_text(
        t(lang, "wh_week_off_confirm_text"),
        reply_markup=working_hours_week_off_confirm_kb(lang),
    )
    await safe_callback_answer(callback)


@router.callback_query(F.data == "wh:week_off_confirm")
async def wh_week_off_apply(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    async with async_session_factory() as session:
        await make_next_7_days_unavailable(session)
        await session.commit()
    await safe_callback_answer(callback, t(lang, "wh_week_off_done"))
    await show_working_hours_menu(callback, lang)
