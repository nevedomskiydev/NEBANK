"""NEBANK Mini App REST API. All endpoints require Telegram WebApp auth."""
from __future__ import annotations

import secrets
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.config import settings
from app.core.currencies import ALL_CURRENCIES, CRYPTO, FIAT, fmt_amount
from app.db import get_session
from app.models import (
    Budget, Category, FamilyGroup, FamilyMember, Goal, Habit, Subscription,
    SubPeriod, Transaction, TxKind, TxSource, User, utcnow,
)
from app.services import achievements as ach
from app.services import analytics, export, insights, payments, rates
from app.services import subscriptions as subs
from app.services.parser.expense_parser import ParsedEntry
from app.services.transactions import create_transaction

router = APIRouter(prefix="/api")


def _is_premium(u: User) -> bool:
    return payments.is_premium(u)


# ----------------------------------------------------------------- profile
@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "telegram_id": user.telegram_id,
        "first_name": user.first_name,
        "language": user.language,
        "base_currency": user.base_currency,
        "voice_lang": user.voice_lang,
        "theme": "light",
        "onboarded": user.onboarded,
        "is_premium": _is_premium(user),
        "premium_until": user.premium_until.isoformat() if user.premium_until else None,
        "stash_enabled": user.stash_enabled,
        "stash_round_to": user.stash_round_to,
        "stash_balance": float(user.stash_balance or 0),
        "referral_code": user.referral_code,
        "currencies": {"fiat": list(FIAT.keys()), "crypto": list(CRYPTO.keys())},
    }


class MePatch(BaseModel):
    language: str | None = None
    base_currency: str | None = None
    voice_lang: str | None = None
    onboarded: bool | None = None
    stash_enabled: bool | None = None
    stash_round_to: int | None = None


@router.patch("/me")
async def patch_me(body: MePatch, user: User = Depends(get_current_user),
                   session: AsyncSession = Depends(get_session)):
    if body.language in ("ru", "en"):
        user.language = body.language
    if body.base_currency and body.base_currency.upper() in ALL_CURRENCIES:
        user.base_currency = body.base_currency.upper()
    if body.voice_lang in ("ru", "en"):
        user.voice_lang = body.voice_lang
    if body.onboarded is not None:
        user.onboarded = body.onboarded
    if body.stash_enabled is not None:
        user.stash_enabled = body.stash_enabled
    if body.stash_round_to is not None and body.stash_round_to > 0:
        user.stash_round_to = body.stash_round_to
    await session.commit()
    return await get_me(user)


# --------------------------------------------------------------- dashboard
@router.get("/dashboard")
async def dashboard(period: str = Query("month"), user: User = Depends(get_current_user),
                    session: AsyncSession = Depends(get_session)):
    start, end = analytics.period_bounds(period)
    tot = await analytics.totals(session, user.id, start, end)
    cats = await analytics.by_category(session, user.id, start, end, TxKind.expense)
    trend = await analytics.daily_series(session, user.id, start, end, TxKind.expense)
    recent = (await session.execute(
        select(Transaction, Category.name, Category.color)
        .outerjoin(Category, Category.id == Transaction.category_id)
        .where(Transaction.user_id == user.id)
        .order_by(Transaction.occurred_at.desc(), Transaction.id.desc()).limit(12)
    )).all()
    return {
        "period": period,
        "currency": user.base_currency,
        "income": tot.income, "expense": tot.expense, "net": tot.net,
        "categories": cats,
        "trend": trend,
        "recent": [_tx_dict(t, c, col) for t, c, col in recent],
    }


def _tx_dict(t: Transaction, cat_name: str | None, cat_color: str | None) -> dict:
    return {
        "id": t.id, "kind": t.kind.value, "amount": float(t.amount),
        "original_amount": float(t.original_amount), "original_currency": t.original_currency,
        "title": t.title, "category": cat_name, "category_id": t.category_id,
        "category_color": cat_color, "source": t.source.value,
        "occurred_at": t.occurred_at.isoformat(), "crypto_network": t.crypto_network,
    }


