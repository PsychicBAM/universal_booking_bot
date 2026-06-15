import logging
import re

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.i18n import t
from app.bot.keyboards import cancel_kb
from app.bot.keyboards.confirmation_settings_kb import (
    confirmation_main_text_kb,
    confirmation_responses_kb,
    confirmation_reset_confirm_kb,
)
from app.bot.settings_ui import (
    edit_confirmation_group_main,
    edit_confirmation_group_responses,
    edit_confirmation_language_menu,
    edit_confirmation_language_select,
    edit_confirmation_reset_confirm,
    send_confirmation_language_menu,
)
from app.bot.states import AdminConfirmationTextStates
from app.bot.utils.callbacks import safe_callback_answer
from app.database.session import async_session_factory
from app.services.confirmation_text_service import (
    FIELD_MAX_LEN,
    load_confirmation_text_config,
    reset_confirmation_texts,
    save_confirmation_text,
    send_confirmation_preview,
    validate_confirmation_value,
)
from app.services.language_service import parse_enabled_languages_value

router = Router()
logger = logging.getLogger(__name__)

VALID_FIELDS = frozenset(
    {
        "title",
        "question",
        "yes_button",
        "no_button",
        "yes_response",
        "no_action_prompt",
        "yes_admin",
        "no_admin",
    }
)
VALID_LANGS = frozenset({"ru", "en"})

FIELD_EDIT_LABEL = {
    "title": "confirm_edit_title_plain",
    "question": "confirm_edit_question_plain",
    "yes_button": "confirm_edit_confirm_button",
    "no_button": "confirm_edit_change_button",
    "yes_response": "confirm_edit_client_confirm_response",
    "no_action_prompt": "confirm_edit_client_change_prompt",
    "yes_admin": "confirm_edit_admin_confirm_notice",
    "no_admin": "confirm_edit_admin_change_notice",
}

_LANG_RE = re.compile(r"^(ru|en)$")


async def _enabled_codes(telegram_id: int) -> list[str]:
    from app.services.bot_settings_service import load_bot_settings_snapshot

    async with async_session_factory() as session:
        snapshot = await load_bot_settings_snapshot(session, telegram_id)
    return parse_enabled_languages_value(",".join(snapshot.enabled_languages))


def _parse_lang_suffix(data: str, prefix: str) -> str | None:
    if not data.startswith(prefix):
        return None
    lang_code = data[len(prefix) :]
    return lang_code if _LANG_RE.match(lang_code) else None


@router.callback_query(F.data == "conf:open")
async def conf_open(callback: CallbackQuery, is_admin: bool, lang: str, state: FSMContext) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    await safe_callback_answer(callback)
    await state.clear()
    codes = await _enabled_codes(callback.from_user.id)
    if len(codes) == 1:
        await edit_confirmation_language_menu(callback, lang, codes[0], multi_lang=False)
    else:
        await edit_confirmation_language_select(callback, lang)


