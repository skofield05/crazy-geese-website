"""
Einmal-Helper zum Aufbereiten von WhatsApp-Bildern fuer den Blog.

- Nimmt Quellordner mit JPEGs
- Schreibt fuer jede Datei zwei Varianten ins Zielverzeichnis:
    <slug>-<nn>.jpg      -> max. 1600px Breite, Qualitaet 82 (Lightbox)
    <slug>-<nn>-thumb.jpg -> max.  800px laengste Kante, Qualitaet 78 (Kachel)
  Die Kachel begrenzt bewusst die LAENGSTE Kante, nicht die Breite: ein
  Hochformat 900x1600 bliebe sonst 800x1422 gross und waere als Thumbnail
  kaum kleiner als das Vollbild (gemessen: 231 KB Thumb zu 287 KB Full).
- Respektiert EXIF-Orientierung und strippt EXIF-Metadaten fuers Web.

Nutzung:
    python scripts/optimize_blog_images.py \
        --src "blog/Schulcup 2026-04" \
        --dst "img/blog/schulcup-mattersburg-2026-04" \
        --slug schulcup-mattersburg
"""
from __future__ import annotations

import argparse
import pathlib
import sys

from PIL import Image, ImageOps


FULL_MAX_WIDTH = 1600
THUMB_MAX_SIDE = 800
FULL_QUALITY = 82
THUMB_QUALITY = 78


def optimize(src_dir: pathlib.Path, dst_dir: pathlib.Path, slug: str) -> None:
    dst_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in src_dir.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".jfif", ".png"})
    if not files:
        print(f"Keine Bilder in {src_dir}", file=sys.stderr)
        return

    for idx, src in enumerate(files, start=1):
        with Image.open(src) as im:
            im = ImageOps.exif_transpose(im)
            if im.mode != "RGB":
                im = im.convert("RGB")

            full_name = f"{slug}-{idx:02d}.jpg"
            thumb_name = f"{slug}-{idx:02d}-thumb.jpg"

            full = _resize_max_width(im, FULL_MAX_WIDTH)
            full.save(dst_dir / full_name, "JPEG", quality=FULL_QUALITY, optimize=True, progressive=True)

            thumb = _resize_max_side(im, THUMB_MAX_SIDE)
            thumb.save(dst_dir / thumb_name, "JPEG", quality=THUMB_QUALITY, optimize=True, progressive=True)

        full_kb = (dst_dir / full_name).stat().st_size // 1024
        thumb_kb = (dst_dir / thumb_name).stat().st_size // 1024
        print(f"{src.name} -> {full_name} ({full_kb} KB), {thumb_name} ({thumb_kb} KB)")


def _resize_max_side(im: Image.Image, max_side: int) -> Image.Image:
    """Skaliert so, dass die laengste Kante max_side nicht ueberschreitet."""
    longest = max(im.width, im.height)
    if longest <= max_side:
        return im.copy()
    ratio = max_side / longest
    return im.resize((round(im.width * ratio), round(im.height * ratio)), Image.LANCZOS)


def _resize_max_width(im: Image.Image, max_width: int) -> Image.Image:
    if im.width <= max_width:
        return im.copy()
    ratio = max_width / im.width
    return im.resize((max_width, round(im.height * ratio)), Image.LANCZOS)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", required=True)
    parser.add_argument("--dst", required=True)
    parser.add_argument("--slug", required=True)
    args = parser.parse_args()
    optimize(pathlib.Path(args.src), pathlib.Path(args.dst), args.slug)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
