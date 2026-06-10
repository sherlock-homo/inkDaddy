from __future__ import annotations

from fastapi import APIRouter

from ..config import get_settings
from ..services.updates import (
    firmware_manifest_response,
    get_firmware_update_info,
    get_hub_update_info,
    hub_update_response,
    start_hub_update,
    update_policy,
)

router = APIRouter(prefix="/api/updates", tags=["updates"])


@router.get("/hub/check")
@router.post("/hub/check")
def hub_update_check() -> dict[str, object]:
    return hub_update_response(get_hub_update_info())


@router.post("/hub/apply")
def hub_update_apply(payload: dict[str, object]) -> dict[str, object]:
    info = get_hub_update_info()
    version = str(payload.get("version") or info.latest_version or "latest")
    return start_hub_update(version=version, update_info=info)


@router.get("/hub/auto")
def hub_auto_update_status() -> dict[str, object]:
    settings = get_settings()
    policy = update_policy(settings)
    return {
        "repository": policy.repository,
        "auto_apply": policy.auto_apply,
        "apply_allowed": policy.apply_allowed,
        "check_interval_seconds": policy.check_interval_seconds,
        "command": policy.command,
        "configured": bool(policy.repository),
    }


@router.put("/hub/auto")
def hub_auto_update_update(_payload: dict[str, object]) -> dict[str, object]:
    return {
        **hub_auto_update_status(),
        "detail": "Auto-update policy is controlled by service environment variables and installer settings.",
    }


@router.get("/firmware/check")
@router.post("/firmware/check")
def firmware_check(board: str = "xiao_mg24", current_version: str | None = None) -> dict[str, object]:
    return firmware_manifest_response(get_firmware_update_info(board=board, current_version=current_version))


@router.post("/firmware/approve")
def firmware_approve(payload: dict[str, object]) -> dict[str, object]:
    return {
        "approved": True,
        "target": payload.get("target", "xiao_mg24"),
        "version": payload.get("version"),
        "delivery": "hub-mediated",
        "detail": "Firmware approval is recorded by the hub OTA orchestrator before a device pulls the manifest.",
    }


@router.get("/firmware/manifest")
def firmware_manifest(board: str = "xiao_mg24", current_version: str | None = None) -> dict[str, object]:
    return firmware_manifest_response(get_firmware_update_info(board=board, current_version=current_version))
