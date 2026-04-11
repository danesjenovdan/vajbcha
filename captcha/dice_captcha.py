import os
import random
import time

from PIL import Image, ImageDraw, ImageFont

from .base import BaseCaptcha

# ---------------------------------------------------------------------------
# Pip positions as (x_fraction, y_fraction) within the die face area.
# Axes: x → right, y → down. Values follow standard d6 pip layout.
# ---------------------------------------------------------------------------
_L, _M, _R = 0.25, 0.5, 0.75
_T, _C, _B = 0.25, 0.5, 0.75

_PIP_POSITIONS: dict[int, list[tuple[float, float]]] = {
    1: [(_M, _C)],
    2: [(_R, _T), (_L, _B)],
    3: [(_R, _T), (_M, _C), (_L, _B)],
    4: [(_L, _T), (_R, _T), (_L, _B), (_R, _B)],
    5: [(_L, _T), (_R, _T), (_M, _C), (_L, _B), (_R, _B)],
    6: [(_L, _T), (_R, _T), (_L, _C), (_R, _C), (_L, _B), (_R, _B)],
}


class DiceCaptcha(BaseCaptcha):
    """Captcha that shows 2–4 rolled d6 dice; the user types the total sum.

    Two face styles are supported:
        "pips"    — classic dots (default)
        "numbers" — digit printed on each face

    To swap in this implementation, change one line in app.py:
        captcha_provider = DiceCaptcha()          # pips
        captcha_provider = DiceCaptcha("numbers") # numbers
    """

    MIN_DICE = 2
    MAX_DICE = 4

    # Die geometry
    DIE_SIZE = 72         # width and height of the die face, in pixels
    CORNER_RADIUS = 12
    PIP_RADIUS = 5

    # Scene geometry
    IMAGE_WIDTH = 340
    IMAGE_HEIGHT = 160

    # Colours
    TABLE_COLOR = (46, 94, 58)      # casino felt green
    DIE_COLOR = (255, 252, 235)     # warm ivory
    SHADOW_COLOR = (30, 60, 38)     # dark green shadow
    PIP_COLOR = (28, 28, 28)

    # Randomisation
    ROTATE_RANGE = (-20, 20)   # degrees
    JITTER_Y = 20              # max vertical offset from centre line, px

    def __init__(self, style: str = "numbers") -> None:
        if style not in ("pips", "numbers"):
            raise ValueError("style must be 'pips' or 'numbers'")
        super().__init__()
        self._style = style

    # ------------------------------------------------------------------
    # BaseCaptcha overrides
    # ------------------------------------------------------------------

    def _generate_answer(self) -> str:
        """Return comma-separated individual rolls, e.g. '3,5,2'.

        The rolls are stored as the canonical answer; verify() compares
        the user-supplied sum against sum(rolls).
        """
        num_dice = random.randint(self.MIN_DICE, self.MAX_DICE)
        rolls = [random.randint(1, 6) for _ in range(num_dice)]
        return ",".join(str(r) for r in rolls)

    def verify(self, captcha_id: str, answer: str) -> bool:
        """Accept the integer sum of all visible dice as the correct answer."""
        with self._lock:
            entry = self._store.pop(captcha_id, None)

        if entry is None:
            return False
        if time.time() > entry["expires_at"]:
            return False

        try:
            user_total = int(answer.strip())
        except ValueError:
            return False

        rolls = [int(r) for r in entry["answer"].split(",")]
        return user_total == sum(rolls)

    def _create_image(self, captcha_id: str, answer: str, image_dir: str) -> None:
        rolls = [int(r) for r in answer.split(",")]
        image = self._render_scene(rolls)
        out_path = os.path.join(image_dir, f"{captcha_id}.png")
        image.save(out_path, "PNG")

    # ------------------------------------------------------------------
    # Scene rendering
    # ------------------------------------------------------------------

    def _render_scene(self, rolls: list[int]) -> Image.Image:
        scene = Image.new("RGB", (self.IMAGE_WIDTH, self.IMAGE_HEIGHT), self.TABLE_COLOR)
        self._draw_felt_texture(scene)

        n = len(rolls)
        spacing = self.IMAGE_WIDTH // (n + 1)
        center_y = self.IMAGE_HEIGHT // 2

        for i, value in enumerate(rolls):
            x = spacing * (i + 1)
            y = center_y + random.randint(-self.JITTER_Y, self.JITTER_Y)
            angle = random.randint(*self.ROTATE_RANGE)
            die_img = self._render_die(value, angle)
            # Paste centred on (x, y)
            paste_x = x - die_img.width // 2
            paste_y = y - die_img.height // 2
            scene.paste(die_img, (paste_x, paste_y), die_img)

        return scene

    def _draw_felt_texture(self, image: Image.Image) -> None:
        """Scatter subtle noise dots to simulate fabric weave."""
        draw = ImageDraw.Draw(image)
        tr, tg, tb = self.TABLE_COLOR
        for _ in range(600):
            x = random.randint(0, self.IMAGE_WIDTH)
            y = random.randint(0, self.IMAGE_HEIGHT)
            delta = random.randint(-18, 18)
            color = (
                max(0, min(255, tr + delta)),
                max(0, min(255, tg + delta)),
                max(0, min(255, tb + delta)),
            )
            draw.point((x, y), fill=color)

    # ------------------------------------------------------------------
    # Die rendering
    # ------------------------------------------------------------------

    def _render_die(self, value: int, angle: int) -> Image.Image:
        """Return a transparent-background RGBA die image, rotated by angle."""
        pad = 12   # room around die body for shadow bleed and rotation
        canvas_size = self.DIE_SIZE + pad * 2
        canvas = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(canvas)

        # Drop shadow (offset +4px)
        offset = 4
        draw.rounded_rectangle(
            [pad + offset, pad + offset, pad + self.DIE_SIZE + offset, pad + self.DIE_SIZE + offset],
            radius=self.CORNER_RADIUS,
            fill=self.SHADOW_COLOR + (150,),
        )

        # Die face
        draw.rounded_rectangle(
            [pad, pad, pad + self.DIE_SIZE, pad + self.DIE_SIZE],
            radius=self.CORNER_RADIUS,
            fill=self.DIE_COLOR + (255,),
            outline=(190, 182, 160, 255),
            width=2,
        )

        if self._style == "pips":
            self._draw_pips(draw, pad, value)
        else:
            self._draw_number(draw, pad, value)

        return canvas.rotate(angle, expand=True)

    def _draw_pips(self, draw: ImageDraw.ImageDraw, pad: int, value: int) -> None:
        for xf, yf in _PIP_POSITIONS[value]:
            cx = int(pad + xf * self.DIE_SIZE)
            cy = int(pad + yf * self.DIE_SIZE)
            r = self.PIP_RADIUS
            draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=self.PIP_COLOR)

    def _draw_number(self, draw: ImageDraw.ImageDraw, pad: int, value: int) -> None:
        font_size = int(self.DIE_SIZE * 0.6)
        font = ImageFont.load_default(size=font_size)
        text = str(value)
        bbox = font.getbbox(text)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        cx = pad + (self.DIE_SIZE - text_w) // 2 - bbox[0]
        cy = pad + (self.DIE_SIZE - text_h) // 2 - bbox[1]
        draw.text((cx, cy), text, font=font, fill=self.PIP_COLOR)
