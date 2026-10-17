#!/usr/bin/env python3
"""Raya studio photos, used by the webmaster Raya page (tools/admin.py).

Commands:
  add <staging_dir> <rating>   resize, save and watermark photos staged by admin.py (rating 0 = not rated yet)
  rate <file> <rating>         set the rating 1-5, or 0 to hide the photo from the public page
  remove <file>                take one photo out (originals go to media/_Dipadam)
  commit <message>             save the changes as a git commit and try to push it

Source of truth: site/data/raya-gallery.json. Clean originals: media/raya/<name>.webp (1600px)
and <name>-full.webp (up to 6000px). Thumbnails: site/img/raya/<name>-sm.webp (720px, never watermarked).
Watermarked copies are made by tools/watermark.py from media/raya.
The public Raya page shows only rated photos, 5 stars first. Visitors never see the ratings.
"""
import datetime
import json
import pathlib
import re
import secrets
import shutil
import subprocess
import sys

from PIL import Image, ImageOps

REPO = pathlib.Path(__file__).resolve().parent.parent
DATA = REPO / "site" / "data" / "raya-gallery.json"
MEDIA = REPO / "media" / "raya"
THUMBS = REPO / "site" / "img" / "raya"
TRASH = REPO / "media" / "_Dipadam"
FILE_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,80}$")
EXT = {".jpg", ".jpeg", ".webp"}

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))


def die(msg):
    print(f"!! {msg}")
    sys.exit(1)


def load():
    return json.loads(DATA.read_text(encoding="utf-8"))


def save(items):
    DATA.write_text(json.dumps(items, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def find(items, name):
    for item in items:
        if item["file"] == name:
            return item
    die(f"photo {name} is not in the Raya gallery")


def slug(text, limit=40):
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:limit].strip("-") or "photo"


def new_name(existing, original):
    stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    while True:
        name = f"raya-{slug(pathlib.Path(original).stem)}-{stamp}-{secrets.token_hex(2)}"
        if name not in existing and FILE_RE.match(name):
            return name


def write_versions(im, name):
    """Save the three sizes. im is an RGB image already turned upright. Returns (full size, thumb size)."""
    MEDIA.mkdir(parents=True, exist_ok=True)
    THUMBS.mkdir(parents=True, exist_ok=True)
    big = im.copy()
    big.thumbnail((1600, 1600), Image.LANCZOS)
    big.save(MEDIA / f"{name}.webp", "WEBP", quality=78, method=6)
    full = im.copy()
    if max(full.size) > 6000:
        full.thumbnail((6000, 6000), Image.LANCZOS)
    full.save(MEDIA / f"{name}-full.webp", "WEBP", quality=82, method=6)
    small = im.copy()
    small.thumbnail((720, 720), Image.LANCZOS)
    small.save(THUMBS / f"{name}-sm.webp", "WEBP", quality=74, method=6)
    return full.size, small.size


def refresh_watermarks():
    import watermark
    watermark.main()


def cmd_add(staging, rating):
    staging = pathlib.Path(staging)
    items = load()
    existing = {i["file"] for i in items}
    new_items = []
    try:
        for src in sorted(staging.iterdir()):
            if src.suffix.lower() not in EXT:
                continue
            name_file = src.with_suffix(".txt")
            original = name_file.read_text(encoding="utf-8") if name_file.exists() else src.name
            try:
                with Image.open(src) as raw:
                    im = ImageOps.exif_transpose(raw).convert("RGB")
            except Exception as err:
                print(f"! skipped {original}: not a readable photo ({err})")
                continue
            name = new_name(existing, original)
            existing.add(name)
            full, small = write_versions(im, name)
            new_items.append({"file": name, "size": f"{full[0]}×{full[1]}",
                              "sm": [small[0], small[1]], "rating": rating})
            print(f"+ {original} -> {name} ({full[0]}×{full[1]}), rating {rating}")
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    if not new_items:
        die("no photo could be processed")
    items = new_items + items
    save(items)
    refresh_watermarks()
    print(f"Added {len(new_items)} photo(s).")


def cmd_rate(name, rating):
    items = load()
    find(items, name)["rating"] = rating
    save(items)
    print(f"Rated {name}: {rating if rating else 'not rated (hidden)'}.")


def cmd_remove(name):
    items = load()
    find(items, name)
    save([i for i in items if i["file"] != name])
    TRASH.mkdir(parents=True, exist_ok=True)
    for suffix in ("", "-full"):
        src = MEDIA / f"{name}{suffix}.webp"
        if src.exists():
            shutil.move(str(src), str(TRASH / f"{name}{suffix}.webp"))
    thumb = THUMBS / f"{name}-sm.webp"
    if thumb.exists():
        thumb.unlink()
    refresh_watermarks()
    print(f"Removed {name}. Original moved to media/_Dipadam.")


def cmd_commit(message):
    # watermarked copies and the watermark record are generated files (see .gitignore), so they are not committed
    paths = ["site/data/raya-gallery.json", "media/raya", "site/img/raya"]
    subprocess.run(["git", "add", "-A", "--"] + paths, cwd=REPO, check=True)
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=REPO).returncode == 0:
        print("Nothing new to save.")
        return
    subprocess.run(["git", "-c", "user.name=Webmaster", "-c", "user.email=webmaster@johorstudio.com",
                    "commit", "-q", "-m", message], cwd=REPO, check=True)
    print(f"Saved: {message}")
    try:
        r = subprocess.run(["git", "push", "-q", "origin", "HEAD:main"], cwd=REPO,
                           capture_output=True, text=True, timeout=60)
        print("Also pushed to GitHub." if r.returncode == 0 else
              "Not pushed to GitHub yet (the server has no write access). It is kept on the server.")
    except Exception:
        print("Not pushed to GitHub yet (the server has no write access). It is kept on the server.")


def main(argv):
    if len(argv) < 2:
        die("usage: raya.py add|rate|remove|commit ...")
    cmd, args = argv[1], argv[2:]
    if cmd == "add" and len(args) == 2 and args[1].isdigit() and int(args[1]) <= 5:
        return cmd_add(args[0], int(args[1]))
    if cmd == "rate" and len(args) == 2 and args[1].isdigit() and int(args[1]) <= 5:
        return cmd_rate(args[0], int(args[1]))
    if cmd == "remove" and len(args) == 1:
        return cmd_remove(*args)
    if cmd == "commit" and len(args) == 1:
        return cmd_commit(*args)
    die(f"bad command: {cmd} {args}")


if __name__ == "__main__":
    main(sys.argv)
