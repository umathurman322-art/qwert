from __future__ import annotations

import io
import random
import string

from PIL import Image, ImageDraw, ImageFont
from aiogram.types import BufferedInputFile


def math_captcha() -> tuple[str, str]:
    a, b = random.randint(2, 20), random.randint(2, 20)
    return f"{a} + {b}", str(a + b)


def image_captcha() -> tuple[BufferedInputFile, str]:
    code = "".join(random.choices(string.digits, k=4))
    img = Image.new("RGB", (240, 90), (24, 28, 40))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 42)
    except OSError:
        font = ImageFont.load_default()
    draw.text((40, 22), code, fill=(240, 240, 255), font=font)
    for _ in range(8):
        draw.line(
            (
                random.randint(0, 240),
                random.randint(0, 90),
                random.randint(0, 240),
                random.randint(0, 90),
            ),
            fill=(80, 90, 120),
            width=1,
        )
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return BufferedInputFile(buf.read(), filename="captcha.png"), code
