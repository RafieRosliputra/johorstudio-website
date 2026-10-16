#!/usr/bin/env python3
"""JohorStudio.com logo watermark, bottom-right corner.

Used in two ways:
  1. tools/projects.py calls add_watermark() for every project photo it publishes
     (the 1600px and full-resolution versions, which open when a photo is clicked).
  2. Run it directly to watermark the portfolio and Raya photos in site/img:
         python3 tools/watermark.py
     It remembers which files are done (site/img/.watermarked.json), so running it
     again only touches new or replaced photos. Thumbnails (-sm) are never watermarked.
"""
import hashlib
import json
import pathlib

from PIL import Image, ImageFilter

REPO = pathlib.Path(__file__).resolve().parent.parent
LOGO = REPO / "site" / "img" / "logo-light.png"   # white version of the logo
VERSION = 1            # change to re-watermark everything with a new design
WIDTH = 0.16           # logo width as a share of the photo's long side
OPACITY = 0.85

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
    lw = max(90, int(max(w, h) * WIDTH))
    lh = round(logo.height * lw / logo.width)
    mark = logo.resize((lw, lh), Image.LANCZOS)
    alpha = mark.getchannel("A").point(lambda a: int(a * OPACITY))
    mark.putalpha(alpha)
    # soft dark shadow so the white logo still reads on bright backgrounds
    pad = max(4, lw // 25)
    shadow_a = Image.new("L", (lw + pad * 4, lh + pad * 4), 0)
    shadow_a.paste(alpha.point(lambda a: int(a * 0.55)), (pad * 2, pad * 2))
    shadow_a = shadow_a.filter(ImageFilter.GaussianBlur(pad))
    margin = int(min(w, h) * 0.035)
    x, y = w - lw - margin, h - lh - margin
    out = im.copy()
    out.paste((0, 0, 0), (x - pad * 2, y - pad * 2), shadow_a)
    out.paste(mark, (x, y), mark)
    return out


def _sha(p):
    return hashlib.sha1(p.read_bytes()).hexdigest()


def watermark_folder_files(files, record):
    """Watermark WebP files in place. record: {name: sha of the watermarked file}."""
    done = 0
    for f in files:
        key = f"{f.parent.name}/{f.name}"
        if record.get(key, {}).get("sha") == _sha(f) and record[key].get("v") == VERSION:
            continue
        with Image.open(f) as raw:
            icc = raw.info.get("icc_profile")
            big = raw.size[0] > 2000 or raw.size[1] > 2000
            out = add_watermark(raw)
        kw = {"quality": 84 if big else 80, "method": 6}
        if icc:
            kw["icc_profile"] = icc
        out.save(f, "WEBP", **kw)
        record[key] = {"sha": _sha(f), "v": VERSION}
        done += 1
    return done


def main():
    rec_file = REPO / "site" / "img" / ".watermarked.json"
    try:
        record = json.loads(rec_file.read_text())
    except Exception:
        record = {}
    total = 0
    for folder in ("gallery", "raya"):
        d = REPO / "site" / "img" / folder
        if not d.is_dir():
            continue
        files = sorted(p for p in d.glob("*.webp") if not p.stem.endswith("-sm"))
        n = watermark_folder_files(files, record)
        print(f" {folder}: {n} watermarked, {len(files) - n} already done")
        total += n
    rec_file.write_text(json.dumps(record, indent=0, sort_keys=True))
    print("Done.")


if __name__ == "__main__":
    main()
