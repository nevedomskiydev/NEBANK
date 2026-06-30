"""Subscriptions: auto-detect recurring charges + reminder scheduling (TZ §12.4)."""
from __future__ import annotations

import re
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Subscription, SubPeriod, Transaction, TxKind


def fingerprint(title: str | None, amount: float) -> str:
    base = re.sub(r"[^\wа-яё]+", "", (title or "").lower())[:24]
    return f"{base}:{round(amount)}"


def next_charge(period: SubPeriod, frm: date) -> date:
    if period == SubPeriod.weekly:
        return frm + timedelta(days=7)
    if period == SubPeriod.quarterly:
        return frm + timedelta(days=91)
    if period == SubPeriod.yearly:
        return frm + timedelta(days=365)
    # monthly
    month = frm.month % 12 + 1
    year = frm.year + (1 if frm.month == 12 else 0)
    day = min(frm.day, 28)
    return date(year, month, day)


async def detect_recurring(session: AsyncSession, user_id: int) -> list[dict]:
    """Find merchant+amount that repeats >=2 times in distinct months and isn't tracked yet."""
    rows = (await session.execute(
        select(Transaction.title, Transaction.amount, Transaction.occurred_at)
        .where(Transaction.user_id == user_id, Transaction.kind == TxKind.expense,
               Transaction.title.isnot(None))
        .order_by(Transaction.occurred_at)
    )).all()
    groups: dict[str, list] = {}
    for title, amount, day in rows:
        groups.setdefault(fingerprint(title, float(amount)), []).append((title, float(amount), day))

    tracked = {s.fingerprint for s in (await session.execute(
        select(Subscription).where(Subscription.user_id == user_id))).scalars()}

    suggestions = []
    for fp, items in groups.items():
        if fp in tracked or len(items) < 2:
            continue
        months = {(d.year, d.month) for _, _, d in items}
        if len(months) >= 2:
            last = max(items, key=lambda x: x[2])
            suggestions.append({
                "fingerprint": fp, "name": last[0], "amount": last[1],
                "last_charge": last[2].isoformat(),
                "next_charge": next_charge(SubPeriod.monthly, last[2]).isoformat(),
            })
    return suggestions


async def due_reminders(session: AsyncSession, today: date) -> list[tuple]:
    """Return (subscription, days_left) for subs needing a 3d or 1d reminder today."""
    subs = list((await session.execute(
        select(Subscription).where(Subscription.is_active == True))).scalars())  # noqa: E712
    out = []
    for s in subs:
        days_left = (s.next_charge - today).days
        if days_left == 3 and s.remind_3d_sent_for != s.next_charge:
            out.append((s, 3))
        elif days_left == 1 and s.remind_1d_sent_for != s.next_charge:
            out.append((s, 1))
        elif days_left < 0:
            # roll the charge forward so future reminders work
            s.next_charge = next_charge(s.period, s.next_charge)
    return out
