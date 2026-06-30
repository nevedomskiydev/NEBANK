"""API auth dependency: validate Telegram WebApp initData -> User."""
from __future__ import annotations

import secrets

from fastapi import Depends, Header, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import AuthError, validate_init_data
from app.db import get_session
from app.models import User


def _gen_referral() -> str:
    return secrets.token_urlsafe(6)[:8]


async def get_current_user(
    x_init_data: str | None = Header(default=None, alias="X-Init-Data"),
    init_data_q: str | None = Query(default=None, alias="initData"),
    session: AsyncSession = Depends(get_session),
) -> User:
    raw = x_init_data or init_data_q
    try:
        tg_user = validate_init_data(raw or "")
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=f"auth: {exc}") from exc

    tg_id = int(tg_user["id"])
    user = (await session.execute(select(User).where(User.telegram_id == tg_id))).scalar_one_or_none()
    if user is None:
        lang = "ru" if (tg_user.get("language_code") or "").startswith("ru") else "en"
        user = User(
            telegram_id=tg_id,
            username=tg_user.get("username"),
            first_name=tg_user.get("first_name"),
            language=lang,
            voice_lang=lang,
            referral_code=_gen_referral(),
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user
