"""Deterministic multilingual expense parser (TZ §5–§7).

Splits one message into one or more entries, each with amount, currency,
kind (expense/income), title (kept verbatim), and the purchase date.
Works with zero API keys.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

from app.core.currencies import ALL_CURRENCIES, CRYPTO, CRYPTO_SET
from app.services.parser.dates import extract_date
from app.services.parser.numbers import find_amount

# symbol -> code
SYMBOL_CUR = {"$": "USD", "€": "EUR", "£": "GBP", "₽": "RUB", "₴": "UAH",
              "₸": "KZT", "₾": "GEL", "₺": "TRY", "¥": "JPY", "₹": "INR", "₩": "KRW"}

# words / tickers -> code (lowercased keys)
WORD_CUR = {
    "руб": "RUB", "рублей": "RUB", "рубль": "RUB", "рубля": "RUB", "р": "RUB", "rub": "RUB",
    "доллар": "USD", "долларов": "USD", "доллара": "USD", "бакс": "USD", "usd": "USD", "dollars": "USD", "dollar": "USD",
    "евро": "EUR", "eur": "EUR", "euro": "EUR",
    "фунт": "GBP", "фунтов": "GBP", "gbp": "GBP", "pound": "GBP", "pounds": "GBP",
    "тенге": "KZT", "kzt": "KZT", "гривен": "UAH", "гривны": "UAH", "uah": "UAH",
    "lari": "GEL", "лари": "GEL", "yen": "JPY", "иен": "JPY",
    "btc": "BTC", "биткоин": "BTC", "биткоинов": "BTC", "биткоина": "BTC", "bitcoin": "BTC",
    "eth": "ETH", "эфир": "ETH", "эфира": "ETH", "ethereum": "ETH",
    "usdt": "USDT", "tether": "USDT", "юсдт": "USDT", "тезер": "USDT",
    "trx": "TRX", "tron": "TRX", "трон": "TRX",
}

INCOME_WORDS = {
    "зарплата", "зарплату", "аванс", "доход", "получил", "получила", "премия", "премию",
    "кэшбэк", "кешбэк", "возврат", "пополнение", "salary", "income", "paycheck", "bonus",
    "refund", "cashback", "deposit", "received", "payout", "wage",
}

# Split on separators, but never on a comma that sits between digits (decimal/thousands).
SPLIT_RE = re.compile(r"\s*[;\n]\s*|\s*,(?!\d)\s*|\s+и\s+|\s+and\s+")


@dataclass
class ParsedEntry:
    amount: float
    currency: str
    kind: str = "expense"  # expense | income
    title: str | None = None
    occurred_at: date = field(default_factory=date.today)
    crypto_network: str | None = None
    needs_usdt_amount: bool = False
    raw: str = ""


def _blank(s: str, span: tuple[int, int] | None) -> str:
    """Replace a span with equal-length spaces to keep all indices aligned."""
    if not span:
        return s
    a, b = span
    return s[:a] + (" " * (b - a)) + s[b:]


def _detect_currency(masked: str, default: str) -> tuple[str, str]:
    """Detect currency, blanking its token (length-preserving). Returns (code, masked)."""
    for sym, code in SYMBOL_CUR.items():
        i = masked.find(sym)
        if i != -1:
            return code, _blank(masked, (i, i + len(sym)))
    low = masked.lower()
    for m in re.finditer(r"[a-zа-яё]+", low):
        w = m.group(0)
        if w in WORD_CUR:
            return WORD_CUR[w], _blank(masked, (m.start(), m.end()))
    return default, masked


def _clean_title(masked_no_amount: str) -> str | None:
    s = re.sub(r"[+]", " ", masked_no_amount)
    s = re.sub(r"\s+", " ", s).strip(" -–—:.,")
    words = [w for w in s.split() if w.lower() not in WORD_CUR]
    s = " ".join(words).strip()
    return s or None


def _parse_fragment(fragment: str, base_currency: str, today: date | None) -> ParsedEntry | None:
    fragment = fragment.strip()
    if not fragment:
        return None

    kind = "income" if any(w in INCOME_WORDS for w in re.findall(r"[a-zа-яё]+", fragment.lower())) else "expense"
    if fragment.lstrip().startswith("+"):
        kind = "income"

    occurred, date_span = extract_date(fragment, today)
    # mask the date first so its digits are never read as the amount
    masked = _blank(fragment, date_span)
    currency, masked = _detect_currency(masked, base_currency)

    amount, amount_span = find_amount(masked)
    if amount is None:
        return None

    title = _clean_title(_blank(masked, amount_span))

    network = None
    if currency in CRYPTO_SET:
        nets = CRYPTO[currency]["networks"]
        network = nets[0] if len(nets) == 1 else None

    return ParsedEntry(
        amount=amount, currency=currency, kind=kind, title=title,
        occurred_at=occurred, crypto_network=network, raw=fragment,
    )


def parse_message(text: str, base_currency: str = "USD", today: date | None = None) -> list[ParsedEntry]:
    """Parse a free-form message into entries. Multi-entry aware (TZ §5)."""
    text = (text or "").strip()
    if not text:
        return []

    fragments = [f for f in SPLIT_RE.split(text) if f.strip()]
    if not fragments:
        fragments = [text]

    entries: list[ParsedEntry] = []
    carry = ""
    for frag in fragments:
        candidate = (carry + ", " + frag).strip(", ") if carry else frag
        entry = _parse_fragment(candidate, base_currency, today)
        if entry is None:
            # no amount in this fragment — carry it forward (e.g. "вчера" alone)
            carry = candidate
            continue
        carry = ""
        entries.append(entry)

    # whole-message fallback (single entry) if split produced nothing
    if not entries:
        e = _parse_fragment(text, base_currency, today)
        if e:
            entries.append(e)
    return entries


def is_currency_token(word: str) -> bool:
    return word.upper() in ALL_CURRENCIES or word.lower() in WORD_CUR
