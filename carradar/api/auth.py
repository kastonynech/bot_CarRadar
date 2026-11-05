"""Telegram WebApp initData verification. Never trust a Telegram ID sent by the frontend."""
import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

from fastapi import Header, HTTPException

from carradar.shared.config import settings


def verify_init_data(init_data: str, token: str, max_age: int = 86400, now: float | None = None) -> dict:
    pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    got = pairs.pop("hash", None)
    if not got:
        raise ValueError("no hash")
    check = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    if not hmac.compare_digest(hmac.new(secret, check.encode(), hashlib.sha256).hexdigest(), got):
        raise ValueError("bad signature")
    if (now or time.time()) - int(pairs.get("auth_date", 0)) > max_age:
        raise ValueError("expired")
    return json.loads(pairs["user"])


async def current_user(x_init_data: str = Header(default="")) -> dict:
    try:
        return verify_init_data(x_init_data, settings.bot_token)
    except Exception:
        raise HTTPException(401, "invalid initData")
