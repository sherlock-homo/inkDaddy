from __future__ import annotations

from fastapi import APIRouter

from ..config import get_settings

router = APIRouter(prefix="/api/diagnostics", tags=["diagnostics"])


@router.get("")
def diagnostics() -> dict[str, object]:
    settings = get_settings()
    return {
        "app": settings.app_name,
        "version": settings.version,
        "data_dir": str(settings.data_dir),
        "thread_border_router": {
            "status": "unknown",
            "checks": ["ipv6_default_route", "mdns_resolution", "coap_reachability"],
        },
        "secrets_redacted": True,
    }
