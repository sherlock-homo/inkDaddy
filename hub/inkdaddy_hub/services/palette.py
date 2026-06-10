from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Iterable

from PIL import Image


@dataclass(frozen=True)
class Palette:
    name: str
    colors: tuple[tuple[int, int, int], ...]
    bits_per_pixel: int = 4
    packing: str = "high_nibble_first"


WAVESHARE_7COLOR_6 = Palette(
    name="waveshare_7color_6",
    colors=(
        (0, 0, 0),
        (255, 255, 255),
        (0, 180, 0),
        (0, 0, 255),
        (255, 0, 0),
        (255, 255, 0),
    ),
)

PALETTES = {WAVESHARE_7COLOR_6.name: WAVESHARE_7COLOR_6}


def get_palette(name: str) -> Palette:
    try:
        return PALETTES[name]
    except KeyError as exc:
        raise ValueError(f"Unknown palette {name!r}.") from exc


def nearest_palette_index(rgb: tuple[int, int, int], palette: Palette = WAVESHARE_7COLOR_6) -> int:
    r, g, b = rgb
    best_index = 0
    best_distance = float("inf")
    for index, (pr, pg, pb) in enumerate(palette.colors):
        distance = (r - pr) ** 2 + (g - pg) ** 2 + (b - pb) ** 2
        if distance < best_distance:
            best_distance = distance
            best_index = index
    return best_index


def image_to_palette_indices(image: Image.Image, palette: Palette = WAVESHARE_7COLOR_6) -> list[int]:
    rgb_image = image.convert("RGB")
    raw = rgb_image.tobytes()
    return [
        nearest_palette_index((raw[index], raw[index + 1], raw[index + 2]), palette)
        for index in range(0, len(raw), 3)
    ]


def indices_to_image(
    indices: Iterable[int],
    *,
    width: int,
    height: int,
    palette: Palette = WAVESHARE_7COLOR_6,
) -> Image.Image:
    values = list(indices)
    if len(values) != width * height:
        raise ValueError(f"Expected {width * height} pixels, got {len(values)}.")
    image = Image.new("RGB", (width, height))
    image.putdata([palette.colors[index] for index in values])
    return image


def pack_indices(indices: Iterable[int], bits_per_pixel: int = 4) -> bytes:
    values = list(indices)
    if bits_per_pixel not in (1, 2, 4):
        raise ValueError("Only 1, 2, and 4 bpp packing is supported.")
    max_value = (1 << bits_per_pixel) - 1
    packed = bytearray()
    accumulator = 0
    bits_used = 0
    for value in values:
        if value < 0 or value > max_value:
            raise ValueError(f"Palette index {value} does not fit in {bits_per_pixel} bpp.")
        shift = 8 - bits_per_pixel - bits_used
        accumulator |= value << shift
        bits_used += bits_per_pixel
        if bits_used == 8:
            packed.append(accumulator)
            accumulator = 0
            bits_used = 0
    if bits_used:
        packed.append(accumulator)
    return bytes(packed)


def unpack_indices(data: bytes, pixel_count: int, bits_per_pixel: int = 4) -> list[int]:
    if bits_per_pixel not in (1, 2, 4):
        raise ValueError("Only 1, 2, and 4 bpp packing is supported.")
    mask = (1 << bits_per_pixel) - 1
    values: list[int] = []
    for byte in data:
        for shift in range(8 - bits_per_pixel, -1, -bits_per_pixel):
            values.append((byte >> shift) & mask)
            if len(values) == pixel_count:
                return values
    if len(values) != pixel_count:
        raise ValueError(f"Packed data ended after {len(values)} pixels; expected {pixel_count}.")
    return values


def raw_frame_from_image(image: Image.Image, palette: Palette = WAVESHARE_7COLOR_6) -> tuple[bytes, str]:
    indices = image_to_palette_indices(image, palette)
    raw = pack_indices(indices, palette.bits_per_pixel)
    return raw, hashlib.sha256(raw).hexdigest()