# ------------------------------------------------------------ transactions
@router.get("/transactions")
async def list_transactions(
    from_: str | None = Query(None, alias="from"), to: str | None = Query(None),
    category_id: int | None = None, q: str | None = None,
    limit: int = Query(50, le=200), offset: int = 0,
    user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session),
):
    stmt = (select(Transaction, Category.name, Category.color)
            .outerjoin(Category, Category.id == Transaction.category_id)
            .where(Transaction.user_id == user.id))
    if from_:
        stmt = stmt.where(Transaction.occurred_at >= date.fromisoformat(from_))
    if to:
        stmt = stmt.where(Transaction.occurred_at <= date.fromisoformat(to))
    if category_id:
        stmt = stmt.where(Transaction.category_id == category_id)
    if q:
        stmt = stmt.where(Transaction.title.ilike(f"%{q}%"))
    stmt = stmt.order_by(Transaction.occurred_at.desc(), Transaction.id.desc()).limit(limit).offset(offset)
    rows = (await session.execute(stmt)).all()
    return {"items": [_tx_dict(t, c, col) for t, c, col in rows]}


class TxCreate(BaseModel):
    amount: float = Field(gt=0)
    currency: str = "USD"
    kind: str = "expense"
    title: str | None = None
    category_id: int | None = None
    occurred_at: str | None = None


@router.post("/transactions")
async def add_transaction(body: TxCreate, user: User = Depends(get_current_user),
                          session: AsyncSession = Depends(get_session)):
    day = date.fromisoformat(body.occurred_at) if body.occurred_at else date.today()
    entry = ParsedEntry(amount=body.amount, currency=body.currency.upper(),
                        kind=body.kind, title=body.title, occurred_at=day,
                        crypto_network=None, raw=body.title or "")
    tx = await create_transaction(session, user, entry, source=TxSource.manual)
    if tx is None:
        raise HTTPException(409, "duplicate")
    if body.category_id:
        tx.category_id = body.category_id
    await session.commit()
    await session.refresh(tx)
    cat = await session.get(Category, tx.category_id) if tx.category_id else None
    return _tx_dict(tx, cat.name if cat else None, cat.color if cat else None)


class TxPatch(BaseModel):
    amount: float | None = None
    title: str | None = None
    category_id: int | None = None
    occurred_at: str | None = None
    kind: str | None = None


@router.patch("/transactions/{tx_id}")
async def edit_transaction(tx_id: int, body: TxPatch, user: User = Depends(get_current_user),
                           session: AsyncSession = Depends(get_session)):
    tx = await session.get(Transaction, tx_id)
    if not tx or tx.user_id != user.id:
        raise HTTPException(404, "not found")
    if body.amount is not None and body.amount > 0:
        tx.amount = round(body.amount, 2)
    if body.title is not None:
        tx.title = body.title
    if body.category_id is not None:
        tx.category_id = body.category_id
    if body.kind in ("income", "expense"):
        tx.kind = TxKind(body.kind)
    if body.occurred_at:
        tx.occurred_at = date.fromisoformat(body.occurred_at)
    await session.commit()
    cat = await session.get(Category, tx.category_id) if tx.category_id else None
    return _tx_dict(tx, cat.name if cat else None, cat.color if cat else None)


@router.delete("/transactions/{tx_id}")
async def del_transaction(tx_id: int, user: User = Depends(get_current_user),
                          session: AsyncSession = Depends(get_session)):
    tx = await session.get(Transaction, tx_id)
    if not tx or tx.user_id != user.id:
        raise HTTPException(404, "not found")
    await session.delete(tx)
    await session.commit()
    return {"ok": True}


# --------------------------------------------------------------- categories
@router.get("/categories")
async def get_categories(user: User = Depends(get_current_user),
                         session: AsyncSession = Depends(get_session)):
    rows = (await session.execute(
        select(Category).where(Category.user_id == user.id, Category.is_archived == False)  # noqa: E712
        .order_by(Category.name))).scalars()
    return {"items": [{"id": c.id, "name": c.name, "kind": c.kind.value,
                       "color": c.color, "icon": c.icon} for c in rows]}


