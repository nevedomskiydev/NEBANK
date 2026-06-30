"""Bot helpers: user resolution + formatting."""
from __future__ import annotations

import secrets

from aiogram import types
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.currencies import fmt_amount
from app.models import User


async def get_or_create_user(session: AsyncSession, tg: types.User) -> User:
    user = (await session.execute(select(User).where(User.telegram_id == tg.id))).scalar_one_or_none()
    if user is None:
        lang = "ru" if (tg.language_code or "").startswith("ru") else "en"
        user = User(
            telegram_id=tg.id, username=tg.username, first_name=tg.first_name,
            language=lang, voice_lang=lang, referral_code=secrets.token_urlsafe(6)[:8],
        )
        session.add(user)
        await session.flush()
    return user


def line_for(entry, base_currency: str) -> str:
    title = entry.title or ""
    orig = fmt_amount(entry.amount, entry.currency)
    return f"{title} — {orig}".strip(" —")
