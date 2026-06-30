"""Localized bot command menu. Re-applied per-user on language switch (TZ §3)."""
from __future__ import annotations

from aiogram.types import BotCommand, BotCommandScopeChat, BotCommandScopeDefault

from app.bot.loader import bot
from app.core.i18n import t

_KEYS = [
    ("app", "cmd_app"), ("report", "cmd_report"), ("balance", "cmd_balance"),
    ("history", "cmd_history"), ("export", "cmd_export"), ("language", "cmd_language"),
    ("currency", "cmd_currency"), ("premium", "cmd_premium"), ("help", "cmd_help"),
]


def _commands(lang: str) -> list[BotCommand]:
    return [BotCommand(command=cmd, description=t(lang, key)) for cmd, key in _KEYS]


async def set_default_commands() -> None:
    await bot.set_my_commands(_commands("en"), scope=BotCommandScopeDefault())
    await bot.set_my_commands(_commands("ru"), scope=BotCommandScopeDefault(), language_code="ru")


async def set_user_commands(chat_id: int, lang: str) -> None:
    await bot.set_my_commands(_commands(lang), scope=BotCommandScopeChat(chat_id=chat_id))