class CatBody(BaseModel):
    name: str
    kind: str = "expense"
    color: str = "#C9A227"


@router.post("/categories")
async def create_category(body: CatBody, user: User = Depends(get_current_user),
                          session: AsyncSession = Depends(get_session)):
    cat = Category(user_id=user.id, name=body.name.strip()[:64],
                   kind=TxKind(body.kind if body.kind in ("income", "expense") else "expense"),
                   color=body.color)
    session.add(cat)
    await session.commit()
    return {"id": cat.id, "name": cat.name, "kind": cat.kind.value, "color": cat.color}


@router.patch("/categories/{cat_id}")
async def update_category(cat_id: int, body: CatBody, user: User = Depends(get_current_user),
                          session: AsyncSession = Depends(get_session)):
    cat = await session.get(Category, cat_id)
    if not cat or cat.user_id != user.id:
        raise HTTPException(404, "not found")
    cat.name = body.name.strip()[:64]
    cat.color = body.color
    await session.commit()
    return {"id": cat.id, "name": cat.name, "color": cat.color}


@router.delete("/categories/{cat_id}")
async def delete_category(cat_id: int, user: User = Depends(get_current_user),
                          session: AsyncSession = Depends(get_session)):
    cat = await session.get(Category, cat_id)
    if not cat or cat.user_id != user.id:
        raise HTTPException(404, "not found")
    cat.is_archived = True
    await session.commit()
    return {"ok": True}


# ------------------------------------------------------------------ budgets
@router.get("/budgets")
async def get_budgets(user: User = Depends(get_current_user),
                      session: AsyncSession = Depends(get_session)):
    start, end = analytics.period_bounds("month")
    spent = {r["category_id"]: r["total"] for r in
             await analytics.by_category(session, user.id, start, end, TxKind.expense)}
    rows = (await session.execute(
        select(Budget, Category.name, Category.color)
        .join(Category, Category.id == Budget.category_id)
        .where(Budget.user_id == user.id))).all()
    out = []
    for b, name, color in rows:
        used = spent.get(b.category_id, 0.0)
        out.append({"id": b.id, "category_id": b.category_id, "name": name, "color": color,
                    "limit": float(b.limit_amount), "spent": used,
                    "progress": round(used / float(b.limit_amount), 3) if b.limit_amount else 0,
                    "over": used > float(b.limit_amount)})
    return {"items": out, "currency": user.base_currency}


class BudgetBody(BaseModel):
    category_id: int
    limit: float = Field(gt=0)


@router.put("/budgets")
async def set_budget(body: BudgetBody, user: User = Depends(get_current_user),
                     session: AsyncSession = Depends(get_session)):
    existing = (await session.execute(select(Budget).where(
        Budget.user_id == user.id, Budget.category_id == body.category_id))).scalar_one_or_none()
    if existing:
        existing.limit_amount = round(body.limit, 2)
    else:
        session.add(Budget(user_id=user.id, category_id=body.category_id, limit_amount=round(body.limit, 2)))
    await session.commit()
    return {"ok": True}


@router.delete("/budgets/{budget_id}")
async def del_budget(budget_id: int, user: User = Depends(get_current_user),
                     session: AsyncSession = Depends(get_session)):
    b = await session.get(Budget, budget_id)
    if not b or b.user_id != user.id:
        raise HTTPException(404, "not found")
    await session.delete(b)
    await session.commit()
    return {"ok": True}


# ------------------------------------------------------------ subscriptions
@router.get("/subscriptions")
async def get_subscriptions(user: User = Depends(get_current_user),
                            session: AsyncSession = Depends(get_session)):
    rows = (await session.execute(select(Subscription).where(Subscription.user_id == user.id)
            .order_by(Subscription.next_charge))).scalars()
    return {"items": [{"id": s.id, "name": s.name, "amount": float(s.amount), "currency": s.currency,
                       "period": s.period.value, "next_charge": s.next_charge.isoformat(),
                       "is_active": s.is_active, "auto_detected": s.auto_detected} for s in rows],
            "currency": user.base_currency}


