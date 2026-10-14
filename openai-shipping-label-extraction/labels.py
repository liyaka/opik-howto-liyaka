"""Fictional shipping labels, rendered locally with Pillow at run time.

Each entry in LABELS holds the ground truth for one label plus the "damage"
applied when drawing it: rotation, low contrast, smudges, a handwritten-style
field, or a torn patch across the barcode. The PNGs are written to out/ (git
ignored) and regenerated on every run, so the repo ships no binaries.
"""

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT_DIR = Path(__file__).parent / "out"
W, H = 720, 960

FONTS = {
    "sans": ["/System/Library/Fonts/Supplemental/Arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
    "bold": ["/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
    "mono": ["/System/Library/Fonts/Supplemental/Courier New Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"],
    "hand": ["/System/Library/Fonts/Supplemental/Bradley Hand Bold.ttf", "/System/Library/Fonts/MarkerFelt.ttc"],
}

# Ground truth. The expected values live only here and in the suite assertions
# built from them; the model only ever sees the rendered pixels.
LABELS = [
    {
        "id": "clean-ground",
        "kind": "clean label, printed fields",
        "carrier": "Northwind Parcel",
        "tracking_number": "NP 4827 1093 5561",
        "service_level": "Ground",
        "sender_name": "Fernhill Candle Co.",
        "recipient_name": "Marta Oyelaran",
        "recipient_address": "18 Alder Row, Millbrook",
        "recipient_postcode": "MB4 7QT",
        "weight_kg": 2.4,
        "ship_date": "2026-09-14",
        "date_text": "14 SEP 2026",
        "effects": [],
    },
    {
        "id": "rotated-overnight",
        "kind": "label photographed at an angle (rotated 7 degrees)",
        "carrier": "Kestrel Express",
        "tracking_number": "KX-90314-6627-B",
        "service_level": "Overnight",
        "sender_name": "Tidewater Books",
        "recipient_name": "Jonas Whitcombe",
        "recipient_address": "402 Harbor Lane, Port Selby",
        "recipient_postcode": "PS9 2LD",
        "weight_kg": 0.8,
        "ship_date": "2026-10-02",
        "date_text": "02 OCT 2026",
        "effects": ["rotate"],
    },
    {
        "id": "faded-smudged",
        "kind": "low-contrast thermal print with ink smudges",
        "carrier": "BlueHeron Freight",
        "tracking_number": "BHF 7731 0482 9916",
        "service_level": "Economy",
        "sender_name": "Orchard Lane Tools",
        "recipient_name": "Priya Venkataraman",
        "recipient_address": "7 Quarry Close, Eastvale",
        "recipient_postcode": "EV1 5RN",
        "weight_kg": 11.6,
        "ship_date": "2026-08-27",
        "date_text": "27 AUG 2026",
        "effects": ["fade", "smudge"],
    },
    {
        "id": "handwritten-recipient",
        "kind": "recipient block and weight filled in by hand",
        "carrier": "Quokka Post",
        "tracking_number": "QP2026 5540 1187",
        "service_level": "Express",
        "sender_name": "Brindle & Finch Ceramics",
        "recipient_name": "Dewi Hartshorne",
        "recipient_address": "56 Cobbler's Walk, Ashgrove",
        "recipient_postcode": "AG6 3HB",
        "weight_kg": 3.7,
        "ship_date": "2026-10-09",
        "date_text": "09 OCT 2026",
        "effects": ["handwritten"],
    },
    {
        "id": "torn-barcode",
        "kind": "barcode area torn, tracking digits partly missing",
        "carrier": "Kestrel Express",
        "tracking_number": "KX-55208-1943-M",
        "service_level": "Ground",
        "sender_name": "Saltmarsh Pantry",
        "recipient_name": "Ibrahim Castellanos",
        "recipient_address": "91 Linden Terrace, Wrenfield",
        "recipient_postcode": "WF2 8PJ",
        "weight_kg": 5.2,
        "ship_date": "2026-09-30",
        "date_text": "30 SEP 2026",
        "effects": ["tear"],
    },
    {
        "id": "everything-wrong",
        "kind": "rotated, faded, smudged and torn all at once",
        "carrier": "Northwind Parcel",
        "tracking_number": "NP 1096 7742 3085",
        "service_level": "Overnight",
        "sender_name": "Copperleaf Apothecary",
        "recipient_name": "Nkechi Ravensdale",
        "recipient_address": "23 Millstone Yard, Oldcastle",
        "recipient_postcode": "OC3 9ZX",
        "weight_kg": 1.3,
        "ship_date": "2026-10-11",
        "date_text": "11 OCT 2026",
        "effects": ["rotate", "fade", "smudge", "tear"],
    },
]


def font(kind: str, size: int) -> ImageFont.FreeTypeFont:
    for path in FONTS[kind]:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def _barcode(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], seed: str) -> None:
    rng = random.Random(seed)
    x0, y0, x1, y1 = box
    x = x0
    while x < x1:
        bar = rng.choice([2, 2, 3, 4, 6])
        draw.rectangle([x, y0, min(x + bar, x1), y1], fill=(15, 15, 15))
        x += bar + rng.choice([2, 3, 4, 6])


def _draw_label(label: dict) -> Image.Image:
    img = Image.new("RGB", (W, H), (250, 250, 247))
    d = ImageDraw.Draw(img)
    ink = (20, 20, 20)
    hand = "handwritten" in label["effects"]
    d.rectangle([14, 14, W - 14, H - 14], outline=ink, width=5)

    d.text((34, 30), label["carrier"].upper(), font=font("bold", 40), fill=ink)
    sf = font("bold", 30)
    d.text((W - 34 - d.textlength(label["service_level"].upper(), font=sf), 46),
           label["service_level"].upper(), font=sf, fill=ink)
    d.line([14, 100, W - 14, 100], fill=ink, width=4)

    d.text((34, 116), "FROM", font=font("sans", 22), fill=ink)
    d.text((34, 146), label["sender_name"], font=font("bold", 30), fill=ink)
    d.text((34, 190), f"SHIP DATE  {label['date_text']}", font=font("sans", 24), fill=ink)
    d.line([14, 240, W - 14, 240], fill=ink, width=3)

    d.text((34, 256), "SHIP TO", font=font("sans", 22), fill=ink)
    if hand:
        hf = font("hand", 46)
        d.text((44, 292), label["recipient_name"], font=hf, fill=(30, 40, 110))
        d.text((44, 352), label["recipient_address"], font=hf, fill=(30, 40, 110))
        d.text((44, 412), label["recipient_postcode"], font=hf, fill=(30, 40, 110))
    else:
        d.text((44, 292), label["recipient_name"], font=font("bold", 40), fill=ink)
        d.text((44, 346), label["recipient_address"], font=font("bold", 32), fill=ink)
        d.text((44, 396), label["recipient_postcode"], font=font("bold", 56), fill=ink)
    d.line([14, 500, W - 14, 500], fill=ink, width=3)

    d.text((34, 516), "WEIGHT", font=font("sans", 22), fill=ink)
    wf = font("hand", 56) if hand else font("bold", 50)
    d.text((34, 544), f"{label['weight_kg']} kg", font=wf, fill=(30, 40, 110) if hand else ink)
    d.rectangle([W - 190, 520, W - 40, 620], outline=ink, width=4)
    d.text((W - 160, 538), label["service_level"][0], font=font("bold", 64), fill=ink)
    d.line([14, 650, W - 14, 650], fill=ink, width=3)

    _barcode(d, (50, 676, W - 50, 836), label["tracking_number"])
    tn = label["tracking_number"]
    tw = d.textlength(tn, font=font("mono", 38))
    d.text(((W - tw) / 2, 860), tn, font=font("mono", 38), fill=ink)
    d.text((34, 912), "TRACKING", font=font("sans", 18), fill=ink)
    return img


def _fade(img: Image.Image) -> Image.Image:
    bg = Image.new("RGB", img.size, (236, 236, 230))
    return Image.blend(img, bg, 0.72)


def _smudge(img: Image.Image, rng: random.Random) -> Image.Image:
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for _ in range(9):
        cx, cy = rng.randint(80, W - 80), rng.randint(280, 880)
        rx, ry = rng.randint(30, 90), rng.randint(10, 26)
        d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(90, 90, 90, 120))
    layer = layer.filter(ImageFilter.GaussianBlur(9))
    out = img.convert("RGBA")
    out.alpha_composite(layer)
    return out.convert("RGB").filter(ImageFilter.GaussianBlur(1.3))


