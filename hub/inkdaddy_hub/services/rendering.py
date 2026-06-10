from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

from .palette import WAVESHARE_7COLOR_6, Palette, raw_frame_from_image


@dataclass(frozen=True)
class FrameManifest:
    frame_id: str
    width: int
    height: int
    palette: str
    bits_per_pixel: int
    packing: str
    byte_order: str
    size_bytes: int
    sha256: str
    content_type: str
    source_id: str
    created_at: str
    download_url: str

    def as_dict(self) -> dict[str, object]:
        return self.__dict__.copy()


def render_dashboard_preview(width: int = 800, height: int = 480) -> Image.Image:
    image = Image.new("RGB", (width, height), (248, 246, 255))
    draw = ImageDraw.Draw(image)
    margin = 18
    gap = 10
    tile_w = (width - margin * 2 - gap * 3) // 4
    tile_h = (height - margin * 2 - gap) // 2
    colors = [(84, 37, 163), (39, 38, 62), (25, 122, 84), (172, 77, 38), (33, 84, 160)]
    labels = ["72F", "Weather", "Door", "Energy", "Trash Night"]
    font = _font(28)
    small = _font(16)
    for row in range(2):
        for col in range(4):
            x = margin + col * (tile_w + gap)
            y = margin + row * (tile_h + gap)
            fill = (255, 255, 255)
            outline = (71, 47, 118)
            draw.rounded_rectangle((x, y, x + tile_w, y + tile_h), radius=8, fill=fill, outline=outline, width=3)
            color = colors[(row * 4 + col) % len(colors)]
            label = labels[(row * 4 + col) % len(labels)]
            draw.rectangle((x + 12, y + 12, x + 42, y + 42), fill=color)
            draw.text((x + 14, y + 60), label, fill=(25, 20, 35), font=font if col == 0 else small)
    return image


def render_matter_join_screen(
    *,
    qr_payload: str,
    setup_pin: str,
    manual_code: str,
    discriminator: str,
    width: int = 800,
    height: int = 480,
) -> Image.Image:
    image = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    title = _font(44)
    body = _font(24)
    small = _font(18)
    draw.text((32, 28), "Connect inkDaddy", fill=(0, 0, 0), font=title)
    draw.text((36, 94), "Scan to add this display to Matter over Thread.", fill=(0, 0, 0), font=body)
    draw.text((36, 130), "Requires a Thread Border Router on your local network.", fill=(0, 0, 0), font=small)

    qr = _qr_image(qr_payload, size=270)
    image.paste(qr, (36, 176))

    panel_x = 350
    draw.rounded_rectangle((panel_x, 176, width - 36, height - 36), radius=10, outline=(0, 0, 0), width=3)
    draw.text((panel_x + 24, 204), "Manual pairing", fill=(0, 0, 0), font=body)
    draw.text((panel_x + 24, 256), f"PIN: {setup_pin}", fill=(0, 0, 0), font=body)
    draw.text((panel_x + 24, 304), f"Code: {manual_code}", fill=(0, 0, 0), font=body)
    draw.text((panel_x + 24, 352), f"Discriminator: {discriminator}", fill=(0, 0, 0), font=small)
    draw.text((panel_x + 24, 400), "Open inkDaddy > Connect inkDaddy after pairing.", fill=(0, 0, 0), font=small)
    return image


def build_frame_manifest(
    raw: bytes,
    *,
    width: int,
    height: int,
    palette: Palette = WAVESHARE_7COLOR_6,
    source_id: str,
    download_url: str,
    content_type: str = "application/octet-stream",
) -> FrameManifest:
    digest = hashlib.sha256(raw).hexdigest()
    created_at = datetime.now(timezone.utc).isoformat()
    return FrameManifest(
        frame_id=digest[:24],
        width=width,
        height=height,
        palette=palette.name,
        bits_per_pixel=palette.bits_per_pixel,
        packing=palette.packing,
        byte_order="row_major",
        size_bytes=len(raw),
        sha256=digest,
        content_type=content_type,
        source_id=source_id,
        created_at=created_at,
        download_url=download_url,
    )


def render_preview_png_bytes(image: Image.Image) -> bytes:
    out = BytesIO()
    image.save(out, format="PNG")
    return out.getvalue()


def render_preview_raw(image: Image.Image) -> tuple[bytes, FrameManifest]:
    raw, _ = raw_frame_from_image(image, WAVESHARE_7COLOR_6)
    manifest = build_frame_manifest(
        raw,
        width=image.width,
        height=image.height,
        source_id="preview",
        download_url="/api/devices/preview/frame",
    )
    return raw, manifest


def _qr_image(payload: str, size: int) -> Image.Image:
    try:
        import qrcode

        qr = qrcode.QRCode(border=2, box_size=8)
        qr.add_data(payload)
        qr.make(fit=True)
        return qr.make_image(fill_color="black", back_color="white").convert("RGB").resize((size, size))
    except ModuleNotFoundError:
        return _pseudo_qr(payload, size)


def _pseudo_qr(payload: str, size: int) -> Image.Image:
    digest = hashlib.sha256(payload.encode("utf-8")).digest()
    cells = 29
    cell = size // cells
    qr = Image.new("RGB", (cell * cells, cell * cells), (255, 255, 255))
    draw = ImageDraw.Draw(qr)
    for y in range(cells):
        for x in range(cells):
            if _finder_cell(x, y, cells) or digest[(x * 7 + y * 13) % len(digest)] & (1 << ((x + y) % 8)):
                draw.rectangle((x * cell, y * cell, (x + 1) * cell - 1, (y + 1) * cell - 1), fill=(0, 0, 0))
    return qr.resize((size, size))


def _finder_cell(x: int, y: int, cells: int) -> bool:
    in_left = x < 7 and (y < 7 or y >= cells - 7)
    in_right = x >= cells - 7 and y < 7
    if not (in_left or in_right):
        return False
    local_x = x if x < 7 else cells - 1 - x
    local_y = y if y < 7 else cells - 1 - y
    return local_x in (0, 1, 5, 6) or local_y in (0, 1, 5, 6) or (2 <= local_x <= 4 and 2 <= local_y <= 4)


def _font(size: int) -> ImageFont.ImageFont:
    for path in (
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ):
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            continue
    return ImageFont.load_default()
