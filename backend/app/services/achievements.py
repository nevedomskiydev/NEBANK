"""12 progressive achievements computed live on real data (TZ §13).

Best result is persisted in achievement_progress; nothing is fabricated.
"""
from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    AchievementProgress,
    Budget,
    Goal,
    Habit,
    Subscription,
    Transaction,
    TxKind,
    User,
)

# code -> (en, ru, en_desc, ru_desc, target)
DEFS: list[tuple] = [
    ("streak_7", "Steady week", "Неделя дисциплины", "Log entries 7 days in a row",
     "Записи 7 дней подряд", 7),
    ("streak_30", "Month of focus", "Месяц фокуса", "Log entries 30 days in a row",
     "Записи 30 дней подряд", 30),
    ("ops_100", "Centurion", "Сотня", "Record 100 entries", "Записать 100 операций", 100),
    ("ops_500", "Archivist", "Архивариус", "Record 500 entries", "Записать 500 операций", 500),
    ("categories_5", "Explorer", "Исследователь", "Use 5 different categories",
     "Использовать 5 категорий", 5),
    ("subs_1", "Curator", "Куратор", "Track a subscription", "Вести подписку", 1),
    ("clean_30", "Thirty clean", "30 дней чисто", "30 clean days on a habit",
     "30 дней без вредной привычки", 30),
    ("clean_100", "Hundred clean", "100 дней чисто", "100 clean days on a habit",
     "100 дней без вредной привычки", 100),
    ("goal_reached", "Achiever", "Достигатель", "Reach a savings goal", "Достичь цели накоплений", 1),
    ("income_tracked", "Earner", "Учёт дохода", "Record income", "Учесть доход", 1),
    ("budget_month", "In the lines", "В рамках", "Keep a month within budget",
     "Месяц в рамках бюджета", 1),
    ("saver", "Quiet saver", "Тихий накопитель", "Round-up stash reaches 1000",
     "Заначка достигает 1000", 1000),
]


def _max_streak(days: set[date]) -> int:
    if not days:
        return 0
    best = cur = 1
    ordered = sorted(days)
    for i in range(1, len(ordered)):
        if (ordered[i] - ordered[i - 1]).days == 1:
            cur += 1
            best = max(best, cur)
        else:
            cur = 1
    return best


async def compute(session: AsyncSession, user: User) -> list[dict]:
    uid = user.id
    # gather raw signals
    op_dates = set(
        (await session.execute(select(Transaction.occurred_at).where(Transaction.user_id == uid))).scalars()
    )
    op_count = (await session.execute(
        select(func.count(Transaction.id)).where(Transaction.user_id == uid))).scalar() or 0
    cat_count = (await session.execute(
        select(func.count(func.distinct(Transaction.category_id))).where(Transaction.user_id == uid))).scalar() or 0
    sub_count = (await session.execute(
        select(func.count(Subscription.id)).where(Subscription.user_id == uid))).scalar() or 0
    income_sum = (await session.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .where(Transaction.user_id == uid, Transaction.kind == TxKind.income))).scalar() or 0
    goals_done = (await session.execute(
        select(func.count(Goal.id)).where(Goal.user_id == uid, Goal.achieved_at.isnot(None)))).scalar() or 0

    habits = list((await session.execute(select(Habit).where(Habit.user_id == uid))).scalars())
    best_clean = 0
    for h in habits:
        anchor = h.last_relapse or h.started_at
        best_clean = max(best_clean, (date.today() - anchor).days, h.best_streak)

    streak = _max_streak(op_dates)
    stash = float(user.stash_balance or 0)

    # current month within all budgets?
    budgets = list((await session.execute(select(Budget).where(Budget.user_id == uid))).scalars())
    month_ok = 1 if budgets else 0
    if budgets:
        start = date.today().replace(day=1)
        for b in budgets:
            spent = (await session.execute(
                select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                    Transaction.user_id == uid, Transaction.category_id == b.category_id,
                    Transaction.kind == TxKind.expense, Transaction.occurred_at >= start,
                ))).scalar() or 0
            if float(spent) > float(b.limit_amount):
                month_ok = 0
                break

    values = {
        "streak_7": streak, "streak_30": streak, "ops_100": op_count, "ops_500": op_count,
        "categories_5": cat_count, "subs_1": sub_count, "clean_30": best_clean, "clean_100": best_clean,
        "goal_reached": goals_done, "income_tracked": 1 if float(income_sum) > 0 else 0,
        "budget_month": month_ok, "saver": stash,
    }

    # load persisted progress
    rows = {r.code: r for r in (await session.execute(
        select(AchievementProgress).where(AchievementProgress.user_id == uid))).scalars()}

    out = []
    for code, en, ru, en_d, ru_d, target in DEFS:
        cur = float(values.get(code, 0))
        row = rows.get(code)
        if row is None:
            row = AchievementProgress(user_id=uid, code=code, best_value=cur)
            session.add(row)
        best = max(float(row.best_value or 0), cur)
        row.best_value = best
        unlocked = best >= target
        if unlocked and row.unlocked_at is None:
            from app.models import utcnow
            row.unlocked_at = utcnow()
        out.append({
            "code": code,
            "title": ru if user.language == "ru" else en,
            "description": ru_d if user.language == "ru" else en_d,
            "target": target,
            "value": min(best, target),
            "progress": min(1.0, best / target) if target else 1.0,
            "unlocked": unlocked,
        })
    await session.flush()
    return out
