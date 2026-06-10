from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from ..config import HubSettings, get_settings
from ..models import Album, AlbumItem, Photo
from .palette import WAVESHARE_7COLOR_6, raw_frame_from_image
from .rendering import render_preview_png_bytes

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
MAX_UPLOAD_BYTES = 32 * 1024 * 1024


class PhotoProcessingError(ValueError):
    pass


@dataclass(frozen=True)
class ProcessedPhotoFiles:
    processed_path: Path
    preview_path: Path
    frame_path: Path
    width: int
    height: int
    checksum: str
    palette: str


def sanitize_filename(filename: str) -> str:
    name = Path(filename or "upload.jpg").name
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", Path(name).stem).strip(".-") or "photo"
    suffix = Path(name).suffix.lower() or ".jpg"
    if suffix not in ALLOWED_EXTENSIONS:
        raise PhotoProcessingError(f"Unsupported image type {suffix!r}.")
    return f"{stem[:96]}{suffix}"


def photo_to_dict(photo: Photo) -> dict[str, object]:
    return {
        "id": str(photo.id),
        "original_filename": photo.original_filename,
        "stored_filename": photo.stored_filename,
        "processed_status": photo.processed_status,
        "width": photo.width,
        "height": photo.height,
        "palette": photo.palette,
        "checksum": photo.checksum,
        "preview_url": f"/api/photos/{photo.id}/preview" if photo.preview_path else None,
        "frame_url": f"/api/photos/{photo.id}/frame" if photo.frame_path else None,
        "uploaded_at": photo.created_at.isoformat() if photo.created_at else None,
        "updated_at": photo.updated_at.isoformat() if photo.updated_at else None,
    }


def album_to_dict(db: Session, album: Album) -> dict[str, object]:
    item_count = db.scalar(select(func.count()).select_from(AlbumItem).where(AlbumItem.album_id == album.id)) or 0
    return {
        "id": str(album.id),
        "name": album.name,
        "mode": album.mode,
        "item_count": item_count,
        "created_at": album.created_at.isoformat() if album.created_at else None,
        "updated_at": album.updated_at.isoformat() if album.updated_at else None,
    }


def create_photo_from_bytes(
    db: Session,
    *,
    filename: str,
    content: bytes,
    mode: str = "fit",
    settings: HubSettings | None = None,
) -> Photo:
    if not content:
        raise PhotoProcessingError("Uploaded image is empty.")
    if len(content) > MAX_UPLOAD_BYTES:
        raise PhotoProcessingError("Uploaded image exceeds the 32 MB limit.")

    settings = settings or get_settings()
    safe_name = sanitize_filename(filename)
    stem = uuid.uuid4().hex
    original_path = settings.data_dir / "originals" / f"{stem}-{safe_name}"
    original_path.parent.mkdir(parents=True, exist_ok=True)
    original_path.write_bytes(content)

    photo = Photo(
        original_filename=safe_name,
        stored_filename=original_path.name,
        original_path=str(original_path),
        processed_status="processing",
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)

    try:
        processed = process_photo_file(photo.id, original_path, mode=mode, settings=settings)
        photo.processed_path = str(processed.processed_path)
        photo.preview_path = str(processed.preview_path)
        photo.frame_path = str(processed.frame_path)
        photo.width = processed.width
        photo.height = processed.height
        photo.palette = processed.palette
        photo.checksum = processed.checksum
        photo.processed_status = "ready"
    except Exception:
        photo.processed_status = "failed"
        db.commit()
        raise

    db.commit()
    db.refresh(photo)
    return photo


def process_photo_file(
    photo_id: int,
    original_path: Path,
    *,
    mode: str = "fit",
    settings: HubSettings | None = None,
) -> ProcessedPhotoFiles:
    settings = settings or get_settings()
    width = settings.default_width
    height = settings.default_height
    mode = mode if mode in {"fit", "fill", "crop"} else "fit"

    try:
        with Image.open(original_path) as opened:
            image = ImageOps.exif_transpose(opened).convert("RGB")
    except UnidentifiedImageError as exc:
        raise PhotoProcessingError("Uploaded file is not a supported image.") from exc

    if mode == "fill":
        processed = ImageOps.fit(image, (width, height), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    elif mode == "crop":
        processed = ImageOps.fit(image, (width, height), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    else:
        processed = ImageOps.pad(
            image,
            (width, height),
            method=Image.Resampling.LANCZOS,
            color=(255, 255, 255),
            centering=(0.5, 0.5),
        )

    processed_path = settings.data_dir / "processed" / f"photo-{photo_id}.png"
    preview_path = settings.data_dir / "previews" / f"photo-{photo_id}.png"
    frame_path = settings.data_dir / "frames" / f"photo-{photo_id}.raw"
    for path in (processed_path, preview_path, frame_path):
        path.parent.mkdir(parents=True, exist_ok=True)

    processed.save(processed_path, format="PNG")
    preview_path.write_bytes(render_preview_png_bytes(processed))
    raw, checksum = raw_frame_from_image(processed, WAVESHARE_7COLOR_6)
    frame_path.write_bytes(raw)
    return ProcessedPhotoFiles(
        processed_path=processed_path,
        preview_path=preview_path,
        frame_path=frame_path,
        width=width,
        height=height,
        checksum=checksum,
        palette=WAVESHARE_7COLOR_6.name,
    )


def delete_photo_record(db: Session, photo: Photo) -> None:
    for value in (photo.original_path, photo.processed_path, photo.preview_path, photo.frame_path):
        if value:
            Path(value).unlink(missing_ok=True)
    db.execute(delete(AlbumItem).where(AlbumItem.photo_id == photo.id))
    db.delete(photo)
    db.commit()


def create_album(db: Session, *, name: str, mode: str = "ordered") -> Album:
    mode = mode if mode in {"ordered", "shuffle", "random"} else "ordered"
    album = Album(name=name.strip() or "New album", mode=mode)
    db.add(album)
    db.commit()
    db.refresh(album)
    return album


def set_album_items(db: Session, album: Album, photo_ids: list[int]) -> list[AlbumItem]:
    existing = {photo.id for photo in db.scalars(select(Photo).where(Photo.id.in_(photo_ids))).all()}
    db.execute(delete(AlbumItem).where(AlbumItem.album_id == album.id))
    items: list[AlbumItem] = []
    for index, photo_id in enumerate(photo_ids):
        if photo_id in existing:
            item = AlbumItem(album_id=album.id, photo_id=photo_id, sort_order=index)
            db.add(item)
            items.append(item)
    db.commit()
    return items


def album_detail(db: Session, album: Album) -> dict[str, object]:
    rows = db.execute(
        select(AlbumItem, Photo)
        .join(Photo, Photo.id == AlbumItem.photo_id)
        .where(AlbumItem.album_id == album.id)
        .order_by(AlbumItem.sort_order)
    ).all()
    payload = album_to_dict(db, album)
    payload["photos"] = [photo_to_dict(photo) | {"sort_order": item.sort_order} for item, photo in rows]
    return payload