@router.callback_query(F.data == "conf:back")
async def conf_back(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    await safe_callback_answer(callback)
    await edit_confirmation_language_select(callback, lang)


@router.callback_query(F.data.regexp(r"^conf:lang:(ru|en)$"))
async def conf_lang(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    target_lang = callback.data.rsplit(":", 1)[-1]
    await safe_callback_answer(callback)
    await edit_confirmation_language_menu(callback, lang, target_lang, multi_lang=True)


@router.callback_query(F.data.regexp(r"^conf:back:lang:(ru|en)$"))
async def conf_back_lang(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    target_lang = callback.data.rsplit(":", 1)[-1]
    codes = await _enabled_codes(callback.from_user.id)
    await safe_callback_answer(callback)
    await edit_confirmation_language_menu(
        callback, lang, target_lang, multi_lang=len(codes) > 1
    )


@router.callback_query(F.data.regexp(r"^conf:group:main:(ru|en)$"))
async def conf_group_main(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    target_lang = callback.data.rsplit(":", 1)[-1]
    await safe_callback_answer(callback)
    await edit_confirmation_group_main(callback, lang, target_lang)


@router.callback_query(F.data.regexp(r"^conf:group:responses:(ru|en)$"))
async def conf_group_responses(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    target_lang = callback.data.rsplit(":", 1)[-1]
    await safe_callback_answer(callback)
    await edit_confirmation_group_responses(callback, lang, target_lang)


@router.callback_query(F.data == "conf:noop")
async def conf_preview_noop(callback: CallbackQuery, lang: str) -> None:
    await safe_callback_answer(callback, t(lang, "confirm_preview_hint"), show_alert=True)


@router.callback_query(F.data.regexp(r"^conf:preview:(ru|en)$"))
async def conf_preview(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    preview_lang = callback.data.rsplit(":", 1)[-1]
    await safe_callback_answer(callback)
    async with async_session_factory() as session:
        config = await load_confirmation_text_config(session)
    await send_confirmation_preview(callback.message, preview_lang, config)


@router.callback_query(F.data.regexp(r"^conf:reset:ask:(ru|en)$"))
async def conf_reset_ask(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    target_lang = callback.data.rsplit(":", 1)[-1]
    await safe_callback_answer(callback)
    await edit_confirmation_reset_confirm(callback, lang, target_lang)


@router.callback_query(F.data.regexp(r"^conf:reset:yes:(ru|en)$"))
async def conf_reset_yes(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    target_lang = callback.data.rsplit(":", 1)[-1]
    await safe_callback_answer(callback)
    async with async_session_factory() as session:
        await reset_confirmation_texts(session, target_lang)
        await session.commit()
    codes = await _enabled_codes(callback.from_user.id)
    await edit_confirmation_language_menu(
        callback, lang, target_lang, multi_lang=len(codes) > 1
    )


@router.callback_query(F.data.regexp(r"^conf:reset:no:(ru|en)$"))
async def conf_reset_no(callback: CallbackQuery, is_admin: bool, lang: str) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    target_lang = callback.data.rsplit(":", 1)[-1]
    codes = await _enabled_codes(callback.from_user.id)
    await safe_callback_answer(callback)
    await edit_confirmation_language_menu(
        callback, lang, target_lang, multi_lang=len(codes) > 1
    )


@router.callback_query(F.data.regexp(r"^conf:edit:[a-z_]+:(ru|en)$"))
async def conf_edit_start(callback: CallbackQuery, is_admin: bool, lang: str, state: FSMContext) -> None:
    if not is_admin:
        await safe_callback_answer(callback, t(lang, "access_denied"), show_alert=True)
        return
    parts = callback.data.split(":")
    if len(parts) != 4:
        await safe_callback_answer(callback)
        return
    field, text_lang = parts[2], parts[3]
    if field not in VALID_FIELDS or text_lang not in VALID_LANGS:
        await safe_callback_answer(callback)
        return
    label_key = FIELD_EDIT_LABEL[field]
    max_len = FIELD_MAX_LEN.get(field, 500)
    await state.update_data(
        flow_origin="admin_confirmation_settings",
        confirm_field=field,
        confirm_lang=text_lang,
    )
    await state.set_state(AdminConfirmationTextStates.entering_value)
    await safe_callback_answer(callback)
    await callback.message.answer(
        t(lang, "confirm_edit_prompt", field=t(lang, label_key), max_len=str(max_len)),
        reply_markup=cancel_kb(lang),
    )


@router.message(AdminConfirmationTextStates.entering_value, F.text)
async def conf_edit_save(message: Message, state: FSMContext, lang: str) -> None:
    data = await state.get_data()
    field = data.get("confirm_field")
    text_lang = data.get("confirm_lang")
    if not field or text_lang not in VALID_LANGS:
        await state.clear()
        await message.answer(t(lang, "error_generic"))
        return
    error_key = validate_confirmation_value(field, message.text)
    if error_key:
        max_len = FIELD_MAX_LEN.get(field, 500)
        await message.answer(t(lang, error_key, max_len=str(max_len)))
        return
    async with async_session_factory() as session:
        await save_confirmation_text(session, field, text_lang, message.text)
        await session.commit()
    await state.clear()
    await message.answer(t(lang, "settings_saved", key=field))
    codes = await _enabled_codes(message.from_user.id)
    await send_confirmation_language_menu(
        message, lang, text_lang, multi_lang=len(codes) > 1
    )
