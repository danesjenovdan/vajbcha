import io
import math
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from .base import BaseCaptcha
from .font import DotMatrixFont


class ImageCaptcha(BaseCaptcha):
    """
    Captcha implementation that renders distorted text using Pillow.

    Characters are drawn individually with random rotation and positional
    jitter. Random noise lines and dots are added to hinder automated
    solving. Characters are rendered using DotMatrixFont — no font files
    are required.
    """

    # Image dimensions
    WIDTH = 220
    HEIGHT = 90

    # Appearance
    BG_COLOR = (45, 45, 60)
    NOISE_LINE_COUNT = 10
    NOISE_DOT_COUNT = 100
    GRID_SPACING = 14  # pixels between grid lines
    CHAR_ROTATE_RANGE = (-30, 30)  # degrees
    GRID_ROTATE_RANGE = (-25, 25)  # degrees
    CHAR_JITTER_Y = 20  # pixels

    def __init__(self, dot_size: int = 3, dot_gap: int = 2) -> None:
        super().__init__()
        self._dot_size = dot_size
        self._dot_gap = dot_gap

    def _create_media(self, answer: str) -> bytes:
        image = Image.new("RGB", (self.WIDTH, self.HEIGHT), color=self.BG_COLOR)
        draw = ImageDraw.Draw(image)

        self._draw_grid(image)
        self._draw_noise_dots(draw)
        self._draw_noise_lines(draw)
        self._draw_characters(image, answer)

        # Light blur to blend layers
        image = image.filter(ImageFilter.GaussianBlur(radius=0.5))

        self._invert_region(image)

        buf = io.BytesIO()
        image.save(buf, "PNG")
        return buf.getvalue()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _random_color(self, dark: bool = True) -> tuple[int, int, int]:
        if dark:
            # Subtle dark tones for noise on dark background
            return (
                random.randint(65, 100),
                random.randint(65, 100),
                random.randint(65, 100),
            )
        # Light colors for character dots on dark background
        return (
            random.randint(180, 255),
            random.randint(180, 255),
            random.randint(180, 255),
        )

    def _invert_region(self, image: Image.Image) -> None:
        # Pick a random rectangle covering between 1/4 and 2/3 of the image area.
        w, h = image.size
        rw = random.randint(w // 4, int(w * 2 / 3))
        rh = random.randint(h // 4, int(h * 2 / 3))
        x0 = random.randint(0, w - rw)
        y0 = random.randint(0, h - rh)
        box = (x0, y0, x0 + rw, y0 + rh)
        region = image.crop(box)
        inverted = ImageChops.invert(region)
        image.paste(inverted, box)

    def _draw_grid(self, image: Image.Image) -> None:
        angle = random.uniform(*self.GRID_ROTATE_RANGE)
        # Oversized canvas so the rotated grid covers the full image
        diag = int(math.hypot(self.WIDTH, self.HEIGHT)) + self.GRID_SPACING * 2
        grid = Image.new("RGB", (diag, diag), color=self.BG_COLOR)
        grid_draw = ImageDraw.Draw(grid)
        color = self._random_color(dark=True)
        for x in range(0, diag, self.GRID_SPACING):
            grid_draw.line([(x, 0), (x, diag)], fill=color, width=1)
        for y in range(0, diag, self.GRID_SPACING):
            grid_draw.line([(0, y), (diag, y)], fill=color, width=1)
        rotated = grid.rotate(angle, resample=Image.Resampling.BILINEAR, expand=False)
        # Crop the center of the rotated canvas to the image size
        cx, cy = diag // 2, diag // 2
        left = cx - self.WIDTH // 2
        top = cy - self.HEIGHT // 2
        cropped = rotated.crop((left, top, left + self.WIDTH, top + self.HEIGHT))
        image.paste(cropped, (0, 0))

    def _draw_noise_lines(self, draw: ImageDraw.ImageDraw) -> None:
        margin = max(self.WIDTH, self.HEIGHT) // 2
        for _ in range(self.NOISE_LINE_COUNT):
            x1 = random.randint(-margin, self.WIDTH + margin)
            y1 = random.randint(-margin, self.HEIGHT + margin)
            x2 = random.randint(-margin, self.WIDTH + margin)
            y2 = random.randint(-margin, self.HEIGHT + margin)
            w = random.randint(2, 8)
            draw.line([(x1, y1), (x2, y2)], fill=self._random_color(dark=True), width=w)

    def _draw_noise_dots(self, draw: ImageDraw.ImageDraw) -> None:
        for _ in range(self.NOISE_DOT_COUNT):
            x = random.randint(0, self.WIDTH)
            y = random.randint(0, self.HEIGHT)
            r = random.randint(1, 4)
            draw.ellipse(
                [(x - r, y - r), (x + r, y + r)], fill=self._random_color(dark=True)
            )

    def _draw_characters(self, image: Image.Image, answer: str) -> None:
        n = len(answer)
        slot_w = self.WIDTH // n
        font_1x = DotMatrixFont(
            dot_size=self._dot_size,
            dot_gap=self._dot_gap,
            char_gap=0,
        )
        char_w = font_1x.char_width
        char_h = font_1x.char_height
        pad = max(char_w, char_h) // 2  # room for rotation without clipping
        canvas_size = (char_w + pad * 2, char_h + pad * 2)

        for i, char in enumerate(answer):
            # Draw at 2× scale, rotate, then downscale for crisp dots.
            scale = 2
            scaled_canvas = (canvas_size[0] * scale, canvas_size[1] * scale)
            tmp = Image.new("RGBA", scaled_canvas, (0, 0, 0, 0))
            tmp_draw = ImageDraw.Draw(tmp)
            color = self._random_color(dark=False)
            font_2x = DotMatrixFont(
                dot_size=self._dot_size * scale,
                dot_gap=self._dot_gap * scale,
                char_gap=0,
            )
            font_2x.draw_char(tmp_draw, char, pad * scale, pad * scale, color + (255,))

            pixel_bbox = tmp.getbbox()
            if pixel_bbox:
                tmp = tmp.crop(pixel_bbox)

            angle = random.randint(*self.CHAR_ROTATE_RANGE)
            rotated = tmp.rotate(angle, expand=True, resample=Image.Resampling.BILINEAR)
            # Downscale back to 1× with antialiasing
            final = rotated.resize(
                (rotated.width // scale, rotated.height // scale),
                resample=Image.Resampling.LANCZOS,
            )

            # Target position: center of the slot with vertical jitter
            target_x = slot_w * i + (slot_w - final.width) // 2
            jitter_y = random.randint(-self.CHAR_JITTER_Y, self.CHAR_JITTER_Y)
            target_y = (self.HEIGHT - final.height) // 2 + jitter_y

            image.paste(final, (target_x, target_y), final)
