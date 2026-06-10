from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from .security import redact_secrets


@dataclass(frozen=True)
class HAEntity:
    entity_id: str
    domain: str
    name: str | None
    state: str | None
    attributes: dict[str, Any]


def profile_token_url(base_url: str) -> str:
    return base_url.rstrip("/") + "/profile"


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def normalize_state_response(payload: list[dict[str, Any]]) -> list[HAEntity]:
    entities: list[HAEntity] = []
    for item in payload:
        entity_id = str(item.get("entity_id", ""))
        if "." not in entity_id:
            continue
        attributes = item.get("attributes") if isinstance(item.get("attributes"), dict) else {}
        name = attributes.get("friendly_name") or entity_id
        entities.append(
            HAEntity(
                entity_id=entity_id,
                domain=entity_id.split(".", 1)[0],
                name=str(name) if name else None,
                state=str(item.get("state")) if item.get("state") is not None else None,
                attributes=attributes,
            )
        )
    return entities


def validate_home_assistant_token(base_url: str, token: str, timeout: float = 8.0) -> dict[str, Any]:
    request = urllib.request.Request(base_url.rstrip("/") + "/api/", headers=auth_headers(token), method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            return {"ok": 200 <= response.status < 300, "status": response.status, "body": body[:200]}
    except urllib.error.HTTPError as exc:
        return {"ok": False, "status": exc.code, "body": exc.read().decode("utf-8")[:200]}
    except urllib.error.URLError as exc:
        return {"ok": False, "status": None, "body": str(exc.reason)}


def fetch_states(base_url: str, token: str, timeout: float = 12.0) -> list[HAEntity]:
    request = urllib.request.Request(base_url.rstrip("/") + "/api/states", headers=auth_headers(token), method="GET")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Home Assistant /api/states response must be a list.")
    return normalize_state_response(payload)


def safe_ha_log_payload(payload: Any) -> Any:
    return redact_secrets(payload)
