import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .base import BaseCaptcha


class TextCaptcha(BaseCaptcha):
    """Captcha implementation that renders distorted text using Pillow.

    Characters are drawn individually with random rotation and positional
    jitter. Random noise lines and dots are added to hinder automated
    solving. No external font file is required — the built-in ImageFont
    default is used, but a TTF path may be supplied for better styling.
    """

    # Image dimensions
    WIDTH = 220
    HEIGHT = 90

    # Appearance
    BG_COLOR = (245, 245, 245)
    NOISE_LINE_COUNT = 6
    NOISE_DOT_COUNT = 80
    CHAR_ROTATE_RANGE = (-30, 30)  # degrees
    CHAR_JITTER_Y = 8  # pixels

    def __init__(self, font_path: str | None = None, font_size: int = 32) -> None:
        super().__init__()
        self._font_path = font_path
        self._font_size = font_size

    def _create_image(self, captcha_id: str, answer: str, image_dir: str) -> None:
        image = Image.new("RGB", (self.WIDTH, self.HEIGHT), color=self.BG_COLOR)
        draw = ImageDraw.Draw(image)

        self._draw_noise_lines(draw)
        self._draw_noise_dots(draw)
        self._draw_characters(image, answer)

        # Light blur to blend layers
        image = image.filter(ImageFilter.GaussianBlur(radius=0.7))

        out_path = os.path.join(image_dir, f"{captcha_id}.png")
        image.save(out_path, "PNG")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_font(self):
        if self._font_path:
            return ImageFont.truetype(self._font_path, self._font_size)
        return ImageFont.load_default(size=self._font_size)

    def _random_color(self, dark: bool = True) -> tuple:
        if dark:
            return (
                random.randint(0, 120),
                random.randint(0, 120),
                random.randint(0, 120),
            )
        return (
            random.randint(150, 230),
            random.randint(150, 230),
            random.randint(150, 230),
        )

    def _draw_noise_lines(self, draw: ImageDraw.ImageDraw) -> None:
        for _ in range(self.NOISE_LINE_COUNT):
            x1 = random.randint(0, self.WIDTH)
            y1 = random.randint(0, self.HEIGHT)
            x2 = random.randint(0, self.WIDTH)
            y2 = random.randint(0, self.HEIGHT)
            draw.line(
                [(x1, y1), (x2, y2)], fill=self._random_color(dark=False), width=1
            )

    def _draw_noise_dots(self, draw: ImageDraw.ImageDraw) -> None:
        for _ in range(self.NOISE_DOT_COUNT):
            x = random.randint(0, self.WIDTH)
            y = random.randint(0, self.HEIGHT)
            draw.point((x, y), fill=self._random_color(dark=False))

    def _draw_characters(self, image: Image.Image, answer: str) -> None:
        font = self._get_font()
        n = len(answer)
        slot_w = self.WIDTH // n

        for i, char in enumerate(answer):
            # Measure the actual rendered glyph so the canvas is sized correctly
            # regardless of whether a TTF or the default bitmap font is used.
            bbox = font.getbbox(char)  # (left, top, right, bottom)
            glyph_w = bbox[2] - bbox[0]
            glyph_h = bbox[3] - bbox[1]
            pad = max(glyph_w, glyph_h) // 2  # room for rotation without clipping
            canvas_size = (glyph_w + pad * 2, glyph_h + pad * 2)

            tmp = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
            tmp_draw = ImageDraw.Draw(tmp)
            color = self._random_color(dark=True)
            # Draw at the padded offset so the glyph is centred on the canvas
            text_x = pad - bbox[0]
            text_y = pad - bbox[1]
            tmp_draw.text((text_x, text_y), char, font=font, fill=color + (255,))

            # Crop to the actual opaque pixel bounds so font-added spacing is removed
            # before rotation. getbbox() on the image uses the alpha channel to find
            # the tight bounding box of non-transparent pixels.
            pixel_bbox = tmp.getbbox()
            if pixel_bbox:
                tmp = tmp.crop(pixel_bbox)

            angle = random.randint(*self.CHAR_ROTATE_RANGE)
            rotated = tmp.rotate(angle, expand=True)

            # Target position: centre of the slot with vertical jitter
            target_x = slot_w * i + (slot_w - rotated.width) // 2
            jitter_y = random.randint(-self.CHAR_JITTER_Y, self.CHAR_JITTER_Y)
            target_y = (self.HEIGHT - rotated.height) // 2 + jitter_y

            image.paste(rotated, (target_x, target_y), rotated)