@router.get("/subscriptions/suggestions")
async def sub_suggestions(user: User = Depends(get_current_user),
                          session: AsyncSession = Depends(get_session)):
    return {"items": await subs.detect_recurring(session, user.id)}


class SubBody(BaseModel):
    name: str
    amount: float = Field(gt=0)
    currency: str = "USD"
    period: str = "monthly"
    next_charge: str | None = None


@router.post("/subscriptions")
async def create_subscription(body: SubBody, user: User = Depends(get_current_user),
                              session: AsyncSession = Depends(get_session)):
    nc = date.fromisoformat(body.next_charge) if body.next_charge else \
        subs.next_charge(SubPeriod(body.period), date.today())
    s = Subscription(user_id=user.id, name=body.name[:120], amount=round(body.amount, 2),
                     currency=body.currency.upper(),
                     period=SubPeriod(body.period if body.period in
                                      [p.value for p in SubPeriod] else "monthly"),
                     next_charge=nc, fingerprint=subs.fingerprint(body.name, body.amount))
    session.add(s)
    await session.commit()
    return {"id": s.id}


@router.delete("/subscriptions/{sub_id}")
async def del_subscription(sub_id: int, user: User = Depends(get_current_user),
                           session: AsyncSession = Depends(get_session)):
    s = await session.get(Subscription, sub_id)
    if not s or s.user_id != user.id:
        raise HTTPException(404, "not found")
    await session.delete(s)
    await session.commit()
    return {"ok": True}


# -------------------------------------------------------------------- habits
@router.get("/habits")
async def get_habits(user: User = Depends(get_current_user),
                     session: AsyncSession = Depends(get_session)):
    rows = (await session.execute(select(Habit).where(Habit.user_id == user.id))).scalars()
    out = []
    for h in rows:
        anchor = h.last_relapse or h.started_at
        clean_days = max(0, (date.today() - anchor).days)
        saved = round(float(h.daily_cost) * clean_days, 2)
        out.append({"id": h.id, "name": h.name, "daily_cost": float(h.daily_cost),
                    "clean_days": clean_days, "best_streak": max(h.best_streak, clean_days),
                    "saved": saved, "started_at": h.started_at.isoformat()})
    return {"items": out, "currency": user.base_currency}


class HabitBody(BaseModel):
    name: str
    daily_cost: float = Field(ge=0, default=0)


@router.post("/habits")
async def create_habit(body: HabitBody, user: User = Depends(get_current_user),
                       session: AsyncSession = Depends(get_session)):
    h = Habit(user_id=user.id, name=body.name[:120], daily_cost=round(body.daily_cost, 2))
    session.add(h)
    await session.commit()
    return {"id": h.id}


@router.post("/habits/{habit_id}/relapse")
async def habit_relapse(habit_id: int, user: User = Depends(get_current_user),
                        session: AsyncSession = Depends(get_session)):
    h = await session.get(Habit, habit_id)
    if not h or h.user_id != user.id:
        raise HTTPException(404, "not found")
    anchor = h.last_relapse or h.started_at
    h.best_streak = max(h.best_streak, (date.today() - anchor).days)
    h.last_relapse = date.today()
    await session.commit()
    return {"ok": True, "best_streak": h.best_streak}


@router.delete("/habits/{habit_id}")
async def del_habit(habit_id: int, user: User = Depends(get_current_user),
                    session: AsyncSession = Depends(get_session)):
    h = await session.get(Habit, habit_id)
    if not h or h.user_id != user.id:
        raise HTTPException(404, "not found")
    await session.delete(h)
    await session.commit()
    return {"ok": True}


