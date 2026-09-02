import os
import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta

# Heroku web and worker dynos do NOT share a local filesystem.  Therefore a
# local SQLite DB cannot be used for API-key verification across both dynos.
# This implementation creates signed, time-limited keys that can be verified
# by either dyno without shared storage.
KEY_SECRET = os.environ.get("API_KEY_SECRET") or os.environ.get("BOT_TOKEN", "change-me")
PERIOD_DAYS = 30
EPOCH = datetime(2026, 1, 1)


def _period(now: datetime) -> tuple[datetime, datetime]:
    elapsed = max((now - EPOCH).total_seconds(), 0)
    period = int(elapsed // (PERIOD_DAYS * 86400))
    start = EPOCH + timedelta(days=period * PERIOD_DAYS)
    expiry = start + timedelta(days=PERIOD_DAYS)
    return start, expiry


def _make_key(user_id: int, period_start: datetime) -> str:
    payload = f"{user_id}:{period_start.strftime('%Y%m%d')}".encode()
    digest = hmac.new(KEY_SECRET.encode(), payload, hashlib.sha256).digest()[:12]
    token = base64.urlsafe_b64encode(digest).decode().rstrip("=")
    return f"RonakBots_{user_id}_{token}"


def _parse_key(api_key: str):
    if not api_key or not api_key.startswith("RonakBots_"):
        return None
    parts = api_key.split("_")
    if len(parts) != 3:
        return None
    try:
        user_id = int(parts[1])
    except ValueError:
        return None
    return user_id, parts[2]


async def init_db():
    # Kept for compatibility with api.py and bot.py. No local DB is required.
    return None


async def get_or_create_key(user_id: int):
    now = datetime.now()
    start, expiry = _period(now)
    key = _make_key(user_id, start)
    return key, expiry, True


async def verify_key(api_key: str):
    parsed = _parse_key(api_key)
    if not parsed:
        return False, "Invalid API Key"

    user_id, token = parsed
    now = datetime.now()
    start, expiry = _period(now)
    expected = _make_key(user_id, start)
    expected_token = expected.rsplit("_", 1)[1]

    if not hmac.compare_digest(token, expected_token):
        return False, "Invalid API Key"

    if now >= expiry:
        return False, "API Key Expired! Please get a new key from the bot."

    return True, "Valid"
