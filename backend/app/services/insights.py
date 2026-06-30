"""Insights: this month vs last + forecast to month end (TZ §12.6)."""
from __future__ import annotations

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.services import analytics


async def month_insights(session: AsyncSession, user_id: int, today: date | None = None) -> dict:
    today = today or date.today()
    cur_start, cur_end = analytics.period_bounds("month", today)
    prev_start, prev_end = analytics.period_bounds("prev_month", today)

    cur = await analytics.totals(session, user_id, cur_start, cur_end)
    prev = await analytics.totals(session, user_id, prev_start, prev_end)

    day, total_days = analytics.days_in_month(today)
    # linear forecast of expenses for the full month based on run-rate
    run_rate = cur.expense / day if day else 0
    forecast = round(run_rate * total_days, 2)

    def pct(now: float, before: float) -> float | None:
        if before <= 0:
            return None
        return round((now - before) / before * 100, 1)

    return {
        "current": {"income": cur.income, "expense": cur.expense, "net": cur.net},
        "previous": {"income": prev.income, "expense": prev.expense, "net": prev.net},
        "expense_change_pct": pct(cur.expense, prev.expense),
        "income_change_pct": pct(cur.income, prev.income),
        "forecast_expense": forecast,
        "days_elapsed": day,
        "days_total": total_days,
    }