# --------------------------------------------------------------------- goals
@router.get("/goals")
async def get_goals(user: User = Depends(get_current_user),
                    session: AsyncSession = Depends(get_session)):
    rows = (await session.execute(select(Goal).where(Goal.user_id == user.id))).scalars()
    return {"items": [{"id": g.id, "name": g.name, "target": float(g.target_amount),
                       "current": float(g.current_amount),
                       "progress": round(float(g.current_amount) / float(g.target_amount), 3)
                       if g.target_amount else 0,
                       "achieved": g.achieved_at is not None} for g in rows],
            "currency": user.base_currency}


class GoalBody(BaseModel):
    name: str
    target: float = Field(gt=0)


@router.post("/goals")
async def create_goal(body: GoalBody, user: User = Depends(get_current_user),
                      session: AsyncSession = Depends(get_session)):
    g = Goal(user_id=user.id, name=body.name[:120], target_amount=round(body.target, 2))
    session.add(g)
    await session.commit()
    return {"id": g.id}


class TopUp(BaseModel):
    amount: float = Field(gt=0)


@router.post("/goals/{goal_id}/topup")
async def topup_goal(goal_id: int, body: TopUp, user: User = Depends(get_current_user),
                     session: AsyncSession = Depends(get_session)):
    g = await session.get(Goal, goal_id)
    if not g or g.user_id != user.id:
        raise HTTPException(404, "not found")
    g.current_amount = float(g.current_amount) + round(body.amount, 2)
    if g.current_amount >= float(g.target_amount) and g.achieved_at is None:
        g.achieved_at = utcnow()
    await session.commit()
    return {"current": float(g.current_amount), "achieved": g.achieved_at is not None}


@router.delete("/goals/{goal_id}")
async def del_goal(goal_id: int, user: User = Depends(get_current_user),
                   session: AsyncSession = Depends(get_session)):
    g = await session.get(Goal, goal_id)
    if not g or g.user_id != user.id:
        raise HTTPException(404, "not found")
    await session.delete(g)
    await session.commit()
    return {"ok": True}


# ------------------------------------------------------------------ insights
@router.get("/insights")
async def get_insights(user: User = Depends(get_current_user),
                       session: AsyncSession = Depends(get_session)):
    data = await insights.month_insights(session, user.id)
    data["currency"] = user.base_currency
    return data


# -------------------------------------------------------------- achievements
@router.get("/achievements")
async def get_achievements(user: User = Depends(get_current_user),
                           session: AsyncSession = Depends(get_session)):
    items = await ach.compute(session, user)
    await session.commit()
    return {"items": items}


# -------------------------------------------------------------------- stash
@router.get("/stash")
async def get_stash(user: User = Depends(get_current_user)):
    return {"balance": float(user.stash_balance or 0), "enabled": user.stash_enabled,
            "round_to": user.stash_round_to, "currency": user.base_currency}


@router.post("/stash/withdraw")
async def stash_withdraw(user: User = Depends(get_current_user),
                         session: AsyncSession = Depends(get_session)):
    amt = float(user.stash_balance or 0)
    user.stash_balance = 0
    await session.commit()
    return {"withdrawn": amt}


# -------------------------------------------------------------------- rates
@router.get("/rates")
async def get_rates(symbols: str = Query("BTC,ETH,USDT,TRX"), vs: str | None = None,
                    user: User = Depends(get_current_user)):
    vs = (vs or user.base_currency).upper()
    out = []
    for sym in [s.strip().upper() for s in symbols.split(",") if s.strip()]:
        series = await rates.market_series(sym, vs, days=14)
        price = series[-1][1] if series else await rates.convert(1, sym, vs)
        first = series[0][1] if series else None
        change = round((price - first) / first * 100, 2) if (price and first) else None
        out.append({"symbol": sym, "price": price, "vs": vs, "change_pct": change,
                    "spark": [p[1] for p in series[-30:]]})
    return {"items": out}


@router.get("/rates/series")
async def rates_series(symbol: str, vs: str | None = None, days: int = 30,
                       user: User = Depends(get_current_user)):
    vs = (vs or user.base_currency).upper()
    return {"symbol": symbol.upper(), "vs": vs, "series": await rates.market_series(symbol.upper(), vs, days)}


