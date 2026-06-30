"""Convert number-words (RU/EN) and digit groups to floats, incl. fractions.

Handles e.g.:
  "ноль точка ноль ноль ноль шесть" -> 0.0006
  "две тысячи пятьсот" -> 2500
  "twelve fifty" -> 1250 (contextual) / "twelve point five" -> 12.5
  "1 200,50" / "1,200.50" / "2k" / "1.5к" -> 1200.5 / 1200.5 / 2000 / 1500
"""
from __future__ import annotations

import re

RU_UNITS = {
    "ноль": 0, "один": 1, "одна": 1, "одну": 1, "два": 2, "две": 2, "три": 3,
    "четыре": 4, "пять": 5, "шесть": 6, "семь": 7, "восемь": 8, "девять": 9,
    "десять": 10, "одиннадцать": 11, "двенадцать": 12, "тринадцать": 13,
    "четырнадцать": 14, "пятнадцать": 15, "шестнадцать": 16, "семнадцать": 17,
    "восемнадцать": 18, "девятнадцать": 19, "двадцать": 20, "тридцать": 30,
    "сорок": 40, "пятьдесят": 50, "шестьдесят": 60, "семьдесят": 70,
    "восемьдесят": 80, "девяносто": 90, "сто": 100, "двести": 200, "триста": 300,
    "четыреста": 400, "пятьсот": 500, "шестьсот": 600, "семьсот": 700,
    "восемьсот": 800, "девятьсот": 900,
}
RU_SCALES = {"тысяча": 1000, "тысячи": 1000, "тысяч": 1000, "тыс": 1000,
             "миллион": 1_000_000, "миллиона": 1_000_000, "миллионов": 1_000_000, "млн": 1_000_000}

EN_UNITS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
    "eighteen": 18, "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40,
    "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
    "hundred": 100,
}
EN_SCALES = {"thousand": 1000, "million": 1_000_000, "k": 1000, "m": 1_000_000}

POINT_WORDS = {"точка", "запятая", "point", "dot", "целых", "и"}
ALL_WORDS = set(RU_UNITS) | set(RU_SCALES) | set(EN_UNITS) | set(EN_SCALES) | POINT_WORDS


def _words_to_int(tokens: list[str]) -> int | None:
    """Combine integer number-words like 'two thousand five hundred'."""
    total = 0
    current = 0
    seen = False
    for w in tokens:
        if w in RU_UNITS:
            current += RU_UNITS[w]; seen = True
        elif w in EN_UNITS:
            v = EN_UNITS[w]
            if v == 100:
                current = (current or 1) * 100
            else:
                current += v
            seen = True
        elif w in RU_SCALES or w in EN_SCALES:
            scale = RU_SCALES.get(w) or EN_SCALES[w]
            current = (current or 1) * scale
            total += current
            current = 0
            seen = True
        else:
            return None
    if not seen:
        return None
    return total + current


def words_to_number(text: str) -> float | None:
    """Parse a run of number-words possibly containing a decimal point word."""
    toks = re.findall(r"[a-zа-яё]+", text.lower())
    toks = [t for t in toks if t in ALL_WORDS]
    if not toks:
        return None

    # split on a point word
    point_idx = next((i for i, t in enumerate(toks) if t in POINT_WORDS), None)
    if point_idx is None:
        v = _words_to_int(toks)
        return float(v) if v is not None else None

    int_part_toks = toks[:point_idx]
    frac_toks = toks[point_idx + 1:]
    int_val = _words_to_int(int_part_toks) if int_part_toks else 0
    if int_val is None:
        int_val = 0
    # fractional words are read digit-by-digit: ноль ноль ноль шесть -> 0006
    digits = []
    for w in frac_toks:
        d = RU_UNITS.get(w, EN_UNITS.get(w))
        if d is None or d > 9:
            # allow "пятьдесят" style? keep simple: stop at first non-digit word
            break
        digits.append(str(d))
    if not digits:
        return float(int_val)
    return float(f"{int_val}.{''.join(digits)}")


_NUM_RE = re.compile(r"(?<![\w.])(\d{1,3}(?:[  ,.]\d{3})+|\d+)([.,]\d+)?\s*([kкmмкк]?)", re.IGNORECASE)


def normalize_digit_number(raw: str) -> float | None:
    """Parse a digit-form number with mixed separators and k/m suffix."""
    raw = raw.strip().lower().replace(" ", " ")
    m = re.match(r"^([\d ,.]+?)\s*([kкmм])?$", raw)
    if not m:
        return None
    body, suffix = m.group(1).strip(), m.group(2)
    body = body.replace(" ", "")
    # decide decimal separator: the last of ,/. with <=2-3 trailing digits is decimal
    if "," in body and "." in body:
        if body.rfind(",") > body.rfind("."):
            body = body.replace(".", "").replace(",", ".")
        else:
            body = body.replace(",", "")
    elif "," in body:
        # comma could be decimal or thousands
        parts = body.split(",")
        if len(parts[-1]) in (1, 2) and len(parts) == 2:
            body = body.replace(",", ".")
        else:
            body = body.replace(",", "")
    elif body.count(".") > 1:
        body = body.replace(".", "")
    try:
        val = float(body)
    except ValueError:
        return None
    if suffix in ("k", "к"):
        val *= 1000
    elif suffix in ("m", "м"):
        val *= 1_000_000
    return val


def find_amount(text: str) -> tuple[float | None, tuple[int, int] | None]:
    """Find the most plausible amount in a string.

    Returns (value, (start,end)) where the span covers the matched number text.
    Prefers digit numbers; falls back to number-words.
    """
    best: tuple[float, tuple[int, int]] | None = None
    pat = (r"\d{1,3}(?:[\u00a0 ]\d{3})+(?:[.,]\d+)?\s*[k\u043am\u043c]?"
           r"|\d{1,3}(?:,\d{3})+(?:\.\d+)?\s*[k\u043am\u043c]?"
           r"|\d+(?:[.,]\d+)?\s*[k\u043am\u043c]?")
    for m in re.finditer(pat, text):
        val = normalize_digit_number(m.group(0))
        if val is not None and val > 0:
            best = (val, (m.start(), m.end()))
            break
    if best:
        return best[0], best[1]

    # words fallback: scan windows of number-words
    toks = list(re.finditer(r"[a-zа-яё]+", text.lower()))
    run: list[re.Match] = []
    for tok in toks:
        if tok.group(0) in ALL_WORDS:
            run.append(tok)
        else:
            if run:
                seg = text[run[0].start():run[-1].end()]
                v = words_to_number(seg)
                if v is not None and v > 0:
                    return v, (run[0].start(), run[-1].end())
            run = []
    if run:
        seg = text[run[0].start():run[-1].end()]
        v = words_to_number(seg)
        if v is not None and v > 0:
            return v, (run[0].start(), run[-1].end())
    return None, None
