from __future__ import annotations

import json
import os
from pathlib import Path

from ..config import HubSettings, get_settings
from .security import redact_secret_value


def _load(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return {}
    return {str(key): str(value) for key, value in payload.items()}


def _write(path: Path, payload: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.chmod(tmp, 0o600)
    tmp.replace(path)
    os.chmod(path, 0o600)


def set_secret(ref: str, value: str, settings: HubSettings | None = None) -> str:
    settings = settings or get_settings()
    payload = _load(settings.secrets_path)
    payload[ref] = value
    _write(settings.secrets_path, payload)
    return ref


def get_secret(ref: str | None, settings: HubSettings | None = None) -> str | None:
    if not ref:
        return None
    settings = settings or get_settings()
    return _load(settings.secrets_path).get(ref)


def delete_secret(ref: str | None, settings: HubSettings | None = None) -> None:
    if not ref:
        return
    settings = settings or get_settings()
    payload = _load(settings.secrets_path)
    if ref in payload:
        payload.pop(ref)
        _write(settings.secrets_path, payload)


def secret_preview(ref: str | None, settings: HubSettings | None = None) -> str | None:
    value = get_secret(ref, settings)
    return redact_secret_value(value)
