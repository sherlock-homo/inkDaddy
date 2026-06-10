from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Response
from PIL import Image
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..models import AlbumItem, Device, DeviceStatusHistory, Frame, Photo
from ..services.palette import WAVESHARE_7COLOR_6, raw_frame_from_image
from ..services.provisioning import DisplayContentKind, ProvisioningState, next_display_content_kind
from ..services.rendering import (
    build_frame_manifest,
    render_dashboard_preview,
    render_matter_join_screen,
)

router = APIRouter(prefix="/api/devices", tags=["devices"])


def _device_payload(device: Device) -> dict[str, object]:
    warning = device.refresh_interval_minutes < 15
    return {
        "id": str(device.id),
        "device_uid": device.device_uid,
        "name": device.name,
        "hardware_target": device.hardware_target,
        "firmware_version": device.firmware_version,
        "hardware_version": device.hardware_version,
        "provisioned": device.provisioned,
        "mesh_connected": device.mesh_connected,
        "refresh_interval_minutes": device.refresh_interval_minutes,
        "refresh_interval_warning": warning,
        "selected_source_type": device.selected_source_type,
        "selected_source_id": device.selected_source_id,
        "last_seen_at": device.last_seen_at.isoformat() if device.last_seen_at else None,
        "last_refresh_result": device.last_refresh_result,
        "last_frame_id": device.last_frame_id,
        "battery_percent": device.battery_percent,
        "battery_voltage": device.battery_voltage,
        "created_at": device.created_at.isoformat() if device.created_at else None,
        "updated_at": device.updated_at.isoformat() if device.updated_at else None,
    }


def _get_device(db: Session, device_id: str) -> Device:
    device = db.scalar(select(Device).where(Device.device_uid == device_id))
    if not device and device_id.isdigit():
        device = db.get(Device, int(device_id))
    if not device:
        raise HTTPException(status_code=404, detail="Device not found.")
    return device


def create_or_update_device(db: Session, payload: dict[str, object]) -> Device:
    device_uid = str(payload.get("device_uid") or payload.get("id") or f"display-{uuid_suffix(db)}")
    device = db.scalar(select(Device).where(Device.device_uid == device_uid))
    if not device:
        device = Device(
            device_uid=device_uid,
            name=str(payload.get("name") or "inkDaddy Display"),
            hardware_target=str(payload.get("hardware_target") or "xiao_mg24"),
            selected_source_type=str(payload.get("selected_source_type") or "dashboard"),
            selected_source_id=str(payload.get("selected_source_id") or "sample"),
        )
        db.add(device)
    _apply_device_payload(device, payload)
    db.commit()
    db.refresh(device)
    return device


def uuid_suffix(db: Session) -> int:
    return int(db.scalar(select(func.count()).select_from(Device)) or 0) + 1


def _apply_device_payload(device: Device, payload: dict[str, object]) -> None:
    string_fields = ("name", "hardware_target", "firmware_version", "hardware_version", "selected_source_type", "selected_source_id")
    bool_fields = ("provisioned", "mesh_connected")
    float_fields = ("battery_percent", "battery_voltage")
    for key in string_fields:
        if key in payload and payload[key] is not None:
            setattr(device, key, str(payload[key]))
    for key in bool_fields:
        if key in payload:
            setattr(device, key, bool(payload[key]))
    for key in float_fields:
        if key in payload and payload[key] is not None:
            setattr(device, key, float(payload[key]))
    if "refresh_interval_minutes" in payload and payload["refresh_interval_minutes"] is not None:
        minutes = int(payload["refresh_interval_minutes"])
        device.refresh_interval_minutes = max(10, min(3600, minutes))


@router.get("")
def list_devices(db: Session = Depends(get_db)) -> dict[str, object]:
    devices = db.scalars(select(Device).order_by(Device.created_at.desc(), Device.id.desc())).all()
    return {"devices": [_device_payload(device) for device in devices]}


@router.post("")
def create_device(payload: dict[str, object], db: Session = Depends(get_db)) -> dict[str, object]:
    return _device_payload(create_or_update_device(db, payload))


