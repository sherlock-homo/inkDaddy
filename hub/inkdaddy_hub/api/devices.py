from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response

from ..services.provisioning import DisplayContentKind, ProvisioningState, next_display_content_kind
from ..services.rendering import (
    build_frame_manifest,
    render_dashboard_preview,
    render_matter_join_screen,
    render_preview_raw,
)

router = APIRouter(prefix="/api/devices", tags=["devices"])

_devices: dict[str, dict[str, object]] = {}
_last_frame: bytes = b""


@router.get("")
def list_devices() -> dict[str, object]:
    return {"devices": list(_devices.values())}


@router.post("")
def create_device(payload: dict[str, object]) -> dict[str, object]:
    device_id = str(payload.get("device_uid") or payload.get("id") or f"display-{len(_devices) + 1}")
    record = {
        "id": device_id,
        "device_uid": device_id,
        "name": payload.get("name", "inkDaddy Display"),
        "hardware_target": payload.get("hardware_target", "xiao_mg24"),
        "provisioned": bool(payload.get("provisioned", False)),
        "mesh_connected": bool(payload.get("mesh_connected", False)),
        "battery_percent": payload.get("battery_percent"),
        "refresh_interval_minutes": int(payload.get("refresh_interval_minutes", 30)),
        "selected_source_type": payload.get("selected_source_type", "dashboard"),
        "last_refresh_result": None,
    }
    _devices[device_id] = record
    return record


@router.get("/{device_id}")
def get_device(device_id: str) -> dict[str, object]:
    try:
        return _devices[device_id]
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Device not found.") from exc


@router.put("/{device_id}")
def update_device(device_id: str, payload: dict[str, object]) -> dict[str, object]:
    record = get_device(device_id)
    for key in (
        "name",
        "provisioned",
        "mesh_connected",
        "refresh_interval_minutes",
        "selected_source_type",
        "selected_source_id",
    ):
        if key in payload:
            record[key] = payload[key]
    return record


@router.delete("/{device_id}")
def delete_device(device_id: str) -> dict[str, object]:
    _devices.pop(device_id, None)
    return {"deleted": True}


@router.post("/{device_id}/heartbeat")
def heartbeat(device_id: str, payload: dict[str, object]) -> dict[str, object]:
    record = get_device(device_id)
    for key in ("battery_percent", "battery_voltage", "firmware_version", "mesh_connected", "last_frame_id"):
        if key in payload:
            record[key] = payload[key]
    record["last_seen_at"] = payload.get("timestamp", "now")
    return {"ok": True, "device": record}


@router.get("/{device_id}/frame-manifest")
def frame_manifest(device_id: str, refresh_count: int = 0) -> dict[str, object]:
    global _last_frame
    record = get_device(device_id)
    state = ProvisioningState(
        commissioned=bool(record.get("provisioned")),
        mesh_connected=bool(record.get("mesh_connected")),
        cycleable_content_count=1,
        refresh_count=refresh_count,
    )
    content_kind = next_display_content_kind(state)
    if content_kind == DisplayContentKind.MATTER_JOIN_SCREEN:
        image = render_matter_join_screen(
            qr_payload="MT:INKDADDY-PLACEHOLDER",
            setup_pin="12345678",
            manual_code="34970112332",
            discriminator="3840",
        )
        source_id = "matter-join"
    else:
        image = render_dashboard_preview()
        source_id = "dashboard-sample"
    raw, _manifest = render_preview_raw(image)
    _last_frame = raw
    manifest = build_frame_manifest(
        raw,
        width=image.width,
        height=image.height,
        source_id=source_id,
        download_url=f"/api/devices/{device_id}/frame",
    )
    return {**manifest.as_dict(), "content_kind": content_kind.value}


@router.get("/{device_id}/frame")
def frame(device_id: str) -> Response:
    get_device(device_id)
    return Response(content=_last_frame, media_type="application/octet-stream")


@router.get("/{device_id}/config")
def device_config(device_id: str) -> dict[str, object]:
    record = get_device(device_id)
    return {
        "device_uid": record["device_uid"],
        "refresh_interval_minutes": record["refresh_interval_minutes"],
        "selected_source_type": record.get("selected_source_type", "dashboard"),
        "provisioning_timeout_seconds": 300,
        "startup_join_timeout_seconds": 30,
    }


@router.put("/{device_id}/config")
def update_device_config(device_id: str, payload: dict[str, object]) -> dict[str, object]:
    update_device(device_id, payload)
    return device_config(device_id)


@router.post("/{device_id}/refresh-result")
def refresh_result(device_id: str, payload: dict[str, object]) -> dict[str, object]:
    record = get_device(device_id)
    record["last_refresh_result"] = payload.get("result", "unknown")
    record["last_frame_id"] = payload.get("frame_id", record.get("last_frame_id"))
    return {"ok": True, "device": record}
