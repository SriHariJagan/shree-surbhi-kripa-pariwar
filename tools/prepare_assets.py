#!/usr/bin/env python3
"""Prepare optimised website images, the official payment QR and favicon.

Usage: python tools/prepare_assets.py
Source photos are read from ./images (never modified).
Outputs go to ./assets/images and ./assets/brand.
"""

from pathlib import Path
from PIL import Image, ImageOps, ImageEnhance

import json

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "images"
OUT = ROOT / "assets" / "images"
BRAND = ROOT / "assets" / "brand"
OUT.mkdir(parents=True, exist_ok=True)
BRAND.mkdir(parents=True, exist_ok=True)
MANIFEST = {}

# ---------------------------------------------------------------------------
# Source -> output map.  Keep the original WhatsApp files untouched.
# kind controls the responsive widths that are generated.
# ---------------------------------------------------------------------------
ASSETS = {
    "acharya-river": ("WhatsApp Image 2026-11-24 at 11.04.18 AM (1).jpeg", "portrait"),
    "cow-embrace": ("WhatsApp Image 2026-11-24 at 11.04.16 AM (2).jpeg", "portrait"),
    "acharya-portrait": ("WhatsApp Image 2026-11-24 at 11.04.19 AM (2).jpeg", "portrait"),
    "acharya-orange": ("WhatsApp Image 2026-11-24 at 11.04.20 AM.jpeg", "portrait"),
    "acharya-stage": ("WhatsApp Image 2026-11-24 at 11.04.18 AM.jpeg", "portrait"),
    "acharya-contemplation": ("WhatsApp Image 2026-11-24 at 11.04.11 AM.jpeg", "portrait"),
    "gau-seva-black-cow": ("WhatsApp Image 2026-11-24 at 11.04.22 AM (1).jpeg", "landscape"),
    "gau-seva-brown-cow": ("WhatsApp Image 2026-11-24 at 11.04.17 AM.jpeg", "portrait"),
    "community-event": ("WhatsApp Image 2026-11-24 at 11.04.13 AM (1).jpeg", "landscape"),
    "youth-temple": ("WhatsApp Image 2026-11-24 at 11.04.19 AM.jpeg", "portrait"),
    "youth-group": ("WhatsApp Image 2026-11-24 at 11.04.22 AM.jpeg", "landscape"),
    "temple-visit": ("WhatsApp Image 2026-11-24 at 11.04.23 AM (1).jpeg", "square"),
    "honours-shawl": ("WhatsApp Image 2026-11-24 at 11.04.25 AM (1).jpeg", "portrait"),
    "civic-desk": ("WhatsApp Image 2026-11-24 at 11.04.46 AM.jpeg", "square"),
    "civic-portrait": ("WhatsApp Image 2026-11-24 at 11.04.45 AM.jpeg", "landscape"),
    "satsang-seated": ("WhatsApp Image 2026-11-24 at 11.04.12 AM.jpeg", "landscape"),
    "elder-sadhu": ("WhatsApp Image 2026-11-24 at 11.04.15 AM (2).jpeg", "portrait"),
    "cloth-offering": ("WhatsApp Image 2026-11-24 at 11.04.13 AM (2).jpeg", "portrait"),
    "with-swami": ("WhatsApp Image 2026-11-24 at 11.04.11 AM (1).jpeg", "landscape"),
    "senior-swami": ("WhatsApp Image 2026-11-24 at 11.04.12 AM (2).jpeg", "portrait"),
    "hindu-sammelan": ("WhatsApp Image 2026-11-24 at 11.04.24 AM.jpeg", "portrait"),
    "civic-meeting": ("WhatsApp Image 2026-11-24 at 11.04.16 AM (1).jpeg", "landscape"),
    "vishwa-shanti": ("WhatsApp Image 2026-11-24 at 11.04.23 AM.jpeg", "portrait"),
    # press
    "press-feature": ("WhatsApp Image 2026-11-24 at 11.04.28 AM (2).jpeg", "landscape"),
    "press-cow": ("WhatsApp Image 2026-11-24 at 11.04.26 AM (1).jpeg", "landscape"),
    "press-seva": ("WhatsApp Image 2026-11-24 at 11.04.29 AM (1).jpeg", "portrait"),
    "press-culture": ("WhatsApp Image 2026-11-24 at 11.04.34 AM.jpeg", "portrait"),
    "press-shivratri": ("WhatsApp Image 2026-11-24 at 11.04.25 AM (2).jpeg", "landscape"),
    "press-unity": ("WhatsApp Image 2026-11-24 at 11.04.25 AM.jpeg", "portrait"),
    # current event poster (lives in the project root)
    "event-katha": ("../currentEvent.png", "event"),
    # openly licensed photographs (see credits on the pages that use them)
    "agnihotra-yagya": ("../assets/source/agnihotra-yagya.jpg", "portrait"),
    "tree-plantation": ("../assets/source/tree-plantation.jpg", "landscape"),
    "community-meal": ("../assets/source/community-meal.jpg", "square"),
}

