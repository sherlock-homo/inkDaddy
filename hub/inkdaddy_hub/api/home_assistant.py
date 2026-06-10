from __future__ import annotations

from fastapi import APIRouter

from ..services.home_assistant import normalize_state_response, profile_token_url, validate_home_assistant_token
from ..services.security import redact_secret_value

router = APIRouter(prefix="/api/home-assistant", tags=["home-assistant"])

_ha_config: dict[str, object] = {
    "base_url": "http://homeassistant.local:8123",
    "configured": False,
    "token_preview": None,
}
_mock_entities = [
    {
        "entity_id": "sensor.living_room_temperature",
        "state": "72",
        "attributes": {"friendly_name": "Living Room Temperature", "unit_of_measurement": "F"},
    },
    {"entity_id": "binary_sensor.front_door", "state": "off", "attributes": {"friendly_name": "Front Door"}},
]


@router.get("/config")
def get_config() -> dict[str, object]:
    return {**_ha_config, "token_page_url": profile_token_url(str(_ha_config["base_url"]))}


@router.put("/config")
def save_config(payload: dict[str, object]) -> dict[str, object]:
    if payload.get("base_url"):
        _ha_config["base_url"] = str(payload["base_url"]).rstrip("/")
    if payload.get("token"):
        _ha_config["configured"] = True
        _ha_config["token_preview"] = redact_secret_value(str(payload["token"]))
    return get_config()


@router.post("/test")
def test_config(payload: dict[str, object]) -> dict[str, object]:
    base_url = str(payload.get("base_url") or _ha_config["base_url"])
    token = str(payload.get("token") or "")
    if not token:
        return {"ok": False, "detail": "Paste a Home Assistant long-lived access token."}
    result = validate_home_assistant_token(base_url, token)
    return result


@router.get("/entities")
def entities() -> dict[str, object]:
    normalized = normalize_state_response(_mock_entities)
    return {"entities": [entity.__dict__ for entity in normalized], "cached": True}
