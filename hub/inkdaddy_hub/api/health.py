from __future__ import annotations

from fastapi import APIRouter

from ..config import get_settings

router = APIRouter()


@router.get("/api/health")
def health() -> dict[str, object]:
    settings = get_settings()
    return {
        "ok": True,
        "app": settings.app_name,
        "version": settings.version,
        "service": "inkdaddy-hub",
    }
