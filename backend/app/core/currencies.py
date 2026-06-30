"""Currency + crypto reference data."""
from __future__ import annotations

# Crypto is strictly four coins per TZ §7.
CRYPTO = {
    "BTC": {"name": "Bitcoin", "decimals": 8, "networks": ["bitcoin"], "coingecko": "bitcoin"},
    "ETH": {"name": "Ethereum", "decimals": 8, "networks": ["erc20"], "coingecko": "ethereum"},
    "USDT": {"name": "Tether", "decimals": 6, "networks": ["erc20", "trc20"], "coingecko": "tether"},
    "TRX": {"name": "Tron", "decimals": 6, "networks": ["trc20"], "coingecko": "tron"},
}
CRYPTO_SET = set(CRYPTO)

NETWORKS = ["bitcoin", "erc20", "trc20"]

# A broad set of world fiats (symbol -> display). Base currency defaults to USD.
FIAT = {
    "USD": "$", "EUR": "€", "GBP": "£", "RUB": "₽", "JPY": "¥", "CNY": "¥",
    "CHF": "CHF", "CAD": "$", "AUD": "$", "NZD": "$", "SGD": "$", "HKD": "$",
    "SEK": "kr", "NOK": "kr", "DKK": "kr", "PLN": "zł", "CZK": "Kč", "HUF": "Ft",
    "TRY": "₺", "UAH": "₴", "KZT": "₸", "GEL": "₾", "AMD": "֏", "AZN": "₼",
    "INR": "₹", "IDR": "Rp", "MYR": "RM", "THB": "฿", "PHP": "₱", "VND": "₫",
    "KRW": "₩", "AED": "د.إ", "SAR": "﷼", "QAR": "﷼", "ILS": "₪", "EGP": "£",
    "ZAR": "R", "NGN": "₦", "BRL": "R$", "MXN": "$", "ARS": "$", "CLP": "$",
    "COP": "$", "PEN": "S/", "RON": "lei", "BGN": "лв", "RSD": "дин", "ISK": "kr",
}
FIAT_SET = set(FIAT)

ALL_CURRENCIES = FIAT_SET | CRYPTO_SET


def symbol(code: str) -> str:
    return FIAT.get(code, code)


def decimals_for(code: str) -> int:
    if code in CRYPTO:
        return CRYPTO[code]["decimals"]
    if code in ("JPY", "KRW", "VND", "IDR", "CLP", "HUF", "ISK"):
        return 0
    return 2


def fmt_amount(amount: float, code: str) -> str:
    d = decimals_for(code)
    if code in CRYPTO:
        s = f"{amount:.{d}f}".rstrip("0").rstrip(".")
        return f"{s} {code}"
    n = f"{amount:,.{d}f}".replace(",", " ")  # narrow no-break space as thousands sep
    sym = FIAT.get(code, "")
    return f"{sym}{n}" if sym and len(sym) == 1 else f"{n} {code}"
