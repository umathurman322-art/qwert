from __future__ import annotations

import re


def parse_positive_number(text: str | None) -> float | None:
    if not text:
        return None
    cleaned = text.strip().replace(" ", "").replace(",", ".")
    cleaned = re.sub(r"[^\d.]", "", cleaned)
    if cleaned.count(".") > 1:
        return None
    try:
        value = float(cleaned)
    except ValueError:
        return None
    if value <= 0:
        return None
    return value


def parse_price_band(code: str) -> tuple[float | None, float | None]:
    if not code or code in {"any", "-"}:
        return None, None
    if "-" not in code:
        return None, None
    left, right = code.split("-", 1)
    try:
        return float(left), float(right)
    except ValueError:
        return None, None


def parse_catalog_callback(data: str) -> tuple[str | None, str | None, str, int]:
    # cat:rarity:type:band:page
    parts = data.split(":")
    if len(parts) < 5:
        return None, None, "any", 0
    rarity = None if parts[1] in {"-", ""} else parts[1]
    pet_type = None if parts[2] in {"-", ""} else parts[2]
    band = parts[3] or "any"
    try:
        page = int(parts[4])
    except ValueError:
        page = 0
    return rarity, pet_type, band, max(page, 0)
