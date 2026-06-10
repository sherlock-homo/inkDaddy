import unittest

from PIL import Image

from inkdaddy_hub.services.palette import (
    WAVESHARE_7COLOR_6,
    image_to_palette_indices,
    pack_indices,
    raw_frame_from_image,
    unpack_indices,
)


class PaletteTests(unittest.TestCase):
    def test_pack_unpack_four_bpp(self):
        indices = [0, 1, 2, 3, 4, 5, 0]
        packed = pack_indices(indices, bits_per_pixel=4)
        self.assertEqual(unpack_indices(packed, len(indices), bits_per_pixel=4), indices)

    def test_image_conversion_and_checksum(self):
        image = Image.new("RGB", (2, 2))
        image.putdata([(0, 0, 0), (255, 255, 255), (255, 0, 0), (255, 255, 0)])
        indices = image_to_palette_indices(image, WAVESHARE_7COLOR_6)
        self.assertEqual(indices, [0, 1, 4, 5])
        raw, digest = raw_frame_from_image(image, WAVESHARE_7COLOR_6)
        self.assertEqual(len(raw), 2)
        self.assertEqual(len(digest), 64)
