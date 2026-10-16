#!/usr/bin/env python3
"""JohorStudio.com logo watermark, bottom-right corner.

Used in two ways:
  1. tools/projects.py calls add_watermark() for every project photo it publishes
     (the 1600px and full-resolution versions, which open when a photo is clicked).
  2. Portfolio and Raya photos: the clean originals live in media/gallery/ and
     media/raya/ (the 1600px "name.webp" and full-size "name-full.webp" files).
     main() writes watermarked copies to site/img/gallery/ and site/img/raya/.
     Thumbnails (name-sm.webp) stay in site/img/ and are never watermarked.

main() runs automatically from ./publish.sh, ./update.sh and the GitHub Pages
build. It only redoes photos that are new or changed, or all of them when the
watermark design below changes. To run it alone:  python3 tools/watermark.py
"""
import hashlib
import json
import pathlib

from PIL import Image, ImageFilter

REPO = pathlib.Path(__file__).resolve().parent.parent
LOGO = REPO / "site" / "img" / "logo-light.png"   # white version of the logo
WIDTH = 0.112          # logo width as a share of the photo's long side
OPACITY = 0.85
MIN_WIDTH = 70         # pixels
VERSION = f"2-{WIDTH}-{OPACITY}"   # any change here re-watermarks everything

_logo = None


def _load_logo():
    global _logo
    if _logo is None:
        _logo = Image.open(LOGO).convert("RGBA")
    return _logo


def add_watermark(im):
    """Return a copy of an RGB image with the logo at the bottom right."""
    im = im.convert("RGB")
    w, h = im.size
    logo = _load_logo()
    lw = max(MIN_WIDTH, int(max(w, h) * WIDTH))
    lh = round(logo.height * lw / logo.width)
    mark = logo.resize((lw, lh), Image.LANCZOS)
    alpha = mark.getchannel("A").point(lambda a: int(a * OPACITY))
    mark.putalpha(alpha)
    # soft dark shadow so the white logo still reads on bright backgrounds
    pad = max(3, lw // 25)
    shadow_a = Image.new("L", (lw + pad * 4, lh + pad * 4), 0)
    shadow_a.paste(alpha.point(lambda a: int(a * 0.55)), (pad * 2, pad * 2))
    shadow_a = shadow_a.filter(ImageFilter.GaussianBlur(pad))
    margin = int(min(w, h) * 0.03)
    x, y = w - lw - margin, h - lh - margin
    out = im.copy()
    out.paste((0, 0, 0), (x - pad * 2, y - pad * 2), shadow_a)
    out.paste(mark, (x, y), mark)
    return out


def _sha(p):
    return hashlib.sha1(p.read_bytes()).hexdigest()


def main():
    rec_file = REPO / "site" / "img" / ".watermarked.json"
    try:
        record = json.loads(rec_file.read_text())
    except Exception:
        record = {}
    for folder in ("gallery", "raya"):
        src_dir, out_dir = REPO / "media" / folder, REPO / "site" / "img" / folder
        if not src_dir.is_dir():
            continue
        out_dir.mkdir(parents=True, exist_ok=True)
        made = kept = 0
        wanted = set()
        for src in sorted(src_dir.glob("*.webp")):
            dst = out_dir / src.name
            wanted.add(src.name)
            key = f"{folder}/{src.name}"
            sig = f"{_sha(src)}:{VERSION}"
            if record.get(key) == sig and dst.exists():
                kept += 1
                continue
            with Image.open(src) as raw:
                icc = raw.info.get("icc_profile")
                big = max(raw.size) > 2000
                out = add_watermark(raw)
            kw = {"quality": 84 if big else 80, "method": 4}
            if icc:
                kw["icc_profile"] = icc
            out.save(dst, "WEBP", **kw)
            record[key] = sig
            made += 1
        # remove watermarked copies whose original was deleted
        for f in out_dir.glob("*.webp"):
            if not f.stem.endswith("-sm") and f.name not in wanted:
                f.unlink()
                record.pop(f"{folder}/{f.name}", None)
        print(f" {folder}: {made} watermarked, {kept} unchanged")
    rec_file.write_text(json.dumps(record, indent=0, sort_keys=True))


if __name__ == "__main__":
    main()
