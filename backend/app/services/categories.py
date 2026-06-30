"""Category resolution (TZ §6).

Never pre-creates empty defaults. A category is created only when a real entry
needs it. We first try to map the item/place to a sensible category by keywords
(premium, Tinkoff-like), otherwise we create a category from the entry's own name.
"""
from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Category, TxKind

# canonical name (en, ru) -> keyword stems (ru+en)
KEYWORDS: list[tuple[tuple[str, str], str, list[str]]] = [
    (("Groceries", "Продукты"), "#34C759", ["продукт", "магазин", "пятёроч", "пятероч", "ашан", "перекрест",
        "grocery", "groceries", "market", "supermarket", "food", "еда", "молоко", "хлеб"]),
    (("Cafe & Restaurants", "Кафе и рестораны"), "#FF9500", ["кофе", "кафе", "ресторан", "обед", "ужин", "завтрак",
        "бар", "coffee", "cafe", "restaurant", "lunch", "dinner", "breakfast", "starbucks", "пицц", "pizza", "бургер"]),
    (("Transport", "Транспорт"), "#5AC8FA", ["такси", "метро", "автобус", "бензин", "заправка", "uber", "yandex go",
        "taxi", "metro", "bus", "fuel", "gas", "parking", "парковк", "проезд"]),
    (("Entertainment", "Развлечения"), "#AF52DE", ["кино", "игра", "игр", "концерт", "театр", "netflix", "spotify",
        "cinema", "movie", "game", "games", "concert", "развлеч"]),
    (("Shopping", "Покупки"), "#FF2D55", ["одежд", "обувь", "магаз", "shopping", "clothes", "amazon", "ozon", "wildberries",
        "озон", "вайлдберр", "покупк"]),
    (("Health", "Здоровье"), "#FF3B30", ["аптек", "врач", "доктор", "лекарств", "стоматолог", "pharmacy", "doctor",
        "health", "clinic", "медиц", "зубн"]),
    (("Bills & Utilities", "Счета и услуги"), "#8E8E93", ["жкх", "свет", "вода", "электр", "интернет", "связь",
        "мобиль", "bill", "utilities", "internet", "electricity", "rent", "аренд", "квартплат"]),
    (("Subscriptions", "Подписки"), "#007AFF", ["подписк", "subscription", "premium", "youtube", "icloud", "patreon"]),
    (("Travel", "Путешествия"), "#30B0C7", ["отель", "билет", "авиа", "поезд", "hotel", "flight", "ticket", "airbnb",
        "путешеств", "trip", "travel"]),
    (("Crypto", "Крипта"), "#C9A227", ["btc", "eth", "usdt", "trx", "crypto", "крипт", "bitcoin", "биткоин"]),
    (("Income", "Доход"), "#34C759", ["зарплат", "доход", "премия", "salary", "income", "bonus", "аванс"]),
]


def _match_keyword(title: str | None, raw: str | None) -> tuple[tuple[str, str], str] | None:
    hay = f"{title or ''} {raw or ''}".lower()
    if not hay.strip():
        return None
    for (names, color, kws) in KEYWORDS:
        for kw in kws:
            if kw in hay:
                return names, color
    return None


def _title_to_name(title: str | None) -> str:
    if not title:
        return "Other"
    # use the first 1-2 meaningful words, capitalized
    words = re.findall(r"[\wа-яёА-ЯЁ]+", title)
    words = [w for w in words if not w.isdigit()][:2]
    name = " ".join(words).strip() or "Other"
    return name[:1].upper() + name[1:]


async def resolve_category(
    session: AsyncSession, user_id: int, lang: str, kind: TxKind,
    title: str | None, raw: str | None, is_crypto: bool = False,
) -> Category:
    """Return an existing or newly-created category for this entry."""
    names = None
    color = "#C9A227"
    if is_crypto:
        names, color = ("Crypto", "Крипта"), "#C9A227"
    else:
        match = _match_keyword(title, raw)
        if match:
            names, color = match
    name = names[0 if lang != "ru" else 1] if names else _title_to_name(title)

    existing = (
        await session.execute(
            select(Category).where(
                Category.user_id == user_id, Category.kind == kind, Category.name == name
            )
        )
    ).scalar_one_or_none()
    if existing:
        return existing

    cat = Category(user_id=user_id, name=name, kind=kind, color=color)
    session.add(cat)
    await session.flush()
    return cat


async def list_categories(session: AsyncSession, user_id: int, kind: TxKind | None = None) -> list[Category]:
    q = select(Category).where(Category.user_id == user_id, Category.is_archived == False)  # noqa: E712
    if kind:
        q = q.where(Category.kind == kind)
    return list((await session.execute(q.order_by(Category.name))).scalars())