@router.get("/rates/convert")
async def rates_convert(amount: float, from_: str = Query(alias="from"), to: str = Query(...),
                        user: User = Depends(get_current_user)):
    val = await rates.convert(amount, from_.upper(), to.upper())
    return {"amount": amount, "from": from_.upper(), "to": to.upper(), "result": val}


# ------------------------------------------------------------------- family
@router.get("/family")
async def get_family(user: User = Depends(get_current_user),
                     session: AsyncSession = Depends(get_session)):
    membership = (await session.execute(select(FamilyMember, FamilyGroup)
                  .join(FamilyGroup, FamilyGroup.id == FamilyMember.group_id)
                  .where(FamilyMember.user_id == user.id))).first()
    if not membership:
        return {"group": None}
    member, group = membership
    members = (await session.execute(
        select(User.first_name, FamilyMember.role)
        .join(FamilyMember, FamilyMember.user_id == User.id)
        .where(FamilyMember.group_id == group.id))).all()
    return {"group": {"id": group.id, "name": group.name, "invite_code": group.invite_code,
                      "role": member.role,
                      "invite_link": f"https://t.me/{settings.bot_username}?start=fam_{group.invite_code}",
                      "members": [{"name": n or "—", "role": r} for n, r in members]}}


class FamilyCreate(BaseModel):
    name: str


@router.post("/family")
async def create_family(body: FamilyCreate, user: User = Depends(get_current_user),
                        session: AsyncSession = Depends(get_session)):
    name = (body.name or "").strip()
    if not name:
        raise HTTPException(400, "name required")  # TZ §12.11: never auto-name
    code = secrets.token_urlsafe(6)[:8]
    group = FamilyGroup(owner_id=user.id, name=name[:120], invite_code=code)
    session.add(group)
    await session.flush()
    session.add(FamilyMember(group_id=group.id, user_id=user.id, role="owner"))
    await session.commit()
    return {"id": group.id, "invite_code": code}


class FamilyJoin(BaseModel):
    code: str


@router.post("/family/join")
async def join_family(body: FamilyJoin, user: User = Depends(get_current_user),
                      session: AsyncSession = Depends(get_session)):
    group = (await session.execute(select(FamilyGroup).where(
        FamilyGroup.invite_code == body.code.strip()))).scalar_one_or_none()
    if not group:
        raise HTTPException(404, "invalid code")
    exists = (await session.execute(select(FamilyMember).where(
        FamilyMember.group_id == group.id, FamilyMember.user_id == user.id))).scalar_one_or_none()
    if not exists:
        session.add(FamilyMember(group_id=group.id, user_id=user.id, role="member"))
        await session.commit()
    return {"ok": True, "group": group.name}


# ------------------------------------------------------------------ premium
@router.post("/premium/invoice")
async def premium_invoice(user: User = Depends(get_current_user)):
    """Create a Telegram Stars invoice link (currency XTR) via Bot API."""
    if not settings.bot_token:
        raise HTTPException(503, "bot not configured")
    import httpx

    title = "NEBANK Premium"
    desc = ("Расширенные возможности на месяц" if user.language == "ru"
            else "Premium features for one month")
    payload = {
        "title": title, "description": desc, "payload": payments.PREMIUM_PAYLOAD,
        "currency": "XTR",
        "prices": [{"label": title, "amount": settings.premium_price_stars}],
    }
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(f"https://api.telegram.org/bot{settings.bot_token}/createInvoiceLink", json=payload)
        data = r.json()
    if not data.get("ok"):
        raise HTTPException(502, "invoice failed")
    return {"invoice_link": data["result"], "stars": settings.premium_price_stars}


# ------------------------------------------------------------------- export
@router.get("/export.xlsx")
async def export_excel(user: User = Depends(get_current_user),
                       session: AsyncSession = Depends(get_session)):
    if not _is_premium(user):
        raise HTTPException(402, "premium required")
    data = await export.export_xlsx(session, user.id, user.base_currency, user.language)
    return Response(content=data,
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": "attachment; filename=nebank-export.xlsx"})
