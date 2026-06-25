from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.i18n import t
from app.models import PRICE_MODE_EXACT, PRICE_MODE_FROM
from app.utils.formatting import normalize_price_mode


def admin_service_price_kb(service_id: int, service, lang: str = "ru") -> InlineKeyboardMarkup:
    mode = normalize_price_mode(service)
    exact_label = (
        f"✅ {t(lang, 'price_mode_exact')}"
        if mode == PRICE_MODE_EXACT
        else t(lang, "price_set_exact")
    )
    from_label = (
        f"✅ {t(lang, 'price_mode_from')}"
        if mode == PRICE_MODE_FROM
        else t(lang, "price_set_from")
    )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "price_change_amount"),
                    callback_data=f"adm_svc:price:amt:{service_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=exact_label,
                    callback_data=f"adm_svc:price:mode:exact:{service_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=from_label,
                    callback_data=f"adm_svc:price:mode:from:{service_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "price_back_to_service"),
                    callback_data=f"adm_svc:price:back:{service_id}",
                )
            ],
        ]
    )