WIDTHS = {
    "portrait": [640, 1080, 1500],
    "landscape": [640, 1080, 1600],
    "square": [640, 1080, 1400],
    "event": [480, 800, 1204],
}

def warm_grade(img: Image.Image, kind: str = "") -> Image.Image:
    """A very light, consistent grade. Keeps skin tones natural."""
    img = ImageOps.exif_transpose(img).convert("RGB")
    if kind == "event":
        # The event poster is already colour-managed; leave it untouched.
        return img
    img = ImageEnhance.Color(img).enhance(1.03)
    img = ImageEnhance.Contrast(img).enhance(1.025)
    img = ImageEnhance.Brightness(img).enhance(1.01)
    return img


def build_image(name: str, src_name: str, kind: str) -> None:
    src_path = SRC / src_name
    if not src_path.exists():
        print(f"  ! missing: {src_name}")
        return
    img = warm_grade(Image.open(src_path), kind)
    original_w, original_h = img.size
    print(f"  · {name}: {original_w}x{original_h}")
    quality = 90 if kind == "event" else 84

    generated = []
    for requested in WIDTHS[kind]:
        width = min(requested, original_w)
        height = round(original_h * (width / original_w))
        variant = img.resize((width, height), Image.Resampling.LANCZOS)
        out_name = f"{name}-{width}.webp"
        variant.save(OUT / out_name, "WEBP", quality=quality, method=6)
        generated.append({"width": width, "height": height, "file": out_name})
    # De-duplicate widths (small sources produce the same width more than once).
    seen = set()
    generated = [g for g in generated if not (g["width"] in seen or seen.add(g["width"]))]
    # Also save a default file for direct use.
    default_width = min(original_w, 1600 if kind != "portrait" else 1500)
    if kind == "event":
        default_width = min(original_w, 1204)
    height = round(original_h * (default_width / original_w))
    img.resize((default_width, height), Image.Resampling.LANCZOS).save(
        OUT / f"{name}.webp", "WEBP", quality=92 if kind == "event" else 86, method=6
    )
    MANIFEST[name] = {
        "width": original_w,
        "height": original_h,
        "default": f"{name}.webp",
        "variants": generated,
    }


def build_official_qr() -> None:
    """Crop the supplied ICICI/UPI QR to a clean square for the site."""
    source = ROOT / "qrCode.png"
    if not source.exists():
        print("  ! missing: qrCode.png")
        return
    img = Image.open(source).convert("RGB")
    # The QR data modules occupy x=133-581, y=542-990. Add a quiet white margin.
    margin = 28
    box = (133 - margin, 542 - margin, 581 + margin, 990 + margin)
    qr = img.crop(box)
    size = min(qr.size)
    qr = qr.crop((0, 0, size, size))
    qr.save(OUT / "qr-official.png", "PNG", optimize=True)
    upi = (
        "upi://pay?pa=msshreesurbhikripapariwar.eazypay@icici"
        "&pn=MSSHREESURBHIKRIPAPARIWAR&cu=INR"
    )
    (OUT / "qr-official.txt").write_text(upi, encoding="utf-8")
    print(f"  · official QR -> {qr.size[0]}x{qr.size[1]} px")


def build_favicon() -> None:
    """Favicons and app icons from the circular brand mark."""
    master_path = BRAND / "logo-mark.webp"
    if not master_path.exists():
        print("  · logo-mark.webp missing, skipping favicons")
        return
    master = Image.open(master_path).convert("RGBA")
    for size in (32, 192):
        master.resize((size, size), Image.LANCZOS).save(
            BRAND / f"favicon-{size}.png", optimize=True
        )
    touch = master.resize((180, 180), Image.LANCZOS)
    apple = Image.new("RGB", (180, 180), (244, 236, 221))
    apple.paste(touch, (0, 0), touch)
    apple.save(BRAND / "apple-touch-icon.png", optimize=True)
    master.resize((256, 256), Image.LANCZOS).save(
        BRAND / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)]
    )


if __name__ == "__main__":
    print("Preparing images…")
    for name, (src_name, kind) in ASSETS.items():
        build_image(name, src_name, kind)
    print("Building favicon…")
    build_favicon()
    print("Building official QR…")
    build_official_qr()
    (OUT / "manifest.json").write_text(
        json.dumps(MANIFEST, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Wrote {OUT / 'manifest.json'} ({len(MANIFEST)} entries)")
    print("Done.")
