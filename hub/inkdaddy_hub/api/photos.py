from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api", tags=["photos"])

_photos: dict[str, dict[str, object]] = {}
_albums: dict[str, dict[str, object]] = {}


@router.get("/photos")
def list_photos() -> dict[str, object]:
    return {"photos": list(_photos.values())}


@router.post("/photos")
def create_photo_placeholder(payload: dict[str, object]) -> dict[str, object]:
    photo_id = str(payload.get("id") or f"photo-{len(_photos) + 1}")
    record = {
        "id": photo_id,
        "original_filename": payload.get("original_filename", "pending-upload.jpg"),
        "processed_status": "pending",
        "palette": "waveshare_7color_6",
    }
    _photos[photo_id] = record
    return record


@router.post("/photos/batch")
def batch_upload_placeholder(payload: dict[str, object]) -> dict[str, object]:
    filenames = payload.get("filenames", [])
    if not isinstance(filenames, list):
        raise HTTPException(status_code=422, detail="filenames must be a list")
    created = [create_photo_placeholder({"original_filename": name}) for name in filenames[:50]]
    return {"photos": created, "accepted": len(created)}


@router.get("/photos/{photo_id}")
def get_photo(photo_id: str) -> dict[str, object]:
    try:
        return _photos[photo_id]
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Photo not found.") from exc


@router.put("/photos/{photo_id}")
def update_photo(photo_id: str, payload: dict[str, object]) -> dict[str, object]:
    record = get_photo(photo_id)
    record.update({key: value for key, value in payload.items() if key in {"name", "sort_order", "mode"}})
    return record


@router.delete("/photos/{photo_id}")
def delete_photo(photo_id: str) -> dict[str, object]:
    _photos.pop(photo_id, None)
    return {"deleted": True}


@router.post("/albums")
def create_album(payload: dict[str, object]) -> dict[str, object]:
    album_id = str(payload.get("id") or f"album-{len(_albums) + 1}")
    record = {"id": album_id, "name": payload.get("name", "New album"), "mode": payload.get("mode", "ordered")}
    _albums[album_id] = record
    return record
