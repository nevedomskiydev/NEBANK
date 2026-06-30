"""Crypto transaction-link parsing (TZ §7).

Detects the coin/network from an explorer URL or raw txid. For Bitcoin we fetch
the real on-chain output value (blockchain.info, keyless). For ETH/TRX/USDT we
record the entry and ask the user for the amount (USDT always asks, per TZ).
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import httpx

from app.core.currencies import CRYPTO


@dataclass
class CryptoTx:
    coin: str            # BTC | ETH | USDT | TRX
    network: str         # bitcoin | erc20 | trc20
    txid: str
    amount: float | None  # None -> ask the user
    needs_amount: bool


_PATTERNS = [
    # (regex, coin, network)
    (re.compile(r"(?:blockchair\.com/bitcoin|blockchain\.com/(?:btc|bitcoin)|mempool\.space)/(?:tx|transaction)/([0-9a-fA-F]{64})"), "BTC", "bitcoin"),
    (re.compile(r"etherscan\.io/tx/(0x[0-9a-fA-F]{64})"), "ETH", "erc20"),
    (re.compile(r"tronscan\.org/#?/transaction/([0-9a-fA-F]{64})"), "TRX", "trc20"),
]
_RAW_BTC = re.compile(r"^[0-9a-fA-F]{64}$")
_RAW_EVM = re.compile(r"^0x[0-9a-fA-F]{64}$")


async def _btc_value(txid: str) -> float | None:
    try:
        async with httpx.AsyncClient(timeout=12.0) as c:
            r = await c.get(f"https://blockchain.info/rawtx/{txid}")
            r.raise_for_status()
            data = r.json()
        out = sum(o.get("value", 0) for o in data.get("out", []))
        return out / 1e8 if out else None
    except Exception:
        return None


async def parse_crypto_link(text: str) -> CryptoTx | None:
    text = text.strip()
    coin = network = txid = None
    for pat, c, net in _PATTERNS:
        m = pat.search(text)
        if m:
            coin, network, txid = c, net, m.group(1)
            break
    if not coin:
        if _RAW_BTC.match(text):
            coin, network, txid = "BTC", "bitcoin", text
        elif _RAW_EVM.match(text):
            coin, network, txid = "ETH", "erc20", text
        else:
            return None

    amount = None
    needs = True
    if coin == "BTC":
        amount = await _btc_value(txid)
        needs = amount is None
    # ETH/TRX/USDT: amount asked from the user (USDT must, per TZ)
    return CryptoTx(coin=coin, network=network, txid=txid, amount=amount, needs_amount=needs)


def coin_hint(coin: str) -> str:
    info = CRYPTO.get(coin, {})
    nets = ", ".join(info.get("networks", []))
    return f"{coin} ({nets})"
