#!/usr/bin/env python3
"""Publish project posts (like a blog) from folders of photos.

Every folder becomes one project page:

    projects/20261003 Sambutan Maulid Akbar/      <- folder name = date + title
        project.md                                <- optional: title, date, location, description
        IMG_0001.jpg  IMG_0002.jpg  ...           <- photos (jpg, png, webp, heic), shown in name order

Folders are read from projects/ in this repo and, if set, from the upload
folder (UPLOADS environment variable; /uploads inside Docker). A folder in
the upload folder with the same name as one in projects/ replaces it.
Folders whose name starts with "_" are drafts and are skipped.

Generated (not stored in git):
    site/projects/index.html              the Projects page (all posts, newest first)
    site/projects/<slug>/index.html       one page per project
    site/projects/<slug>/img/*.webp       photos: -sm (720px), normal (1600px), -full (original size)
    site/data/projects.json               used by "Recent projects" on the home page
    site/sitemap.xml

Photos are converted only when new or changed, so running it again is quick.

On TrueNAS:  docker compose run --rm publish
Elsewhere:   python3 tools/projects.py      (needs: pip install pillow)
"""
import datetime
import hashlib
import html
import json
import os
import pathlib
import re
import shutil
import sys

from PIL import Image, ImageOps

try:  # iPhone / Samsung HEIC photos, when pillow-heif is installed
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIC = True
except Exception:
    HEIC = False

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from layout import render, SITE, WA, WA_ICON  # noqa: E402

REPO = pathlib.Path(__file__).resolve().parent.parent
SITE_DIR = REPO / "site"
OUT = SITE_DIR / "projects"
CACHE_FILE = OUT / ".cache.json"
IMG_EXT = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"} | ({".heic", ".heif"} if HEIC else set())
SIZES = (("-sm", 720, 74), ("", 1600, 78))
FULL_MAX, FULL_Q = 6000, 82
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August",
          "September", "October", "November", "December"]
MAIN_PAGES = ["", "services.html", "portfolio.html", "projects/", "raya.html", "about.html", "contact.html"]

e = html.escape


# ---------------------------------------------------------------- reading folders

def sources():
    dirs = [REPO / "projects"]
    up = os.environ.get("UPLOADS")
    if up:
        dirs.append(pathlib.Path(up))
    found = {}
    for d in dirs:
        if not d.is_dir():
            continue
        for f in sorted(d.iterdir()):
            if f.is_dir() and not f.name.startswith(("_", ".", "@")):
                found[f.name] = f          # later folders (uploads) replace earlier ones
    return list(found.values())


def natural_key(name):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", name)]


def read_md(folder):
    mds = sorted(folder.glob("*.md"), key=lambda p: (p.name.lower() != "project.md", p.name))
    if not mds:
        return {}, ""
    text = mds[0].read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    meta = {}
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line and not line.lstrip().startswith("#"):
                k, v = line.split(":", 1)
                v = v.strip()
                if len(v) > 1 and v[0] == v[-1] and v[0] in "\"'":
                    v = v[1:-1]
                meta[k.strip().lower()] = v
        text = m.group(2)
    return meta, text.strip()


def parse_date(s):
    """'2026-10-03', '20261003', '2026-10', '2026' -> (sort key, label)."""
    s = (s or "").strip()
    m = re.match(r"^(\d{4})-?(\d{2})-?(\d{2})$", s)
    if m:
        y, mo, d = map(int, m.groups())
        return f"{y:04d}-{mo:02d}-{d:02d}", f"{d} {MONTHS[mo-1]} {y}"
    m = re.match(r"^(\d{4})-?(\d{2})$", s)
    if m:
        y, mo = map(int, m.groups())
        return f"{y:04d}-{mo:02d}-00", f"{MONTHS[mo-1]} {y}"
    m = re.match(r"^(\d{4})$", s)
    if m:
        return f"{s}-00-00", s
    return "", s


def from_folder_name(name):
    """'20261003 Sambutan Maulid Akbar' -> ('20261003', 'Sambutan Maulid Akbar')."""
    m = re.match(r"^(\d{8})(?:-(\d{1,2}))?[\s_\-–]*(.*)$", name)
    if m:
        title = m.group(3).strip(" -_–")
        return m.group(1), m.group(2), title or name
    return "", None, name


def slugify(s, limit=70):
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:limit].rstrip("-") or "project"


# ---------------------------------------------------------------- markdown (small subset)

