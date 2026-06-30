"""Real exchange-rate service. No invented values (TZ §22/§33).

Crypto: CoinGecko (spot + historical + market chart).
Fiat:   Frankfurter (ECB reference rates, current + historical).
Everything is cached on disk (rate_points table) and in-memory (short TTL).
"""
from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta

import httpx
from cachetools import TTLCache
from sqlalchemy import select
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.core.currencies import CRYPTO, FIAT_SET
from app.db import SessionLocal
from app.models import RatePoint

_mem = TTLCache(maxsize=4096, ttl=settings.rates_cache_ttl)
_lock = asyncio.Lock()


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=15.0, headers={"User-Agent": "NEBANK/1.0"})


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8), reraise=True)
async def _get_json(url: str, params: dict | None = None) -> dict:
    async with _client() as c:
        r = await c.get(url, params=params)
        r.raise_for_status()
        return r.json()


# ---------------------------------------------------------------- spot rates
async def _fiat_to_usd(code: str) -> float | None:
    """How many USD one unit of `code` is worth (current)."""
    if code == "USD":
        return 1.0
    try:
        data = await _get_json(f"{settings.fiat_rates_base}/latest", {"base": code, "symbols": "USD"})
        return float(data["rates"]["USD"])
    except Exception:
        return None


async def _crypto_to_usd(code: str) -> float | None:
    cg = CRYPTO[code]["coingecko"]
    try:
        data = await _get_json(
            f"{settings.coingecko_base}/simple/price",
            {"ids": cg, "vs_currencies": "usd"},
        )
        return float(data[cg]["usd"])
    except Exception:
        return None


async def usd_price(code: str) -> float | None:
    code = code.upper()
    key = f"usd:{code}"
    if key in _mem:
        return _mem[key]
    if code in CRYPTO:
        price = await _crypto_to_usd(code)
    elif code in FIAT_SET:
        price = await _fiat_to_usd(code)
    else:
        price = None
    if price is not None:
        _mem[key] = price
    return price


async def convert(amount: float, src: str, dst: str) -> float | None:
    """Convert `amount` of src currency into dst at the current rate."""
    src, dst = src.upper(), dst.upper()
    if src == dst:
        return amount
    su, du = await asyncio.gather(usd_price(src), usd_price(dst))
    if not su or not du:
        return None
    return amount * su / du


# ------------------------------------------------------------ historical (day)
async def _crypto_usd_on(code: str, day: date) -> float | None:
    cg = CRYPTO[code]["coingecko"]
    try:
        data = await _get_json(
            f"{settings.coingecko_base}/coins/{cg}/history",
            {"date": day.strftime("%d-%m-%Y"), "localization": "false"},
        )
        return float(data["market_data"]["current_price"]["usd"])
    except Exception:
        return None


async def _fiat_usd_on(code: str, day: date) -> float | None:
    if code == "USD":
        return 1.0
    try:
        data = await _get_json(f"{settings.fiat_rates_base}/{day.isoformat()}", {"base": code, "symbols": "USD"})
        return float(data["rates"]["USD"])
    except Exception:
        return None


async def usd_price_on(code: str, day: date) -> float | None:
    """USD value of one `code` unit on a given day, cached in DB."""
    code = code.upper()
    today = datetime.utcnow().date()
    if day >= today:
        return await usd_price(code)

    async with SessionLocal() as s:
        row = (
            await s.execute(
                select(RatePoint).where(
                    RatePoint.symbol == code, RatePoint.quote == "USD", RatePoint.day == day
                )
            )
        ).scalar_one_or_none()
        if row:
            return float(row.price)

    if code in CRYPTO:
        price = await _crypto_usd_on(code, day)
    elif code in FIAT_SET:
        price = await _fiat_usd_on(code, day)
    else:
        price = None

    if price is not None:
        async with SessionLocal() as s:
            s.add(RatePoint(symbol=code, quote="USD", day=day, price=price))
            try:
                await s.commit()
            except Exception:
                await s.rollback()
    return price


async def convert_on(amount: float, src: str, dst: str, day: date) -> tuple[float | None, float]:
    """Convert on a specific day. Returns (converted_amount, src->dst rate)."""
    src, dst = src.upper(), dst.upper()
    if src == dst:
        return amount, 1.0
    su, du = await asyncio.gather(usd_price_on(src, day), usd_price_on(dst, day))
    if not su or not du:
        return None, 1.0
    rate = su / du
    return amount * rate, rate


# --------------------------------------------------------------- market chart
async def market_series(code: str, vs: str = "USD", days: int = 30) -> list[list[float]]:
    """Real historical series [[ms_timestamp, price], ...] for charts.

    Crypto via CoinGecko market_chart; fiat via Frankfurter time series.
    """
    code, vs = code.upper(), vs.upper()
    if code in CRYPTO:
        cg = CRYPTO[code]["coingecko"]
        try:
            data = await _get_json(
                f"{settings.coingecko_base}/coins/{cg}/market_chart",
                {"vs_currency": vs.lower(), "days": days},
            )
            return [[int(p[0]), float(p[1])] for p in data.get("prices", [])]
        except Exception:
            return []
    # fiat time series
    try:
        start = (datetime.utcnow().date() - timedelta(days=days)).isoformat()
        end = datetime.utcnow().date().isoformat()
        data = await _get_json(
            f"{settings.fiat_rates_base}/{start}..{end}", {"base": code, "symbols": vs}
        )
        out = []
        for d, rates in sorted(data.get("rates", {}).items()):
            ts = int(datetime.fromisoformat(d).timestamp() * 1000)
            out.append([ts, float(rates[vs])])
        return out
    except Exception:
        return []
