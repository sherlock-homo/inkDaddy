from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Album, AlbumItem, Photo
from ..services.photos import (
    PhotoProcessingError,
    album_detail,
    album_to_dict,
    create_album as create_album_record,
    create_photo_from_bytes,
    delete_photo_record,
    photo_to_dict,
    set_album_items,
)

router = APIRouter(prefix="/api", tags=["photos"])


@router.get("/photos")
def list_photos(db: Session = Depends(get_db)) -> dict[str, object]:
    photos = db.scalars(select(Photo).order_by(Photo.created_at.desc(), Photo.id.desc())).all()
    return {"photos": [photo_to_dict(photo) for photo in photos]}


@router.post("/photos")
async def upload_photo(
    file: UploadFile = File(...),
    mode: str = Form("fit"),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        photo = create_photo_from_bytes(
            db,
            filename=file.filename or "upload.jpg",
            content=await file.read(),
            mode=mode,
        )
    except PhotoProcessingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return photo_to_dict(photo)


@router.post("/photos/batch")
async def batch_upload(
    files: list[UploadFile] = File(default=[]),
    mode: str = Form("fit"),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    if len(files) > 50:
        raise HTTPException(status_code=422, detail="Batch uploads are limited to 50 images.")
    created: list[dict[str, object]] = []
    errors: list[dict[str, object]] = []
    for upload in files:
        try:
            photo = create_photo_from_bytes(
                db,
                filename=upload.filename or "upload.jpg",
                content=await upload.read(),
                mode=mode,
            )
            created.append(photo_to_dict(photo))
        except PhotoProcessingError as exc:
            errors.append({"filename": upload.filename, "detail": str(exc)})
    return {"photos": created, "accepted": len(created), "errors": errors}


@router.post("/photos/placeholders")
def create_photo_placeholder(payload: dict[str, object], db: Session = Depends(get_db)) -> dict[str, object]:
    """Compatibility endpoint for API tests and simulator-only metadata creation."""
    name = str(payload.get("original_filename") or "pending-upload.jpg")
    photo = Photo(
        original_filename=name,
        stored_filename=name,
        original_path="",
        processed_status="pending",
        palette="waveshare_7color_6",
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return photo_to_dict(photo)


@router.get("/photos/{photo_id}")
def get_photo(photo_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    photo = db.get(Photo, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found.")
    return photo_to_dict(photo)


@router.put("/photos/{photo_id}")
def update_photo(photo_id: int, payload: dict[str, object], db: Session = Depends(get_db)) -> dict[str, object]:
    photo = db.get(Photo, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found.")
    if "original_filename" in payload or "name" in payload:
        photo.original_filename = str(payload.get("original_filename") or payload.get("name") or photo.original_filename)
    db.commit()
    db.refresh(photo)
    return photo_to_dict(photo)


@router.delete("/photos/{photo_id}")
def delete_photo(photo_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    photo = db.get(Photo, photo_id)
    if photo:
        delete_photo_record(db, photo)
    return {"deleted": True}


@router.get("/photos/{photo_id}/preview")
def photo_preview(photo_id: int, db: Session = Depends(get_db)) -> Response:
    photo = db.get(Photo, photo_id)
    if not photo or not photo.preview_path:
        raise HTTPException(status_code=404, detail="Photo preview not found.")
    path = Path(photo.preview_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Photo preview file not found.")
    return Response(content=path.read_bytes(), media_type="image/png")


@router.get("/photos/{photo_id}/frame")
def photo_frame(photo_id: int, db: Session = Depends(get_db)) -> Response:
    photo = db.get(Photo, photo_id)
    if not photo or not photo.frame_path:
        raise HTTPException(status_code=404, detail="Photo frame not found.")
    path = Path(photo.frame_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Photo frame file not found.")
    return Response(content=path.read_bytes(), media_type="application/octet-stream")


@router.get("/albums")
def list_albums(db: Session = Depends(get_db)) -> dict[str, object]:
    albums = db.scalars(select(Album).order_by(Album.created_at.desc(), Album.id.desc())).all()
    return {"albums": [album_to_dict(db, album) for album in albums]}


@router.post("/albums")
def create_album(payload: dict[str, object], db: Session = Depends(get_db)) -> dict[str, object]:
    album = create_album_record(db, name=str(payload.get("name") or "New album"), mode=str(payload.get("mode") or "ordered"))
    if isinstance(payload.get("photo_ids"), list):
        set_album_items(db, album, [int(value) for value in payload["photo_ids"]])
    return album_detail(db, album)


@router.get("/albums/{album_id}")
def get_album(album_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    album = db.get(Album, album_id)
    if not album:
        raise HTTPException(status_code=404, detail="Album not found.")
    return album_detail(db, album)


@router.put("/albums/{album_id}")
def update_album(album_id: int, payload: dict[str, object], db: Session = Depends(get_db)) -> dict[str, object]:
    album = db.get(Album, album_id)
    if not album:
        raise HTTPException(status_code=404, detail="Album not found.")
    if "name" in payload:
        album.name = str(payload["name"]).strip() or album.name
    if "mode" in payload:
        mode = str(payload["mode"])
        album.mode = mode if mode in {"ordered", "shuffle", "random"} else album.mode
    if isinstance(payload.get("photo_ids"), list):
        set_album_items(db, album, [int(value) for value in payload["photo_ids"]])
    db.commit()
    db.refresh(album)
    return album_detail(db, album)


@router.delete("/albums/{album_id}")
def delete_album(album_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    album = db.get(Album, album_id)
    if album:
        db.execute(delete(AlbumItem).where(AlbumItem.album_id == album.id))
        db.delete(album)
        db.commit()
    return {"deleted": True}
