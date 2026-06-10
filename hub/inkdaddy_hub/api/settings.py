from __future__ import annotations

from fastapi import APIRouter

from ..config import get_settings

router = APIRouter(prefix="/api/settings", tags=["settings"])

_settings_cache: dict[str, object] = {
    "site_name": "inkDaddy",
    "local_url": "http://inkdaddy.local",
    "default_refresh_minutes": 30,
    "low_refresh_warning_minutes": 15,
}


@router.get("")
def get_hub_settings() -> dict[str, object]:
    settings = get_settings()
    return {
        **_settings_cache,
        "data_dir": str(settings.data_dir),
        "target": {
            "width": settings.default_width,
            "height": settings.default_height,
            "palette": settings.default_palette,
        },
    }


@router.put("")
def update_hub_settings(payload: dict[str, object]) -> dict[str, object]:
    allowed = {"site_name", "default_refresh_minutes", "local_url"}
    for key in allowed:
        if key in payload:
            _settings_cache[key] = payload[key]
    return get_hub_settings()
