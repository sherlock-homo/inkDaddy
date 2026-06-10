from __future__ import annotations

from fastapi import APIRouter

from .devices import create_device

router = APIRouter(prefix="/api/simulator", tags=["simulator"])


@router.post("/devices")
def create_simulated_device(payload: dict[str, object]) -> dict[str, object]:
    record = create_device(
        {
            "device_uid": payload.get("device_uid", "sim-xiao-mg24-001"),
            "name": payload.get("name", "Simulated XIAO MG24"),
            "hardware_target": "xiao_mg24",
            "provisioned": payload.get("provisioned", False),
            "mesh_connected": payload.get("mesh_connected", False),
            "battery_percent": payload.get("battery_percent", 87),
        }
    )
    return {"device": record, "simulator": True}
