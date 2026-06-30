"""Bank-SMS / push parser with dedup (TZ §8)."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from app.services.parser.expense_parser import SYMBOL_CUR, WORD_CUR

DEBIT_WORDS = ("списание", "покупка", "оплата", "оплачено", "снятие", "перевод",
               "debited", "withdrawn", "purchase", "payment", "spent", "charged", "paid")
CREDIT_WORDS = ("зачисление", "пополнение", "поступление", "credited", "deposited", "received", "refund")

AMOUNT_RE = re.compile(r"(\d[\d  .,]*\d|\d)\s*(₽|руб|rub|usd|\$|eur|€|gbp|£|kzt|тенге|uah|грн)?", re.IGNORECASE)
MERCHANT_RE = re.compile(r"(?:в|at|on|to)\s+([A-Za-zА-Яа-я0-9][\w .&'-]{1,40})", re.IGNORECASE)


@dataclass
class ParsedSms:
    amount: float
    currency: str
    kind: str
    merchant: str | None
    dedup_hash: str


def _to_float(raw: str) -> float | None:
    body = raw.replace(" ", "").replace(" ", "")
    if "," in body and "." in body:
        body = body.replace(",", "") if body.rfind(".") > body.rfind(",") else body.replace(".", "").replace(",", ".")
    elif "," in body:
        parts = body.split(",")
        body = body.replace(",", ".") if len(parts[-1]) <= 2 else body.replace(",", "")
    try:
        return float(body)
    except ValueError:
        return None


def parse_bank_sms(text: str, base_currency: str = "USD") -> ParsedSms | None:
    low = text.lower()
    if not any(w in low for w in DEBIT_WORDS + CREDIT_WORDS):
        return None
    kind = "income" if any(w in low for w in CREDIT_WORDS) else "expense"

    amount = None
    currency = base_currency
    for m in AMOUNT_RE.finditer(text):
        val = _to_float(m.group(1))
        if val and val > 0:
            amount = val
            cur_tok = (m.group(2) or "").lower()
            if cur_tok in SYMBOL_CUR:
                currency = SYMBOL_CUR[cur_tok]
            elif cur_tok in WORD_CUR:
                currency = WORD_CUR[cur_tok]
            break
    if amount is None:
        return None

    merchant = None
    mm = MERCHANT_RE.search(text)
    if mm:
        merchant = mm.group(1).strip(" .,")

    # dedup on normalized content (digits + letters), independent of spacing
    norm = re.sub(r"\s+", " ", low).strip()
    dedup = hashlib.sha256(norm.encode()).hexdigest()[:32]
    return ParsedSms(amount=amount, currency=currency, kind=kind, merchant=merchant, dedup_hash=dedup)