@router.get("/{device_id}")
def get_device(device_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
    return _device_payload(_get_device(db, device_id))


@router.put("/{device_id}")
def update_device(device_id: str, payload: dict[str, object], db: Session = Depends(get_db)) -> dict[str, object]:
    device = _get_device(db, device_id)
    _apply_device_payload(device, payload)
    db.commit()
    db.refresh(device)
    return _device_payload(device)


@router.delete("/{device_id}")
def delete_device(device_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
    device = _get_device(db, device_id)
    db.execute(delete(DeviceStatusHistory).where(DeviceStatusHistory.device_id == device.id))
    db.delete(device)
    db.commit()
    return {"deleted": True}


@router.post("/{device_id}/heartbeat")
def heartbeat(device_id: str, payload: dict[str, object], db: Session = Depends(get_db)) -> dict[str, object]:
    device = _get_device(db, device_id)
    _apply_device_payload(device, payload)
    if "last_frame_id" in payload:
        device.last_frame_id = str(payload["last_frame_id"])
    device.last_seen_at = datetime.utcnow()
    db.add(
        DeviceStatusHistory(
            device_id=device.id,
            battery_percent=device.battery_percent,
            battery_voltage=device.battery_voltage,
            status=str(payload.get("status") or "heartbeat"),
            detail_json="{}",
        )
    )
    db.commit()
    db.refresh(device)
    return {"ok": True, "device": _device_payload(device)}


@router.get("/{device_id}/history")
def status_history(device_id: str, limit: int = 50, db: Session = Depends(get_db)) -> dict[str, object]:
    device = _get_device(db, device_id)
    rows = db.scalars(
        select(DeviceStatusHistory)
        .where(DeviceStatusHistory.device_id == device.id)
        .order_by(DeviceStatusHistory.created_at.desc())
        .limit(max(1, min(250, limit)))
    ).all()
    return {
        "history": [
            {
                "status": row.status,
                "battery_percent": row.battery_percent,
                "battery_voltage": row.battery_voltage,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]
    }


@router.get("/{device_id}/frame-manifest")
def frame_manifest(device_id: str, refresh_count: int = 0, db: Session = Depends(get_db)) -> dict[str, object]:
    device = _get_device(db, device_id)
    image, content_kind, source_id = _render_device_image(db, device, refresh_count=refresh_count)
    raw, _checksum = raw_frame_from_image(image, WAVESHARE_7COLOR_6)
    manifest = build_frame_manifest(
        raw,
        width=image.width,
        height=image.height,
        source_id=source_id,
        download_url=f"/api/devices/{device.device_uid}/frame",
    )
    settings = get_settings()
    frame_path = settings.data_dir / "frames" / f"device-{device.id}-{manifest.frame_id}.raw"
    frame_path.parent.mkdir(parents=True, exist_ok=True)
    frame_path.write_bytes(raw)
    frame_record = db.scalar(select(Frame).where(Frame.frame_id == manifest.frame_id))
    if frame_record:
        frame_record.path = str(frame_path)
        frame_record.size_bytes = manifest.size_bytes
        frame_record.sha256 = manifest.sha256
    else:
        db.add(
            Frame(
            frame_id=manifest.frame_id,
            source_type="device",
            source_id=device.device_uid,
            width=manifest.width,
            height=manifest.height,
            palette=manifest.palette,
            bits_per_pixel=manifest.bits_per_pixel,
            packing=manifest.packing,
            byte_order=manifest.byte_order,
            size_bytes=manifest.size_bytes,
            sha256=manifest.sha256,
            content_type=manifest.content_type,
            path=str(frame_path),
            )
        )
    device.last_frame_id = manifest.frame_id
    db.commit()
    return {**manifest.as_dict(), "content_kind": content_kind.value}


@router.get("/{device_id}/frame")
def frame(device_id: str, db: Session = Depends(get_db)) -> Response:
    device = _get_device(db, device_id)
    if not device.last_frame_id:
        raise HTTPException(status_code=404, detail="No frame has been generated for this device.")
    frame_record = db.scalar(select(Frame).where(Frame.frame_id == device.last_frame_id))
    if not frame_record or not Path(frame_record.path).exists():
        raise HTTPException(status_code=404, detail="Frame file not found.")
    return Response(content=Path(frame_record.path).read_bytes(), media_type=frame_record.content_type)


@router.get("/{device_id}/config")
def device_config(device_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
    device = _get_device(db, device_id)
    return {
        "device_uid": device.device_uid,
        "refresh_interval_minutes": device.refresh_interval_minutes,
        "selected_source_type": device.selected_source_type,
        "selected_source_id": device.selected_source_id,
        "provisioning_timeout_seconds": 300,
        "startup_join_timeout_seconds": 30,
        "refresh_interval_warning": device.refresh_interval_minutes < 15,
    }


@router.put("/{device_id}/config")
def update_device_config(device_id: str, payload: dict[str, object], db: Session = Depends(get_db)) -> dict[str, object]:
    update_device(device_id, payload, db)
    return device_config(device_id, db)


@router.post("/{device_id}/refresh-result")
def refresh_result(device_id: str, payload: dict[str, object], db: Session = Depends(get_db)) -> dict[str, object]:
    device = _get_device(db, device_id)
    device.last_refresh_result = str(payload.get("result") or "unknown")
    if payload.get("frame_id"):
        device.last_frame_id = str(payload["frame_id"])
    db.add(
        DeviceStatusHistory(
            device_id=device.id,
            battery_percent=device.battery_percent,
            battery_voltage=device.battery_voltage,
            status=f"refresh:{device.last_refresh_result}",
            detail_json="{}",
        )
    )
    db.commit()
    db.refresh(device)
    return {"ok": True, "device": _device_payload(device)}


def _render_device_image(db: Session, device: Device, *, refresh_count: int) -> tuple[Image.Image, DisplayContentKind, str]:
    content_count = _cycleable_content_count(db, device)
    state = ProvisioningState(
        commissioned=device.provisioned,
        mesh_connected=device.mesh_connected,
        cycleable_content_count=content_count,
        refresh_count=refresh_count,
    )
    content_kind = next_display_content_kind(state)
    if content_kind == DisplayContentKind.MATTER_JOIN_SCREEN:
        return (
            render_matter_join_screen(
                qr_payload=f"MT:INKDADDY-{device.device_uid}",
                setup_pin="12345678",
                manual_code="34970112332",
                discriminator="3840",
            ),
            content_kind,
            "matter-join",
        )
    if device.selected_source_type == "photo":
        photo = _selected_photo(db, device)
        if photo and photo.processed_path and Path(photo.processed_path).exists():
            return Image.open(photo.processed_path).convert("RGB"), content_kind, f"photo-{photo.id}"
    if device.selected_source_type == "album":
        photo = _selected_album_photo(db, device)
        if photo and photo.processed_path and Path(photo.processed_path).exists():
            return Image.open(photo.processed_path).convert("RGB"), content_kind, f"photo-{photo.id}"
    return render_dashboard_preview(), content_kind, device.selected_source_id or "dashboard-sample"


def _cycleable_content_count(db: Session, device: Device) -> int:
    if device.selected_source_type == "photo":
        return 1 if _selected_photo(db, device) else 0
    if device.selected_source_type == "album" and device.selected_source_id and device.selected_source_id.isdigit():
        return int(
            db.scalar(select(func.count()).select_from(AlbumItem).where(AlbumItem.album_id == int(device.selected_source_id)))
            or 0
        )
    return 1 if device.selected_source_type == "dashboard" else 0


def _selected_photo(db: Session, device: Device) -> Photo | None:
    if not device.selected_source_id or not device.selected_source_id.isdigit():
        return None
    photo = db.get(Photo, int(device.selected_source_id))
    if photo and photo.processed_status == "ready":
        return photo
    return None


def _selected_album_photo(db: Session, device: Device) -> Photo | None:
    if not device.selected_source_id or not device.selected_source_id.isdigit():
        return None
    row = db.execute(
        select(Photo)
        .join(AlbumItem, AlbumItem.photo_id == Photo.id)
        .where(AlbumItem.album_id == int(device.selected_source_id), Photo.processed_status == "ready")
        .order_by(AlbumItem.sort_order)
        .limit(1)
    ).scalar_one_or_none()
    return row
