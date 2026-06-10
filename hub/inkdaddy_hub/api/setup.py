from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/setup", tags=["setup"])


@router.get("/status")
def setup_status() -> dict[str, object]:
    return {
        "completed": False,
        "admin_configured": False,
        "home_assistant_configured": False,
        "display_count": 0,
        "next_step": "create_admin",
    }
