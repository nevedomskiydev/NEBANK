"""Inline keyboards. No emoji (TZ §17). Segmented-style switches (TZ §3)."""
from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import WebAppInfo

from app.config import settings
from app.core.currencies import FIAT
from app.core.i18n import t


def webapp_button(lang: str, path: str = "/") -> InlineKeyboardButton:
    url = f"{settings.public_base_url}{path}"
    return InlineKeyboardButton(text=t(lang, "open"), web_app=WebAppInfo(url=url))


def open_app_kb(lang: str, path: str = "/") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=t(lang, "open_app"),
                             web_app=WebAppInfo(url=f"{settings.public_base_url}{path}"))]])


def language_kb(current: str) -> InlineKeyboardMarkup:
    """Segmented language switch — shows both options, marks the current one."""
    def label(code: str, text: str) -> str:
        return f"· {text} ·" if code == current else text
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=label("ru", "Русский"), callback_data="lang:ru"),
        InlineKeyboardButton(text=label("en", "English"), callback_data="lang:en"),
    ]])


def currency_kb(current: str, populars=("USD", "EUR", "GBP", "RUB", "AED", "KZT", "UAH", "TRY", "JPY")) -> InlineKeyboardMarkup:
    rows, row = [], []
    for code in populars:
        mark = "· {} ·".format(code) if code == current else code
        row.append(InlineKeyboardButton(text=mark, callback_data=f"cur:{code}"))
        if len(row) == 3:
            rows.append(row); row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def after_capture_kb(lang: str, tx_ids: list[int]) -> InlineKeyboardMarkup:
    ids = ",".join(str(i) for i in tx_ids)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "open"),
                              web_app=WebAppInfo(url=f"{settings.public_base_url}/"))],
        [InlineKeyboardButton(text=t(lang, "undo"), callback_data=f"undo:{ids}"),
         InlineKeyboardButton(text=t(lang, "change_category"), callback_data=f"cat:{ids}"),
         InlineKeyboardButton(text=t(lang, "delete"), callback_data=f"del:{ids}")],
    ])


def category_pick_kb(lang: str, categories: list, tx_ids: list[int]) -> InlineKeyboardMarkup:
    ids = ",".join(str(i) for i in tx_ids)
    rows, row = [], []
    for c in categories[:18]:
        row.append(InlineKeyboardButton(text=c.name[:20], callback_data=f"setcat:{c.id}:{ids}"))
        if len(row) == 2:
            rows.append(row); row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows or [[InlineKeyboardButton(
        text=t(lang, "open_app"), web_app=WebAppInfo(url=f"{settings.public_base_url}/"))]])


def period_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=t(lang, "report_now"), callback_data="rep:today"),
        InlineKeyboardButton(text=t(lang, "report_week"), callback_data="rep:week"),
        InlineKeyboardButton(text=t(lang, "report_month"), callback_data="rep:month"),
    ]])


def yes_no_kb(lang: str, tag: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=t(lang, "yes"), callback_data=f"{tag}:yes"),
        InlineKeyboardButton(text=t(lang, "no"), callback_data=f"{tag}:no"),
    ]])


def regular_once_kb(lang: str, tx_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=t(lang, "regular"), callback_data=f"reg:{tx_id}:1"),
        InlineKeyboardButton(text=t(lang, "once"), callback_data=f"reg:{tx_id}:0"),
    ]])


def premium_kb(lang: str, stars: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=t(lang, "premium_buy", stars=stars), callback_data="buy_premium")]])
