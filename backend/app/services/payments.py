"""Telegram Stars monetization (TZ §14). Premium ~= 250 Stars / month."""
from __future__ import annotations

from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Payment, User, utcnow

PREMIUM_PAYLOAD = "nebank_premium_month"


async def activate_premium(session: AsyncSession, user: User, stars: int, charge_id: str | None) -> None:
    now = utcnow()
    base = user.premium_until if (user.premium_until and user.premium_until > now) else now
    user.premium_until = base + timedelta(days=settings.premium_period_days)
    user.is_premium = True
    session.add(Payment(user_id=user.id, stars=stars, kind="premium",
                        payload=PREMIUM_PAYLOAD, charge_id=charge_id))
    await session.flush()


def is_premium(user: User) -> bool:
    if not user.is_premium:
        return False
    if user.premium_until is None:
        return False
    return user.premium_until > utcnow()
