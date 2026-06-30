"""Shared aggregation used by reports, dashboard, insights, budgets, achievements."""
from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Category, Transaction, TxKind


@dataclass
class Totals:
    income: float
    expense: float

    @property
    def net(self) -> float:
        return round(self.income - self.expense, 2)


def period_bounds(period: str, today: date | None = None) -> tuple[date, date]:
    today = today or date.today()
    if period == "today" or period == "now":
        return today, today
    if period == "week":
        start = today - timedelta(days=today.weekday())
        return start, today
    if period == "month":
        return today.replace(day=1), today
    if period == "prev_month":
        first = today.replace(day=1)
        last_prev = first - timedelta(days=1)
        return last_prev.replace(day=1), last_prev
    if period == "year":
        return today.replace(month=1, day=1), today
    return today.replace(day=1), today


async def totals(session: AsyncSession, user_id: int, start: date, end: date) -> Totals:
    rows = (
        await session.execute(
            select(Transaction.kind, func.coalesce(func.sum(Transaction.amount), 0))
            .where(Transaction.user_id == user_id, Transaction.occurred_at >= start, Transaction.occurred_at <= end)
            .group_by(Transaction.kind)
        )
    ).all()
    income = expense = 0.0
    for kind, total in rows:
        if kind == TxKind.income:
            income = float(total)
        else:
            expense = float(total)
    return Totals(income=round(income, 2), expense=round(expense, 2))


async def by_category(
    session: AsyncSession, user_id: int, start: date, end: date, kind: TxKind = TxKind.expense
) -> list[dict]:
    rows = (
        await session.execute(
            select(
                Category.id, Category.name, Category.color,
                func.coalesce(func.sum(Transaction.amount), 0).label("total"),
                func.count(Transaction.id),
            )
            .join(Category, Category.id == Transaction.category_id)
            .where(
                Transaction.user_id == user_id, Transaction.kind == kind,
                Transaction.occurred_at >= start, Transaction.occurred_at <= end,
            )
            .group_by(Category.id, Category.name, Category.color)
            .order_by(func.sum(Transaction.amount).desc())
        )
    ).all()
    return [
        {"category_id": r[0], "name": r[1], "color": r[2], "total": round(float(r[3]), 2), "count": r[4]}
        for r in rows
    ]


async def daily_series(
    session: AsyncSession, user_id: int, start: date, end: date, kind: TxKind = TxKind.expense
) -> list[dict]:
    rows = (
        await session.execute(
            select(Transaction.occurred_at, func.coalesce(func.sum(Transaction.amount), 0))
            .where(
                Transaction.user_id == user_id, Transaction.kind == kind,
                Transaction.occurred_at >= start, Transaction.occurred_at <= end,
            )
            .group_by(Transaction.occurred_at)
            .order_by(Transaction.occurred_at)
        )
    ).all()
    by_day = {r[0]: round(float(r[1]), 2) for r in rows}
    out = []
    cur = start
    while cur <= end:
        out.append({"date": cur.isoformat(), "amount": by_day.get(cur, 0.0)})
        cur += timedelta(days=1)
    return out


def days_in_month(today: date | None = None) -> tuple[int, int]:
    today = today or date.today()
    total = calendar.monthrange(today.year, today.month)[1]
    return today.day, total
