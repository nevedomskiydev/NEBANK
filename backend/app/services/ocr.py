"""OCR for receipts / screenshots / QR (TZ §10). Tesseract + ZBar, keyless.

Returns recognised text, decoded QR payloads, and a best-effort receipt total.
The caller feeds the text into the same expense parser for multi-entry support.
"""
from __future__ import annotations

import io
import re
from dataclasses import dataclass, field

from app.services.parser.numbers import normalize_digit_number

TOTAL_WORDS = ("итог", "итого", "total", "сумма", "к оплате", "amount due", "всего")


@dataclass
class OcrResult:
    text: str
    qr: list[str] = field(default_factory=list)
    total: float | None = None
    lines: list[str] = field(default_factory=list)


def _decode_qr(img) -> list[str]:
    try:
        from pyzbar.pyzbar import decode  # type: ignore

        return [d.data.decode("utf-8", "ignore") for d in decode(img)]
    except Exception:
        return []


def _ocr_text(img) -> str:
    try:
        import pytesseract  # type: ignore

        return pytesseract.image_to_string(img, lang="rus+eng")
    except Exception:
        try:
            import pytesseract  # type: ignore

            return pytesseract.image_to_string(img)
        except Exception:
            return ""


def _find_total(text: str) -> float | None:
    best = None
    for line in text.splitlines():
        low = line.lower()
        if any(w in low for w in TOTAL_WORDS):
            nums = re.findall(r"\d[\d  .,]*\d|\d", line)
            for n in nums:
                v = normalize_digit_number(n)
                if v and v > 0:
                    best = v
    if best is None:
        # fallback: the largest number on the receipt
        vals = []
        for n in re.findall(r"\d[\d  .,]*\d|\d", text):
            v = normalize_digit_number(n)
            if v and 0 < v < 10_000_000:
                vals.append(v)
        best = max(vals) if vals else None
    return best


def recognize(image_bytes: bytes) -> OcrResult:
    try:
        from PIL import Image  # type: ignore

        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception:
        return OcrResult(text="")

    qr = _decode_qr(img)
    text = _ocr_text(img)
    total = _find_total(text)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return OcrResult(text=text, qr=qr, total=total, lines=lines)


def qr_to_amount(payload: str) -> float | None:
    """Russian FNS receipt QR carries s=<sum>. Generic: find a sum field."""
    m = re.search(r"[?&]s=([\d.]+)", payload)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            return None
    return None
