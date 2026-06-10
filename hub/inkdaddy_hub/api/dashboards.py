from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response

from ..services.dashboard import DashboardValidationError, SAMPLE_DASHBOARD, load_dashboard_yaml, validate_dashboard_config
from ..services.rendering import render_dashboard_preview, render_preview_png_bytes

router = APIRouter(prefix="/api/dashboards", tags=["dashboards"])

_dashboards: dict[str, dict[str, object]] = {
    "sample": {
        "id": "sample",
        "name": "Home Overview",
        "yaml": SAMPLE_DASHBOARD,
        "active": True,
    }
}


@router.get("")
def list_dashboards() -> dict[str, object]:
    return {"dashboards": list(_dashboards.values())}


@router.post("")
def create_dashboard(payload: dict[str, object]) -> dict[str, object]:
    raw_yaml = str(payload.get("yaml") or SAMPLE_DASHBOARD)
    try:
        config = validate_dashboard_config(load_dashboard_yaml(raw_yaml))
    except (DashboardValidationError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    dashboard_id = str(payload.get("id") or config.get("name", "dashboard")).lower().replace(" ", "-")
    record = {"id": dashboard_id, "name": config.get("name", dashboard_id), "yaml": raw_yaml, "active": False}
    _dashboards[dashboard_id] = record
    return record


@router.get("/{dashboard_id}")
def get_dashboard(dashboard_id: str) -> dict[str, object]:
    try:
        return _dashboards[dashboard_id]
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Dashboard not found.") from exc


@router.put("/{dashboard_id}")
def update_dashboard(dashboard_id: str, payload: dict[str, object]) -> dict[str, object]:
    record = get_dashboard(dashboard_id)
    if "yaml" in payload:
        raw_yaml = str(payload["yaml"])
        try:
            validate_dashboard_config(load_dashboard_yaml(raw_yaml))
        except (DashboardValidationError, RuntimeError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        record["yaml"] = raw_yaml
    if "name" in payload:
        record["name"] = payload["name"]
    return record


@router.delete("/{dashboard_id}")
def delete_dashboard(dashboard_id: str) -> dict[str, object]:
    _dashboards.pop(dashboard_id, None)
    return {"deleted": True}


@router.post("/{dashboard_id}/preview")
def preview_dashboard(dashboard_id: str) -> Response:
    get_dashboard(dashboard_id)
    image = render_dashboard_preview()
    return Response(content=render_preview_png_bytes(image), media_type="image/png")


@router.get("/{dashboard_id}/export")
def export_dashboard(dashboard_id: str) -> Response:
    record = get_dashboard(dashboard_id)
    return Response(content=str(record["yaml"]), media_type="application/x-yaml")


@router.post("/import")
def import_dashboard(payload: dict[str, object]) -> dict[str, object]:
    return create_dashboard(payload)