def inline(t):
    t = e(t, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<em>\1</em>", t)
    t = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2">\1</a>', t)
    return t


def markdown(text):
    out = []
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = [l.rstrip() for l in block.splitlines() if l.strip()]
        if not lines:
            continue
        if all(re.match(r"^\s*[-*]\s+", l) for l in lines):
            out.append("<ul>" + "".join(f"<li>{inline(re.sub(r'^\s*[-*]\s+', '', l))}</li>" for l in lines) + "</ul>")
        elif lines[0].startswith("#"):
            out.append(f"<h2>{inline(lines[0].lstrip('#').strip())}</h2>")
            if lines[1:]:
                out.append(f"<p>{inline(' '.join(lines[1:]))}</p>")
        else:
            out.append(f"<p>{inline(' '.join(lines))}</p>")
    return "\n".join(out)


def plain(text, limit=160):
    t = re.sub(r"[*_#>\[\]]|\(https?://[^)]+\)", "", text.split("\n\n")[0]).strip()
    t = re.sub(r"\s+", " ", t)
    return t if len(t) <= limit else t[:limit].rsplit(" ", 1)[0] + "…"


# ---------------------------------------------------------------- photos

def file_sig(p):
    h = hashlib.sha1()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def to_rgb(im):
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGB", im.size, (255, 255, 255))
        bg.paste(im, mask=im.split()[-1])
        return bg
    return im.convert("RGB")


def save_webp(im, path, maxside, q, icc):
    im = im.copy()
    if max(im.size) > maxside:
        im.thumbnail((maxside, maxside), Image.LANCZOS)
    kw = {"quality": q, "method": 6}
    if icc:
        kw["icc_profile"] = icc
    im.save(path, "WEBP", **kw)
    return im.size


def process_photo(src, dest_dir, stem, full, cache):
    """Make the WebP versions of one photo. Returns info for the page."""
    sig = file_sig(src)
    key = f"{dest_dir.parent.name}/{stem}"
    old = cache.get(key)
    outs = [dest_dir / f"{stem}{suf}.webp" for suf, _, _ in SIZES] + ([dest_dir / f"{stem}-full.webp"] if full else [])
    if old and old.get("sig") == sig and old.get("full") == full and all(o.exists() for o in outs):
        return old, False
    with Image.open(src) as raw:
        icc = raw.info.get("icc_profile")
        im = to_rgb(ImageOps.exif_transpose(raw))
    w, h = im.size
    info = {"sig": sig, "full": full, "w": w, "h": h}
    for suf, size, q in SIZES:
        sw, sh = save_webp(im, dest_dir / f"{stem}{suf}.webp", size, q, icc)
        info["sm" if suf else "md"] = [sw, sh]
    if full:
        if src.suffix.lower() == ".webp" and max(w, h) <= FULL_MAX:
            shutil.copyfile(src, dest_dir / f"{stem}-full.webp")   # already WebP: keep as is
        else:
            fw, fh = save_webp(im, dest_dir / f"{stem}-full.webp", FULL_MAX, FULL_Q, icc)
            info["w"], info["h"] = fw, fh
    cache[key] = info
    return info, True


# ---------------------------------------------------------------- one project

def load_project(folder):
    meta, body = read_md(folder)
    fdate, fend, ftitle = from_folder_name(folder.name)
    title = meta.get("title") or ftitle
    sort, label = parse_date(meta.get("date") or fdate)
    end = meta.get("end") or (fdate[:6] + fend.zfill(2) if fend else "")
    if end and sort[8:] not in ("", "00"):
        esort, _ = parse_date(end)
        if esort and esort > sort:
            y, m, d1, d2 = int(sort[:4]), int(sort[5:7]), int(sort[8:]), int(esort[8:])
            if esort[:7] == sort[:7]:
                label = f"{d1}–{d2} {MONTHS[m-1]} {y}"
    photos = sorted((p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in IMG_EXT
                     and not p.name.startswith(("._", "."))), key=lambda p: natural_key(p.name))
    datekey = "".join(x for x in sort.split("-") if x != "00") if sort else ""
    slug = slugify(f"{datekey} {title}")
    return {
        "folder": folder, "slug": slug, "title": title, "sort": sort, "date": label,
        "location": meta.get("location", ""), "client": meta.get("client", ""),
        "services": meta.get("services", ""), "cover": meta.get("cover", ""),
        "hidden": meta.get("hidden", "").lower() in ("true", "yes", "1"),
        "body": body, "photos": photos,
    }


def build_photos(p, cache):
    dest = OUT / p["slug"] / "img"
    dest.mkdir(parents=True, exist_ok=True)
    used, items, new = set(), [], 0
    for src in p["photos"]:
        stem = slugify(src.stem, 60)
        base, n = stem, 2
        while stem in used:
            stem, n = f"{base}-{n}", n + 1
        used.add(stem)
        full = not src.name.lower().startswith("bts")      # behind-the-scenes photos: no full size
        try:
            info, made = process_photo(src, dest, stem, full, cache)
        except Exception as err:  # unreadable or unsupported file
            print(f"   ! skipped {src.name}: {err}")
            continue
        new += made
        items.append({"stem": stem, "name": src.name, **info})
    keep = {f"{i['stem']}{s}.webp" for i in items for s in ("-sm", "", "-full")}
    for f in dest.iterdir():
        if f.name not in keep:
            f.unlink()
    return items, new


def pick_cover(p, items):
    if not items:
        return None
    want = p["cover"].lower()
    for i in items:
        if want and (i["name"].lower() == want or i["stem"] == slugify(pathlib.Path(want).stem, 60)):
            return i
    return items[0]


# ---------------------------------------------------------------- HTML

def meta_list(p):
    rows = [("Date", p["date"]), ("Location", p["location"]), ("Client", p["client"]), ("Services", p["services"])]
    return "".join(f"<div><dt>{k}</dt><dd>{e(v)}</dd></div>" for k, v in rows if v)


def project_page(p, items, prev, nxt):
    n = len(items)
    thumbs = []
    for k, i in enumerate(items):
        cap = f"{p['title']}, photo {k + 1} of {n}"
        full = (f' data-full="img/{i["stem"]}-full.webp" data-size="{i["w"]}×{i["h"]}"' if i["full"] else "")
        sw, sh = i["sm"]
        thumbs.append(
            f'<button type="button" class="lb-thumb" data-lightbox data-src="img/{i["stem"]}.webp"{full} '
            f'data-caption="{e(cap)}"><img src="img/{i["stem"]}-sm.webp" width="{sw}" height="{sh}" '
            f'alt="{e(cap)}"{"" if k < 6 else " loading=\"lazy\""} decoding="async"></button>')
    gallery = (f'''<section class="wrap pj-photos">
  <p class="muted">{n} photo{"s" if n != 1 else ""}. Tap a photo to view it at full resolution.</p>
  <div class="gallery">
{chr(10).join(thumbs)}
  </div>
</section>''' if items else "")
    pager = ""
    if prev or nxt:
        a = f'<a class="pj-prev" href="../{prev["slug"]}/"><span>Newer</span>{e(prev["title"])}</a>' if prev else "<span></span>"
        b = f'<a class="pj-next" href="../{nxt["slug"]}/"><span>Older</span>{e(nxt["title"])}</a>' if nxt else "<span></span>"
        pager = f'<nav class="wrap pj-pager" aria-label="More projects">{a}{b}</nav>'
    body = f'''
<section class="page-head pj-head"><div class="wrap">
  <p class="pj-crumb"><a href="../">Projects</a></p>
  <h1>{e(p["title"])}</h1>
  <dl class="pj-meta">{meta_list(p)}</dl>
  <div class="pj-desc">{markdown(p["body"]) if p["body"] else ""}</div>
</div></section>
{gallery}
{pager}
<section class="cta-band"><div class="wrap">
  <h2>Planning something similar?</h2>
  <div class="actions"><a class="btn" href="{WA}">{WA_ICON}WhatsApp us</a><a class="btn btn-line" href="../../contact.html">Get a quotation</a></div>
</div></section>
'''
    desc = plain(p["body"]) or f"{p['title']}{', ' + p['location'] if p['location'] else ''}. Photography and video by JohorStudio.com."
    cover = p.get("cover_item")
    og = f"{SITE}/projects/{p['slug']}/img/{cover['stem']}.webp" if cover else None
    return render("projects/", f"{p['title']} | JohorStudio.com", desc, body, root="../../",
                  path=f"projects/{p['slug']}/", og_image=og, body_class="page-projects page-project")


def card(p, root=""):
    c = p.get("cover_item")
    where = " · ".join(x for x in (p["date"], p["location"]) if x)
    if c:
        sw, sh = c["sm"]
        fig = (f'<figure><img src="{root}{p["slug"]}/img/{c["stem"]}-sm.webp" width="{sw}" height="{sh}" '
               f'alt="{e(p["title"])}" loading="lazy" decoding="async"></figure>')
    else:
        fig = f'<figure class="pj-text"><p>{e(plain(p["body"], 110) or p["title"])}</p></figure>'
    count = f'<span class="pj-count">{len(p["items"])} photos</span>' if p["items"] else ""
    return (f'<a class="pj-card" href="{root}{p["slug"]}/" data-year="{p["sort"][:4]}">{fig}'
            f'<p class="pj-when">{e(where)}</p><h2>{e(p["title"])}</h2>'
            f'<p class="pj-services">{e(p["services"])}{count}</p></a>')


def index_page(projects):
    years = sorted({p["sort"][:4] for p in projects if p["sort"]}, reverse=True)
    chips = ""
    if len(years) > 1:
        chips = ('<div class="filters" role="group" aria-label="Filter by year" data-year-filter>'
                 '<button type="button" data-year="all" aria-pressed="true">All</button>'
                 + "".join(f'<button type="button" data-year="{y}" aria-pressed="false">{y}</button>' for y in years)
                 + "</div>")
    body = f'''
<section class="page-head"><div class="wrap">
  <h1>Projects</h1>
  <p class="lead">Events, ceremonies and productions we have covered, newest first. Open a project to see the photos.</p>
</div></section>
<section class="wrap" style="padding-bottom:72px">
  {chips}
  <div class="pj-grid">
{chr(10).join(card(p) for p in projects)}
  </div>
</section>
'''
    return render("projects/", "Projects | JohorStudio.com",
                  "Events, convocations, corporate functions and productions covered by JohorStudio.com in Johor and across Malaysia.",
                  body, root="../", path="projects/")


def sitemap(projects):
    today = datetime.date.today().isoformat()
    urls = [f"{SITE}/{u}" for u in MAIN_PAGES] + [f"{SITE}/projects/{p['slug']}/" for p in projects]
    rows = "\n".join(f"  <url><loc>{u}</loc><lastmod>{today}</lastmod></url>" for u in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{rows}\n</urlset>\n'


# ---------------------------------------------------------------- main

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        cache = json.loads(CACHE_FILE.read_text())
    except Exception:
        cache = {}
    projects = [p for p in (load_project(f) for f in sources()) if not p["hidden"]]
    seen = set()
    for p in projects:                                 # make slugs unique
        base, n = p["slug"], 2
        while p["slug"] in seen:
            p["slug"], n = f"{base}-{n}", n + 1
        seen.add(p["slug"])
    projects.sort(key=lambda p: (p["sort"] or "0000", p["title"].lower()), reverse=True)

    print(f"Publishing {len(projects)} project(s){'' if HEIC else ' (HEIC photos not supported here)'}")
    for p in projects:
        p["items"], new = build_photos(p, cache)
        p["cover_item"] = pick_cover(p, p["items"])
        print(f" ✓ {p['title']}  —  {len(p['items'])} photos{f', {new} new' if new else ''}")
        if 0 < len(p["items"]) < 10:
            print(f"   note: only {len(p['items'])} photos (10 or more looks best)")

    for i, p in enumerate(projects):
        prev = projects[i - 1] if i > 0 else None
        nxt = projects[i + 1] if i + 1 < len(projects) else None
        (OUT / p["slug"] / "index.html").write_text(project_page(p, p["items"], prev, nxt), encoding="utf-8")
    (OUT / "index.html").write_text(index_page(projects), encoding="utf-8")

    # remove pages of projects whose folder is gone
    for d in OUT.iterdir():
        if d.is_dir() and d.name not in seen:
            shutil.rmtree(d)
    cache = {k: v for k, v in cache.items() if k.split("/")[0] in seen}
    CACHE_FILE.write_text(json.dumps(cache))

    data = [{
        "slug": p["slug"], "url": f"projects/{p['slug']}/", "title": p["title"], "date": p["date"],
        "sort": p["sort"], "location": p["location"], "client": p["client"], "services": p["services"],
        "summary": plain(p["body"], 140), "photos": len(p["items"]),
        "cover": f"projects/{p['slug']}/img/{p['cover_item']['stem']}-sm.webp" if p["cover_item"] else None,
        "cover_md": f"projects/{p['slug']}/img/{p['cover_item']['stem']}.webp" if p["cover_item"] else None,
    } for p in projects]
    (SITE_DIR / "data").mkdir(exist_ok=True)
    (SITE_DIR / "data" / "projects.json").write_text(json.dumps({"items": data}, indent=1, ensure_ascii=False), encoding="utf-8")
    (SITE_DIR / "sitemap.xml").write_text(sitemap(projects), encoding="utf-8")
    print("Done. Open /projects/ on the website to check.")


if __name__ == "__main__":
    main()
