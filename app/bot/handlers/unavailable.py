import re
from datetime import date

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.utils.callbacks import safe_callback_answer
from app.bot.utils.telegram_ui import safe_edit_text

from app.bot.i18n import t
from app.bot.keyboards import ADMIN_UNAVAILABLE_TEXTS, admin_menu, cancel_kb
from app.bot.keyboards.unavailable_kb import (
    unavailable_confirm_kb,
    unavailable_date_picker_kb,
    unavailable_delete_confirm_kb,
    unavailable_items_kb,
    unavailable_main_kb,
    unavailable_time_presets_kb,
)
from app.bot.states import AdminUnavailableStates
from app.database.session import async_session_factory
from app.services.unavailable_service import (
    TIME_RANGE_PRESETS,
    UnavailableItem,
    block_full_day,
    block_next_7_days,
    block_time_range,
    block_tomorrow,
    date_from_offset,
    delete_unavailable,
    list_upcoming_unavailable,
)
from app.utils.datetime_utils import now_local
from app.utils.formatting import format_date, parse_date, parse_time

router = Router()

TIME_RANGE_RE = re.compile(r"^(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})$")


def _main_text(lang: str) -> str:
    return f"{t(lang, 'unav_title')}\n\n{t(lang, 'unav_intro')}"


def _format_item_line(item: UnavailableItem, lang: str) -> str:
    date_s = format_date(item.target_date)
    if item.kind == "date":
        return t(lang, "unav_item_full_day", date=date_s)
    return t(
        lang,
        "unav_item_time",
        date=date_s,
        start=item.start_time.strftime("%H:%M"),
        end=item.end_time.strftime("%H:%M"),
    )


async def show_unavailable_menu(event: Message | CallbackQuery, lang: str) -> None:
    text = _main_text(lang)
    keyboard = unavailable_main_kb(lang)
    if isinstance(event, CallbackQuery):
        await safe_edit_text(event.message,text, reply_markup=keyboard)
    else:
        await event.answer(text, reply_markup=keyboard)


async def send_unavailable_main(message: Message, lang: str) -> None:
    await show_unavailable_menu(message, lang)


async def _show_items_list(callback: CallbackQuery, lang: str) -> None:
    async with async_session_factory() as session:
        items = await list_upcoming_unavailable(session)
    if items:
        lines = [t(lang, "unav_items_title"), ""] + [_format_item_line(item, lang) for item in items]
        text = "\n".join(lines)
    else:
        text = f"{t(lang, 'unav_items_title')}\n\n{t(lang, 'unav_items_empty')}"
    await safe_edit_text(callback.message,text, reply_markup=unavailable_items_kb(items, lang))


@router.message(F.text.in_(ADMIN_UNAVAILABLE_TEXTS))
async def open_unavailable_from_reply(
    message: Message,
    state: FSMContext,
    is_admin: bool,
    lang: str,
) -> None:
    if not is_admin:
        return
    if await state.get_state():
        await state.clear()
    await state.update_data(flow_origin="admin")
    await show_unavailable_menu(message, lang)


