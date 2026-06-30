"""High-quality photo understanding via an optional vision LLM (TZ §10).

When LLM_API_KEY is set, receipts / screenshots / bank-app captures are read by a
vision model and returned as structured entries — far better than plain OCR.
Falls back to Tesseract + QR (services/ocr.py) when no key is configured.
Costs a fraction of a cent per image; nothing is sent anywhere without a key.
"""
from __future__ import annotations

import base64
import json
from datetime import date

import httpx

from app.config import settings
from app.core.currencies import ALL_CURRENCIES, CRYPTO_SET
from app.services.parser.expense_parser import ParsedEntry

_PROMPT_EN = (
    "You read financial images: store receipts, payment screenshots, bank-app "
    "transaction lists, QR receipts. Extract real spending/income.\n"
    "Rules:\n"
    "- If the image is ONE store receipt, return ONE item: the grand total and the merchant name.\n"
    "- If the image shows SEVERAL distinct transactions (e.g. a bank app list), return one item per transaction.\n"
    "- amount: positive number. kind: \"expense\" or \"income\".\n"
    "- currency: ISO code (USD, EUR, RUB...) or crypto (BTC, ETH, USDT, TRX); null if unknown.\n"
    "- title: merchant / item / place, kept as written. date: YYYY-MM-DD if visible else null.\n"
    "Return STRICT JSON only: {\"items\":[{\"amount\":..,\"currency\":..,\"kind\":..,\"title\":..,\"date\":..}]}.\n"
    "If you cannot find any amount, return {\"items\":[]}."
)


async def extract_from_image(image_bytes: bytes, base_currency: str, lang: str,
                             mime: str = "image/jpeg") -> list[ParsedEntry]:
    if not settings.llm_api_key:
        return []
    b64 = base64.b64encode(image_bytes).decode()
    payload = {
        "model": settings.llm_model,
        "messages": [
            {"role": "system", "content": _PROMPT_EN},
            {"role": "user", "content": [
                {"type": "text", "text": f"Base currency is {base_currency}. Extract entries."},
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
            ]},
        ],
        "temperature": 0,
        "max_tokens": 800,
        "response_format": {"type": "json_object"},
    }
    try:
        async with httpx.AsyncClient(timeout=60.0) as c:
            r = await c.post(
                f"{settings.llm_api_base}/chat/completions",
                headers={"Authorization": f"Bearer {settings.llm_api_key}"},
                json=payload,
            )
            r.raise_for_status()
            content = r.json()["choices"][0]["message"]["content"]
        data = json.loads(content)
    except Exception:
        return []

    out: list[ParsedEntry] = []
    for it in (data.get("items") or [])[:15]:
        try:
            amount = float(it["amount"])
        except (KeyError, TypeError, ValueError):
            continue
        if amount <= 0:
            continue
        cur = (it.get("currency") or base_currency or "USD").upper()
        if cur not in ALL_CURRENCIES:
            cur = base_currency
        day = date.today()
        if it.get("date"):
            try:
                day = date.fromisoformat(str(it["date"])[:10])
            except ValueError:
                pass
        network = None
        if cur in CRYPTO_SET:
            from app.core.currencies import CRYPTO
            nets = CRYPTO[cur]["networks"]
            network = nets[0] if len(nets) == 1 else None
        out.append(ParsedEntry(
            amount=amount, currency=cur,
            kind="income" if it.get("kind") == "income" else "expense",
            title=(it.get("title") or None), occurred_at=day,
            crypto_network=network, raw="photo",
        ))
    return out
