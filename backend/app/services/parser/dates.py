"""Date extraction (RU/EN). Day-first; never swap day and month (TZ §5)."""
from __future__ import annotations

import re
from datetime import date, timedelta

RU_MONTHS = {
    "январ": 1, "феврал": 2, "март": 3, "апрел": 4, "мая": 5, "май": 5, "мае": 5,
    "июн": 6, "июл": 7, "август": 8, "сентябр": 9, "октябр": 10, "ноябр": 11, "декабр": 12,
}
EN_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6, "jul": 7,
    "aug": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
}


def _clamp(y: int, m: int, d: int, today: date) -> date | None:
    try:
        result = date(y, m, d)
    except ValueError:
        return None
    return result


def extract_date(text: str, today: date | None = None) -> tuple[date, tuple[int, int] | None]:
    """Return (occurred_date, span_to_strip). Defaults to today when nothing found."""
    today = today or date.today()
    low = text.lower()

    # relative words
    rel = [
        (r"\bпозавчера\b", 2), (r"\bвчера\b", 1), (r"\bсегодня\b", 0),
        (r"\bday before yesterday\b", 2), (r"\byesterday\b", 1), (r"\btoday\b", 0),
    ]
    for pat, days in rel:
        m = re.search(pat, low)
        if m:
            return today - timedelta(days=days), (m.start(), m.end())

    # "N дней назад" / "N days ago"
    m = re.search(r"\b(\d{1,3})\s*(?:дн(?:я|ей|ь)|days?)\s*(?:назад|ago)\b", low)
    if m:
        return today - timedelta(days=int(m.group(1))), (m.start(), m.end())
    m = re.search(r"\b(?:неделю|week)\s*(?:назад|ago)\b", low)
    if m:
        return today - timedelta(days=7), (m.start(), m.end())

    # "15 января" / "4 июля"
    m = re.search(r"\b(\d{1,2})\s+([а-яё]+)\b", low)
    if m:
        d = int(m.group(1))
        stem = m.group(2)
        for key, mon in RU_MONTHS.items():
            if stem.startswith(key):
                res = _clamp(today.year, mon, d, today)
                if res:
                    if res > today:
                        res = _clamp(today.year - 1, mon, d, today) or res
                    return res, (m.start(), m.end())

    # "jan 3" / "3 jan"
    m = re.search(r"\b([a-z]{3,4})\.?\s+(\d{1,2})\b", low)
    if m and m.group(1)[:3] in EN_MONTHS:
        mon = EN_MONTHS[m.group(1)[:4]] if m.group(1)[:4] in EN_MONTHS else EN_MONTHS[m.group(1)[:3]]
        res = _clamp(today.year, mon, int(m.group(2)), today)
        if res:
            if res > today:
                res = _clamp(today.year - 1, mon, int(m.group(2)), today) or res
            return res, (m.start(), m.end())
    m = re.search(r"\b(\d{1,2})\s+([a-z]{3,4})\b", low)
    if m and (m.group(2)[:3] in EN_MONTHS or m.group(2)[:4] in EN_MONTHS):
        mon = EN_MONTHS.get(m.group(2)[:4], EN_MONTHS.get(m.group(2)[:3]))
        res = _clamp(today.year, mon, int(m.group(1)), today)
        if res:
            if res > today:
                res = _clamp(today.year - 1, mon, int(m.group(1)), today) or res
            return res, (m.start(), m.end())

    # numeric d.m / d.m.y / d/m — day first, month second (TZ: do not swap)
    m = re.search(r"\b(\d{1,2})[./](\d{1,2})(?:[./](\d{2,4}))?\b", low)
    if m:
        d, mo = int(m.group(1)), int(m.group(2))
        y = today.year
        if m.group(3):
            y = int(m.group(3))
            y += 2000 if y < 100 else 0
        if 1 <= d <= 31 and 1 <= mo <= 12:
            res = _clamp(y, mo, d, today)
            if res:
                if res > today and not m.group(3):
                    res = _clamp(y - 1, mo, d, today) or res
                return res, (m.start(), m.end())

    return today, None