@router.callback_query(F.data == "unav:list")
async def unav_list(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    await show_unavailable_menu(callback, lang)
    await safe_callback_answer(callback)


@router.callback_query(F.data == "unav:back")
async def unav_back_admin(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    await callback.message.delete()
    await callback.message.answer(t(lang, "admin_panel"), reply_markup=admin_menu(lang))
    await safe_callback_answer(callback)


@router.callback_query(F.data == "unav:tomorrow")
async def unav_tomorrow_confirm(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    await safe_edit_text(callback.message,
        t(lang, "unav_tomorrow_confirm_text"),
        reply_markup=unavailable_confirm_kb(
            "unav:tomorrow_confirm", "unav:list", lang, yes_key="unav_tomorrow_confirm_yes"
        ),
    )
    await safe_callback_answer(callback)


@router.callback_query(F.data == "unav:tomorrow_confirm")
async def unav_tomorrow_apply(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    async with async_session_factory() as session:
        await block_tomorrow(session)
        await session.commit()
    await safe_callback_answer(callback, t(lang, "unav_tomorrow_done"))
    await show_unavailable_menu(callback, lang)


@router.callback_query(F.data == "unav:next7")
async def unav_next7_confirm(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    await safe_edit_text(callback.message,
        t(lang, "unav_next7_confirm_text"),
        reply_markup=unavailable_confirm_kb(
            "unav:next7_confirm", "unav:list", lang, yes_key="unav_next7_confirm_yes"
        ),
    )
    await safe_callback_answer(callback)


@router.callback_query(F.data == "unav:next7_confirm")
async def unav_next7_apply(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    async with async_session_factory() as session:
        await block_next_7_days(session)
        await session.commit()
    await safe_callback_answer(callback, t(lang, "unav_next7_done"))
    await show_unavailable_menu(callback, lang)


@router.callback_query(F.data == "unav:day")
async def unav_block_day_picker(callback: CallbackQuery, state: FSMContext, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    await state.update_data(unav_flow="day", flow_origin="admin")
    await safe_edit_text(callback.message,
        t(lang, "unav_block_day"),
        reply_markup=unavailable_date_picker_kb("unav:list", lang),
    )
    await safe_callback_answer(callback)


@router.callback_query(F.data == "unav:time")
async def unav_block_time_picker(callback: CallbackQuery, state: FSMContext, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    await state.update_data(unav_flow="time", flow_origin="admin")
    await safe_edit_text(callback.message,
        t(lang, "unav_block_time"),
        reply_markup=unavailable_date_picker_kb("unav:list", lang),
    )
    await safe_callback_answer(callback)


@router.callback_query(F.data.regexp(r"^unav:dp:\d+$"))
async def unav_date_offset(callback: CallbackQuery, state: FSMContext, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    offset = int(callback.data.split(":")[2])
    target = date_from_offset(offset)
    data = await state.get_data()
    flow = data.get("unav_flow", "day")
    if flow == "time":
        await state.update_data(unav_target_date=target.isoformat())
        await safe_edit_text(callback.message,
            t(lang, "unav_block_time") + f"\n{format_date(target)}",
            reply_markup=unavailable_time_presets_kb(target, lang),
        )
    else:
        await safe_edit_text(callback.message,
            t(lang, "unav_day_confirm_text", date=format_date(target)),
            reply_markup=unavailable_confirm_kb(
                f"unav:day:confirm:{target.isoformat()}",
                "unav:day",
                lang,
                yes_key="unav_day_confirm_yes",
            ),
        )
    await safe_callback_answer(callback)


@router.callback_query(F.data == "unav:dp:manual")
async def unav_date_manual_start(callback: CallbackQuery, state: FSMContext, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    await state.update_data(flow_origin="admin")
    await state.set_state(AdminUnavailableStates.manual_date)
    await callback.message.answer(t(lang, "unav_enter_date_prompt"), reply_markup=cancel_kb(lang))
    await safe_callback_answer(callback)


@router.callback_query(F.data.startswith("unav:day:confirm:"))
async def unav_day_confirm_apply(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    iso = callback.data.removeprefix("unav:day:confirm:")
    target = date.fromisoformat(iso)
    async with async_session_factory() as session:
        await block_full_day(session, target)
        await session.commit()
    await safe_callback_answer(callback, t(lang, "unav_day_done"))
    await show_unavailable_menu(callback, lang)


@router.callback_query(F.data.regexp(r"^unav:tr:\d{4}-\d{2}-\d{2}:\w+$"))
async def unav_time_preset(callback: CallbackQuery, state: FSMContext, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    _, _, iso, action = callback.data.split(":", 3)
    target = date.fromisoformat(iso)
    if action == "manual":
        await state.update_data(unav_target_date=iso, flow_origin="admin")
        await state.set_state(AdminUnavailableStates.manual_time)
        await callback.message.answer(t(lang, "unav_enter_time_prompt"), reply_markup=cancel_kb(lang))
        await safe_callback_answer(callback)
        return
    async with async_session_factory() as session:
        if action == "fd":
            await block_full_day(session, target)
        else:
            start, end = TIME_RANGE_PRESETS[int(action)]
            await block_time_range(session, target, start, end)
        await session.commit()
    await safe_callback_answer(callback, t(lang, "unav_time_done" if action != "fd" else "unav_day_done"))
    await show_unavailable_menu(callback, lang)


@router.message(AdminUnavailableStates.manual_date, F.text)
async def unav_manual_date_save(message: Message, state: FSMContext, lang: str) -> None:
    parsed = parse_date(message.text.strip())
    if not parsed or parsed < now_local().date():
        await message.answer(t(lang, "unav_invalid_date"))
        return
    data = await state.get_data()
    flow = data.get("unav_flow", "day")
    await state.set_state(None)
    if flow == "time":
        await state.update_data(unav_target_date=parsed.isoformat())
        await message.answer(
            t(lang, "unav_block_time") + f"\n{format_date(parsed)}",
            reply_markup=unavailable_time_presets_kb(parsed, lang),
        )
        return
    await message.answer(
        t(lang, "unav_day_confirm_text", date=format_date(parsed)),
        reply_markup=unavailable_confirm_kb(
            f"unav:day:confirm:{parsed.isoformat()}",
            "unav:day",
            lang,
            yes_key="unav_day_confirm_yes",
        ),
    )


@router.message(AdminUnavailableStates.manual_time, F.text)
async def unav_manual_time_save(message: Message, state: FSMContext, lang: str) -> None:
    text = message.text.strip().replace("–", "-")
    match = TIME_RANGE_RE.match(text)
    if not match:
        await message.answer(t(lang, "unav_invalid_time"))
        return
    start = parse_time(match.group(1))
    end = parse_time(match.group(2))
    if not start or not end or start >= end:
        await message.answer(t(lang, "unav_invalid_time"))
        return
    data = await state.get_data()
    target = date.fromisoformat(data["unav_target_date"])
    async with async_session_factory() as session:
        await block_time_range(session, target, start, end)
        await session.commit()
    await state.clear()
    await message.answer(t(lang, "unav_time_done"))
    await send_unavailable_main(message, lang)


@router.callback_query(F.data == "unav:items")
async def unav_items_list(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    await _show_items_list(callback, lang)
    await safe_callback_answer(callback)


@router.callback_query(F.data.regexp(r"^unav:del:(date|time):\d+$"))
async def unav_delete_confirm(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    _, _, kind, item_id_s = callback.data.split(":")
    async with async_session_factory() as session:
        items = await list_upcoming_unavailable(session)
    item = next((i for i in items if i.kind == kind and i.id == int(item_id_s)), None)
    if not item:
        await safe_callback_answer(callback, t(lang, "not_found"), show_alert=True)
        return
    text = f"{t(lang, 'unav_delete_confirm_text')}\n\n{_format_item_line(item, lang)}"
    await safe_edit_text(callback.message,
        text,
        reply_markup=unavailable_delete_confirm_kb(kind, item.id, lang),
    )
    await safe_callback_answer(callback)


@router.callback_query(F.data.regexp(r"^unav:del_confirm:(date|time):\d+$"))
async def unav_delete_apply(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        return
    _, _, kind, item_id_s = callback.data.split(":")
    async with async_session_factory() as session:
        deleted = await delete_unavailable(session, kind, int(item_id_s))
        await session.commit()
    if not deleted:
        await safe_callback_answer(callback, t(lang, "not_found"), show_alert=True)
        return
    await safe_callback_answer(callback, t(lang, "unav_delete_done"))
    await _show_items_list(callback, lang)
