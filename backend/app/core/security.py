"""Telegram Mini App (WebApp) initData validation.

Implements the official check:
https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
"""
from __future__ import annotations

import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

from app.config import settings


class AuthError(Exception):
    pass


def _secret_key(bot_token: str) -> bytes:
    return hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()


def validate_init_data(init_data: str, *, max_age: int | None = None) -> dict:
    """Validate a Telegram WebApp initData string. Returns the parsed user dict.

    Raises AuthError on any failure.
    """
    if not settings.bot_token:
        raise AuthError("bot token not configured")
    if not init_data:
        raise AuthError("empty initData")

    pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = pairs.pop("hash", None)
    if not received_hash:
        raise AuthError("missing hash")

    data_check_string = "\n".join(f"{k}={pairs[k]}" for k in sorted(pairs))
    calc = hmac.new(_secret_key(settings.bot_token), data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calc, received_hash):
        raise AuthError("bad signature")

    max_age = settings.initdata_max_age if max_age is None else max_age
    auth_date = int(pairs.get("auth_date", "0"))
    if max_age and auth_date and (time.time() - auth_date) > max_age:
        raise AuthError("initData expired")

    user_raw = pairs.get("user")
    if not user_raw:
        raise AuthError("missing user")
    try:
        user = json.loads(user_raw)
    except json.JSONDecodeError as exc:  # pragma: no cover
        raise AuthError("bad user json") from exc
    return user
