"""Utility script: generate static/test.png for manual image testing.

Run directly:
    python generate_test_image.py

Or call generate_test_image() from any other module.
"""

import os

from PIL import Image, ImageDraw

from captcha.font import DotMatrixFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(BASE_DIR, "static", "test.png")


def generate_test_image(
    output_path: str = OUTPUT_PATH, width: int = 800, height: int = 600
) -> None:
    image = Image.new("RGB", (width, height), color=(18, 18, 28))
    draw = ImageDraw.Draw(image)

    # Subtle grid
    for x in range(0, width, 40):
        draw.line([(x, 0), (x, height)], fill=(30, 30, 45), width=1)
    for y in range(0, height, 40):
        draw.line([(0, y), (width, y)], fill=(30, 30, 45), width=1)

    # Border
    draw.rectangle([0, 0, width - 1, height - 1], outline=(80, 80, 120), width=2)

    font_large = DotMatrixFont(dot_size=8, dot_gap=3, char_gap=12)
    font_medium = DotMatrixFont(dot_size=5, dot_gap=2, char_gap=8)
    font_tiny = DotMatrixFont(dot_size=1, dot_gap=2, char_gap=3)

    # "DOT MATRIX": w=628, h=74
    font_large.draw_text_centred(draw, "DOT MATRIX", width, 36, (100, 220, 255))
    # "ABCDEFGHIJKLM": w=525, h=47
    font_medium.draw_text_centred(draw, "ABCDEFGHIJKLM", width, 170, (200, 200, 80))
    # "NOPQRSTUVWXYZ": w=525, h=47
    font_medium.draw_text_centred(draw, "NOPQRSTUVWXYZ", width, 234, (200, 200, 80))
    # "0 1 2 3 4 5 6 7 8 9": w=771, h=47
    font_medium.draw_text_centred(
        draw, "0 1 2 3 4 5 6 7 8 9", width, 320, (180, 130, 255)
    )
    # tiny labels — each char is 14px wide + 3 gap = 17px advance; 40 chars = 677px
    font_tiny.draw_text_centred(
        draw, "EDIT GENERATE TEST IMAGE PY TO CUSTOMISE", width, 450, (100, 100, 140)
    )
    font_tiny.draw_text_centred(
        draw, os.path.basename(output_path).upper(), width, 490, (70, 70, 100)
    )

    image.save(output_path, "PNG")
    print(f"Saved {output_path}")


if __name__ == "__main__":
    generate_test_image()
