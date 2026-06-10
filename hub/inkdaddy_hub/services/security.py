from __future__ import annotations

from typing import Any

SECRET_KEY_PARTS = ("token", "secret", "password", "pin", "manual_code", "setup_code")


def redact_secret_value(value: str | None) -> str | None:
    if value is None:
        return None
    if len(value) <= 8:
        return "<redacted>"
    return value[:2] + "<redacted>" + value[-2:]


def redact_secrets(payload: Any) -> Any:
    if isinstance(payload, dict):
        redacted: dict[Any, Any] = {}
        for key, value in payload.items():
            key_text = str(key).lower()
            if any(part in key_text for part in SECRET_KEY_PARTS):
                redacted[key] = redact_secret_value(str(value)) if value is not None else None
            else:
                redacted[key] = redact_secrets(value)
        return redacted
    if isinstance(payload, list):
        return [redact_secrets(item) for item in payload]
    return payload
