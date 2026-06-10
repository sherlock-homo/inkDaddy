from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from .devices import _device_payload, create_or_update_device

router = APIRouter(prefix="/api/simulator", tags=["simulator"])


@router.post("/devices")
def create_simulated_device(payload: dict[str, object], db: Session = Depends(get_db)) -> dict[str, object]:
    record = create_or_update_device(
        db,
        {
            "device_uid": payload.get("device_uid", "sim-xiao-mg24-001"),
            "name": payload.get("name", "Simulated XIAO MG24"),
            "hardware_target": "xiao_mg24",
            "provisioned": payload.get("provisioned", False),
            "mesh_connected": payload.get("mesh_connected", False),
            "battery_percent": payload.get("battery_percent", 87),
            "selected_source_type": payload.get("selected_source_type", "dashboard"),
            "selected_source_id": payload.get("selected_source_id", "sample"),
        }
    )
    return {"device": _device_payload(record), "simulator": True}
