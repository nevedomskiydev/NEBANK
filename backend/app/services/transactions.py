"""Transaction creation pipeline: FX conversion, dedup, stash round-up."""
from __future__ import annotations

import hashlib
import math
from datetime import date

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Transaction, TxKind, TxSource, User
from app.services import rates
from app.services.categories import resolve_category
from app.services.parser.expense_parser import ParsedEntry


def _dedup_hash(user_id: int, amount: float, currency: str, day: date, title: str | None) -> str:
    base = f"{user_id}|{round(amount, 6)}|{currency}|{day.isoformat()}|{(title or '').lower().strip()}"
    return hashlib.sha256(base.encode()).hexdigest()[:32]


async def create_transaction(
    session: AsyncSession,
    user: User,
    entry: ParsedEntry,
    source: TxSource = TxSource.text,
    dedup_hash: str | None = None,
    add_stash: bool = True,
) -> Transaction | None:
    """Create a transaction from a parsed entry. Returns None if it's a duplicate."""
    kind = TxKind.income if entry.kind == "income" else TxKind.expense
    day = entry.occurred_at

    converted, rate = await rates.convert_on(entry.amount, entry.currency, user.base_currency, day)
    if converted is None:
        # rate unavailable: keep original magnitude, rate 1 (still recorded, never lost)
        converted, rate = entry.amount, 1.0

    is_crypto = entry.crypto_network is not None or entry.currency in ("BTC", "ETH", "USDT", "TRX")
    category = await resolve_category(
        session, user.id, user.language, kind, entry.title, entry.raw, is_crypto=is_crypto
    )

    dh = dedup_hash or _dedup_hash(user.id, entry.amount, entry.currency, day, entry.title)
    existing = (
        await session.execute(
            select(Transaction).where(Transaction.user_id == user.id, Transaction.dedup_hash == dh)
        )
    ).scalar_one_or_none()
    if existing:
        return None

    tx = Transaction(
        user_id=user.id,
        category_id=category.id,
        kind=kind,
        amount=round(float(converted), 2),
        original_amount=entry.amount,
        original_currency=entry.currency,
        fx_rate=rate,
        title=entry.title,
        source=source,
        raw_text=entry.raw,
        crypto_network=entry.crypto_network,
        occurred_at=day,
        dedup_hash=dh,
    )
    session.add(tx)
    try:
        await session.flush()
    except IntegrityError:
        await session.rollback()
        return None

    # Round-up stash (TZ §12.10): only for expenses, in base currency
    if add_stash and user.stash_enabled and kind == TxKind.expense and user.stash_round_to > 0:
        rounded = math.ceil(converted / user.stash_round_to) * user.stash_round_to
        diff = round(rounded - converted, 2)
        if diff > 0:
            user.stash_balance = float(user.stash_balance or 0) + diff

    return tx


async def recategorize(session: AsyncSession, tx: Transaction, category_id: int) -> None:
    tx.category_id = category_id
    await session.flush()
