#!/usr/bin/env python3
"""Portfolio gallery tools, used by the webmaster Portfolio page (tools/admin.py).

Commands:
  add <staging_dir> <category> <caption>   resize, save and watermark photos staged by admin.py
  move <file> <category>                   change the category of one photo
  remove <file>                            take one photo out (originals go to media/_Dipadam)
  category <key> <label>                   add a new category (tab)
  commit <message>                         save the changes as a git commit on this server

Source of truth: site/data/portfolio.json (the list of photos and categories).
Clean originals: media/gallery/<name>.webp (1600px) and <name>-full.webp (up to 6000px).
Thumbnails:      site/img/gallery/<name>-sm.webp (720px, never watermarked).
Watermarked copies are made by tools/watermark.py from media/gallery.
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
DATA = REPO / "site" / "data" / "portfolio.json"
MEDIA = REPO / "media" / "gallery"
THUMBS = REPO / "site" / "img" / "gallery"
TRASH = REPO / "media" / "_Dipadam"
KEY_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,40}$")
FILE_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,80}$")
EXT = {".jpg", ".jpeg", ".webp"}

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))


def die(msg):
    print(f"!! {msg}")
    sys.exit(1)


def load():
    return json.loads(DATA.read_text(encoding="utf-8"))


def save(d):
    DATA.write_text(json.dumps(d, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def category_keys(d):
    return {c["key"] for c in d.get("categories", [])}


def find(d, name):
    for item in d["items"]:
        if item["file"] == name:
            return item
    die(f"photo {name} is not in the portfolio")


def slug(text, limit=40):
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:limit].strip("-") or "photo"


def new_name(existing, original):
    stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    while True:
        name = f"{slug(pathlib.Path(original).stem)}-{stamp}-{secrets.token_hex(2)}"
        if name not in existing and FILE_RE.match(name):
            return name


def write_versions(im, name):
    """Save the three sizes. im is an RGB image already turned upright."""
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
    return full.size


def refresh_watermarks():
    import watermark
    watermark.main()


def cmd_add(staging, category, caption):
    staging = pathlib.Path(staging)
    d = load()
    if category not in category_keys(d):
        die(f"unknown category {category}")
    caption = caption.strip()[:200]
    existing = {i["file"] for i in d["items"]}
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
            size = write_versions(im, name)
            new_items.append({"file": name, "category": category, "caption": caption,
                              "full": True, "size": f"{size[0]}×{size[1]}"})
            print(f"+ {original} -> {name} ({size[0]}×{size[1]})")
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    if not new_items:
        die("no photo could be processed")
    d["items"] = new_items + d["items"]
    save(d)
    refresh_watermarks()
    print(f"Added {len(new_items)} photo(s) to '{category}'.")


def cmd_move(name, category):
    d = load()
    if category not in category_keys(d):
        die(f"unknown category {category}")
    item = find(d, name)
    item["category"] = category
    save(d)
    print(f"Moved {name} to '{category}'.")


def cmd_remove(name):
    d = load()
    find(d, name)
    d["items"] = [i for i in d["items"] if i["file"] != name]
    save(d)
    TRASH.mkdir(parents=True, exist_ok=True)
    for suffix in ("", "-full"):
        src = MEDIA / f"{name}{suffix}.webp"
        if src.exists():
            shutil.move(str(src), str(TRASH / f"{name}{suffix}.webp"))
    for path in (THUMBS / f"{name}-sm.webp",):
        if path.exists():
            path.unlink()
    refresh_watermarks()
    print(f"Removed {name}. Original moved to media/_Dipadam.")


def cmd_category(key, label):
    if not KEY_RE.match(key):
        die("category key must be lowercase letters, numbers or dashes")
    d = load()
    if key in category_keys(d):
        die(f"category {key} already exists")
    d.setdefault("categories", []).append({"key": key, "label": label.strip()[:40] or key})
    save(d)
    print(f"Added category '{label}' ({key}).")


def cmd_commit(message):
    # watermarked copies and the watermark record are generated files (see .gitignore), so they are not committed
    paths = ["site/data/portfolio.json", "media/gallery", "site/img/gallery"]
    subprocess.run(["git", "add", "-A", "--"] + paths, cwd=REPO, check=True)
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=REPO).returncode == 0:
        print("Nothing new to save.")
        return
    subprocess.run(["git", "-c", "user.name=Webmaster", "-c", "user.email=webmaster@johorstudio.com",
                    "commit", "-q", "-m", message], cwd=REPO, check=True)
    print(f"Saved on the server: {message}")
    try:
        r = subprocess.run(["git", "push", "-q", "origin", "HEAD:main"], cwd=REPO,
                           capture_output=True, text=True, timeout=60)
        if r.returncode == 0:
            print("Also pushed to GitHub.")
        else:
            print("Not pushed to GitHub yet (the server has no write access). It is kept on the server.")
    except Exception:
        print("Not pushed to GitHub yet (the server has no write access). It is kept on the server.")


def main(argv):
    if len(argv) < 2:
        die("usage: portfolio.py add|move|remove|category|commit ...")
    cmd, args = argv[1], argv[2:]
    if cmd == "add" and len(args) == 3:
        return cmd_add(*args)
    if cmd == "move" and len(args) == 2:
        return cmd_move(*args)
    if cmd == "remove" and len(args) == 1:
        return cmd_remove(*args)
    if cmd == "category" and len(args) == 2:
        return cmd_category(*args)
    if cmd == "commit" and len(args) == 1:
        return cmd_commit(*args)
    die(f"bad command: {cmd} {args}")


if __name__ == "__main__":
    main(sys.argv)