def _tear(img: Image.Image, rng: random.Random) -> Image.Image:
    d = ImageDraw.Draw(img)
    top, bottom = 700, 905
    left = 480
    pts = [(left + rng.randint(-14, 14), top)]
    for y in range(top, bottom, 22):
        pts.append((left + rng.randint(-26, 26), y))
    pts += [(W - 14, bottom), (W - 14, top)]
    d.polygon(pts, fill=(218, 214, 205))
    for (x, y) in pts[:-2]:
        d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(150, 146, 138))
    return img


def render_label(label: dict, path: Path) -> Path:
    rng = random.Random(label["id"])
    img = _draw_label(label)
    fx = label["effects"]
    if "tear" in fx:
        img = _tear(img, rng)
    if "smudge" in fx:
        img = _smudge(img, rng)
    if "fade" in fx:
        img = _fade(img)
    if "rotate" in fx:
        img = img.rotate(7, expand=True, fillcolor=(205, 205, 200), resample=Image.BICUBIC)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, optimize=True)
    return path


def render_all(out_dir: Path = OUT_DIR) -> dict[str, Path]:
    return {lb["id"]: render_label(lb, out_dir / f"{lb['id']}.png") for lb in LABELS}


if __name__ == "__main__":
    for label_id, p in render_all().items():
        print(label_id, p)
