import hashlib
import hmac
import time
from typing import Optional

from .config import settings


def generate_state(user_id: int) -> str:
    """
    Генерирует подписанный state вида: "<user_id>:<timestamp>:<signature_hex>".
    Signature = HMAC-SHA256(user_id:timestamp, STATE_SECRET).
    """
    ts = int(time.time())
    payload = f"{user_id}:{ts}"
    signature = hmac.new(
        settings.state_secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"{payload}:{signature}"


def parse_state(state: str) -> Optional[int]:
    """
    Проверяет подпись state и возвращает user_id, если всё ок.
    В случае ошибки/подделки возвращает None.
    """
    try:
        user_id_str, ts_str, signature = state.split(":", 2)
        payload = f"{user_id_str}:{ts_str}"
        expected_signature = hmac.new(
            settings.state_secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(signature, expected_signature):
            return None
        return int(user_id_str)
    except Exception:  # noqa: BLE001
        return None


