#!/usr/bin/env python3
"""Publish project posts (like a blog) from folders of photos.

Where projects come from
    1. New folders in the upload folder (UPLOADS, /uploads in Docker): only folders
       directly in the root. Folders starting with "_" or "." and the "_DONE" folder
       are ignored. After a folder is published it is moved into "_DONE".
    2. projects/ in this repo: added once, when the project is not on the website yet.

Every folder is one project page:

    20261003 Sambutan Maulid Akbar/      <- folder name = date + title
        project.md                       <- optional: title, date, location, client, services, cover, body
        IMG_0001.jpg  IMG_0002.jpg  ...  <- photos (jpg, png, webp, heic), shown in name order

Publishing only ADDS or UPDATES projects. Projects already on the website stay there
even if their folder is gone. Projects are removed with --remove-project / --remove-photo,
which move the original files into the upload folder as "_<folder name>".

Each published project is stored in the website folder (site/projects/<slug>/meta.json),
so the website does not depend on the source folders any more.

If one folder fails, it is left where it is, the project on the website stays as it was,
and the problem is listed at the end of the log.

Generated (not stored in git):
    site/projects/index.html              the Projects page (all posts, newest first)
    site/projects/<slug>/index.html       one page per project
    site/projects/<slug>/img/*.webp       photos: -sm (720px), normal (1600px), -full (original size)
    site/projects/<slug>/meta.json        everything needed to rebuild the project page
    site/data/projects.json               used by "Recent projects" on the home page
    site/sitemap.xml

Photos are converted only when new or changed, so running it again is quick.
The 1600px and full-size versions get the logo watermark (tools/watermark.py);
thumbnails do not.

On TrueNAS:  docker compose run --rm publish
Elsewhere:   python3 tools/projects.py      (needs: pip install pillow)
Remove:      python3 tools/projects.py --remove-project SLUG
             python3 tools/projects.py --remove-photo SLUG PHOTO-STEM
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
from watermark import add_watermark, cap_pixels, VERSION as WM_VERSION, QUALITY as PHOTO_Q, main as watermark_site_photos  # noqa: E402

REPO = pathlib.Path(__file__).resolve().parent.parent
SITE_DIR = REPO / "site"
OUT = SITE_DIR / "projects"
CACHE_FILE = OUT / ".cache.json"
REMOVED_FILE = OUT / ".removed.json"
STAGING = OUT / ".staging"
DONE = "_DONE"
IMG_EXT = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"} | ({".heic", ".heif"} if HEIC else set())
PREVIEW_SIDE = 600                                  # grid thumbnail
PHOTO_VER = f"24mp-q{PHOTO_Q}"                      # change this and every photo is redone
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August",
          "September", "October", "November", "December"]
MAIN_PAGES = ["", "services.html", "portfolio.html", "projects/", "raya.html", "about.html", "contact.html"]
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,80}$")

e = html.escape


# ---------------------------------------------------------------- folders

def uploads_dir():
    up = os.environ.get("UPLOADS")
    return pathlib.Path(up) if up else None


def subfolders(d):
    """Projects in a folder: subfolders only, skipping drafts, _DONE and hidden folders."""
    if not d or not d.is_dir():
        return []
    return [f for f in sorted(d.iterdir()) if f.is_dir() and not f.name.startswith(("_", ".", "@"))]


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


def process_photo(src, dest_dir, stem, full, cache, key, force=False):
    """Make the WebP versions of one photo. Returns (info, made_new)."""
    sig = file_sig(src)
    old = cache.get(key)
    outs = [dest_dir / f"{stem}-sm.webp", dest_dir / f"{stem}.webp"] + ([dest_dir / f"{stem}-full.webp"] if full else [])
    if (not force and old and old.get("sig") == sig and old.get("full") == full and old.get("wm") == WM_VERSION
            and old.get("pv") == PHOTO_VER and all(o.exists() for o in outs)):
        return old, False
    with Image.open(src) as raw:
        icc = raw.info.get("icc_profile")
        im = cap_pixels(to_rgb(ImageOps.exif_transpose(raw)))
    w, h = im.size
    info = {"sig": sig, "full": full, "w": w, "h": h, "wm": WM_VERSION, "pv": PHOTO_VER}
    # thumbnail stays clean; the versions that open on click carry the logo
    sw, sh = save_webp(im, dest_dir / f"{stem}-sm.webp", PREVIEW_SIDE, PHOTO_Q, icc)
    info["sm"] = [sw, sh]
    md = im.copy()
    md.thumbnail((1600, 1600), Image.LANCZOS)
    sw, sh = save_webp(add_watermark(md), dest_dir / f"{stem}.webp", 1600, PHOTO_Q, icc)
    info["md"] = [sw, sh]
    if full:
        fw, fh = save_webp(add_watermark(im), dest_dir / f"{stem}-full.webp", max(w, h), PHOTO_Q, icc)
        info["w"], info["h"] = fw, fh
    cache[key] = info
    return info, True


def find_original(m, i):
    """The original file of one photo, if it still exists (upload _DONE folder or repo projects/)."""
    up = uploads_dir()
    origin = i.get("origin", m["source"]["origin"])
    src = i.get("src", m["source"]["name"])
    if origin == "uploads":
        cands = [up / DONE / (i.get("done_as") or src), up / src] if up else []
    else:
        cands = [REPO / "projects" / src]
    for d in cands:
        f = d / i["name"]
        if f.is_file():
            return f
    return None


def recompress_existing(img, i):
    """No original left: re-encode the saved files. The watermark is not added again."""
    stem = i["stem"]
    out = {}
    for suffix, side in (("-full", None), ("", 1600), ("-sm", PREVIEW_SIDE)):
        f = img / f"{stem}{suffix}.webp"
        if not f.exists() or (suffix == "-full" and not i.get("full")):
            continue
        with Image.open(f) as im:
            im = cap_pixels(im.convert("RGB"))
            if side and max(im.size) > side:
                im.thumbnail((side, side), Image.LANCZOS)
            im.save(f, "WEBP", quality=PHOTO_Q, method=6)
            out[suffix] = list(im.size)
    if "-sm" in out:
        i["sm"] = out["-sm"]
    if "" in out:
        i["md"] = out[""]
    if "-full" in out:
        i["w"], i["h"] = out["-full"]
    i["pv"] = PHOTO_VER


def refresh_site_photos(state, cache):
    """Photos made before the current rule (24MP cap, WebP quality 50) are redone once.
    Originals are used when they still exist; otherwise the saved files are re-encoded."""
    changed = 0
    for slug, m in state.items():
        img = OUT / slug / "img"
        todo = [i for i in m.get("items", []) if i.get("pv") != PHOTO_VER]
        if not todo or not img.is_dir():
            continue
        for i in todo:
            try:
                src = find_original(m, i)
                if src is not None:
                    info, _ = process_photo(src, img, i["stem"], i["full"], cache, f"{slug}/{i['stem']}", force=True)
                    i.update(info)
                else:
                    recompress_existing(img, i)
                changed += 1
            except Exception as err:
                print(f"   ! {slug}/{i['name']}: {err}")
        (OUT / slug / "meta.json").write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
    if changed:
        print(f"Photos updated to 24MP / quality {PHOTO_Q}: {changed}")
    return changed


def photo_files(folder):
    return sorted((p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in IMG_EXT
                   and not p.name.startswith(("._", "."))), key=lambda p: natural_key(p.name))


def unique_stem(name, used):
    base = slugify(pathlib.Path(name).stem, 60)
    stem, n = base, 2
    while stem in used:
        stem, n = f"{base}-{n}", n + 1
    return stem


def pick_cover(p, items):
    if not items:
        return None
    want = (p.get("cover") or "").lower()
    for i in items:
        if want and (i["name"].lower() == want or i["stem"] == slugify(pathlib.Path(want).stem, 60)):
            return i
    return items[0]


# ---------------------------------------------------------------- reading a project folder

def project_info(folder):
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
    datekey = "".join(x for x in sort.split("-") if x != "00") if sort else ""
    return {
        "slug": slugify(f"{datekey} {title}"), "title": title, "sort": sort, "date": label,
        "date_src": meta.get("date") or fdate, "location": meta.get("location", ""),
        "client": meta.get("client", ""), "services": meta.get("services", ""),
        "cover": meta.get("cover", ""), "hidden": meta.get("hidden", "").lower() in ("true", "yes", "1"),
        "body": body,
    }


# ---------------------------------------------------------------- stored projects

def load_state():
    """Every published project, read from site/projects/<slug>/meta.json."""
    state = {}
    if OUT.is_dir():
        for d in sorted(OUT.iterdir()):
            mf = d / "meta.json"
            if d.is_dir() and mf.exists():
                try:
                    state[d.name] = json.loads(mf.read_text(encoding="utf-8"))
                except Exception as err:
                    print(f"! {d.name}: meta.json cannot be read ({err})")
    return state


def load_removed():
    try:
        return set(json.loads(REMOVED_FILE.read_text(encoding="utf-8")))
    except Exception:
        return set()


def save_removed(removed):
    OUT.mkdir(parents=True, exist_ok=True)
    REMOVED_FILE.write_text(json.dumps(sorted(removed), ensure_ascii=False, indent=1), encoding="utf-8")


def load_cache():
    try:
        return json.loads(CACHE_FILE.read_text())
    except Exception:
        return {}


def swap(staging, final):
    """Put the finished project in place. The old one is kept until the new one is in."""
    trash = STAGING / (final.name + ".old")
    if trash.exists():
        shutil.rmtree(trash)
    if final.exists():
        final.rename(trash)
    staging.rename(final)
    if trash.exists():
        shutil.rmtree(trash, ignore_errors=True)


KEEP_TEXT = ("title", "sort", "date", "date_src", "location", "client", "services", "cover", "body")


def find_existing(folder, state):
    """A project already on the website that got its photos from a folder with this name."""
    for slug, m in state.items():
        if any(i.get("src") == folder.name and i.get("origin") == "uploads" for i in m.get("items", [])):
            return slug
    return None


def build_project(folder, origin, old, cache, slug=None):
    """Add or update one project from its folder. Returns (meta, number of new photos).
    Raises if something goes wrong; the project on the website is then left as it was."""
    info = project_info(folder)
    slug = slug or info["slug"]
    info["slug"] = slug
    if old:                                             # a folder without project.md keeps the old text
        for k in KEEP_TEXT:
            if not info.get(k) and old.get(k):
                info[k] = old[k]
    final, staging = OUT / slug, STAGING / slug
    STAGING.mkdir(parents=True, exist_ok=True)
    if staging.exists():
        shutil.rmtree(staging)
    img = staging / "img"
    img.mkdir(parents=True)
    try:
        if (final / "img").is_dir():                        # start from the photos already on the site
            shutil.copytree(final / "img", img, dirs_exist_ok=True)
        items = list(old.get("items", [])) if old else []
        have = {i["name"] for i in items}
        used = {i["stem"] for i in items}
        new = 0
        for src in photo_files(folder):
            if src.name in have:
                continue
            stem = unique_stem(src.stem, used)
            used.add(stem)
            full = not src.name.lower().startswith("bts")      # behind-the-scenes photos: no full size
            try:
                got, made = process_photo(src, img, stem, full, cache, f"{slug}/{stem}")
            except Exception as err:  # unreadable or unsupported file
                print(f"   ! skipped {src.name}: {err}")
                continue
            new += made
            items.append({"stem": stem, "name": src.name, "src": folder.name, "origin": origin, **got})
        keep = {f"{i['stem']}{s}.webp" for i in items for s in ("-sm", "", "-full")}
        for f in img.iterdir():
            if f.name not in keep:
                f.unlink()
        meta = {**info, "items": items, "source": {"origin": origin, "name": folder.name}}
        (staging / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    swap(staging, final)
    return meta, new


def move_to_done(folder):
    up = uploads_dir()
    done = up / DONE
    done.mkdir(exist_ok=True)
    target = done / folder.name
    n = 2
    while target.exists():
        target = done / f"{folder.name} ({n})"
        n += 1
    shutil.move(str(folder), str(target), copy_function=shutil.copyfile)
    return target.name


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


def render_site(state):
    """Write every page and data file from the stored projects (not from the source folders)."""
    OUT.mkdir(parents=True, exist_ok=True)
    projects = sorted((p for p in state.values() if not p.get("hidden")),
                      key=lambda p: (p["sort"] or "0000", p["title"].lower()), reverse=True)
    projects = [dict(p, cover_item=pick_cover(p, p["items"])) for p in projects]
    for i, p in enumerate(projects):
        prev = projects[i - 1] if i > 0 else None
        nxt = projects[i + 1] if i + 1 < len(projects) else None
        (OUT / p["slug"] / "index.html").write_text(project_page(p, p["items"], prev, nxt), encoding="utf-8")
    for slug, m in state.items():
        if m.get("hidden") and (OUT / slug / "index.html").exists():
            (OUT / slug / "index.html").unlink()
    (OUT / "index.html").write_text(index_page(projects), encoding="utf-8")

    for d in OUT.iterdir():
        if not d.is_dir() or d.name.startswith("."):
            continue
        if d.name not in state:
            if (d / "meta.json").exists():
                shutil.rmtree(d)
            else:
                print(f"! {d.name}: old page without data, not removed (publish its source folder again to fix)")

    (SITE_DIR / "data").mkdir(exist_ok=True)
    data = [{
        "slug": p["slug"], "url": f"projects/{p['slug']}/", "title": p["title"], "date": p["date"],
        "sort": p["sort"], "location": p["location"], "client": p["client"], "services": p["services"],
        "summary": plain(p["body"], 140), "photos": len(p["items"]),
        "cover": f"projects/{p['slug']}/img/{p['cover_item']['stem']}-sm.webp" if p["cover_item"] else None,
        "cover_md": f"projects/{p['slug']}/img/{p['cover_item']['stem']}.webp" if p["cover_item"] else None,
    } for p in projects]
    (SITE_DIR / "data" / "projects.json").write_text(json.dumps({"items": data}, indent=1, ensure_ascii=False), encoding="utf-8")
    (SITE_DIR / "sitemap.xml").write_text(sitemap(projects), encoding="utf-8")
    return projects


# ---------------------------------------------------------------- publish

def publish():
    print("Watermarking portfolio and Raya photos (new ones only)")
    watermark_site_photos()
    OUT.mkdir(parents=True, exist_ok=True)
    cache = load_cache()
    state = load_state()
    removed = load_removed()

    jobs = []
    for f in subfolders(REPO / "projects"):
        if f.name in removed:
            continue                                    # removed by hand
        try:
            if project_info(f)["slug"] in state:
                continue                                # already on the website
        except Exception as err:
            print(f"! {f.name}: {err}")
            continue
        jobs.append((f, "repo"))
    for f in subfolders(uploads_dir()):
        jobs.append((f, "uploads"))

    print(f"{len(state)} project(s) on the website, {len(jobs)} folder(s) to check")
    problems = []
    for folder, origin in jobs:
        print(f"→ {folder.name}")
        try:
            slug = find_existing(folder, state) if origin == "uploads" else None
            slug = slug or project_info(folder)["slug"]
            meta, new = build_project(folder, origin, state.get(slug), cache, slug=slug)
        except Exception as err:
            problems.append(f"{folder.name}: {err}")
            print(f"   ! FAILED: {err}")
            print("     Left in place. The project on the website is not changed.")
            continue
        state[meta["slug"]] = meta
        print(f" ✓ {meta['title']}  —  {len(meta['items'])} photos{f', {new} new' if new else ''}")
        if 0 < len(meta["items"]) < 10:
            print(f"   note: only {len(meta['items'])} photos (10 or more looks best)")
        if origin == "uploads":
            try:
                done_as = move_to_done(folder)
                for i in meta["items"]:
                    if i.get("src") == folder.name and "done_as" not in i:
                        i["done_as"] = done_as
                (OUT / meta["slug"] / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
            except Exception as err:
                problems.append(f"{folder.name}: published, but could not move to {DONE} ({err})")
                print(f"   ! published, but could not move to {DONE}: {err}")

    refresh_site_photos(state, cache)                  # photos made before the current rule

    cache = {k: v for k, v in cache.items() if k.split("/")[0] in state}
    CACHE_FILE.write_text(json.dumps(cache))
    projects = render_site(state)

    if problems:
        print(f"\n⚠ {len(problems)} problem(s):")
        for p in problems:
            print(f"  - {p}")
    print(f"Done. {len(projects)} project(s) live. Open /projects/ on the website to check.")


# ---------------------------------------------------------------- remove

def write_draft_md(dest, meta):
    mf = dest / "project.md"
    if mf.exists():
        return
    lines = ["---", f"title: {meta['title']}"]
    for key, val in (("date", meta.get("date_src")), ("location", meta.get("location")),
                     ("client", meta.get("client")), ("services", meta.get("services")),
                     ("cover", meta.get("cover"))):
        if val:
            lines.append(f"{key}: {val}")
    lines.append("---")
    mf.write_text("\n".join(lines) + "\n" + (meta.get("body") or "") + "\n", encoding="utf-8")


def remove(slug, stem=None):
    """Remove a whole project (stem=None) or one photo. Originals go to "_<folder name>"
    in the upload folder; project.md keeps the text. Works for projects without photos too."""
    state = load_state()
    removed = load_removed()
    meta = state.get(slug)
    if not meta:
        print(f"! Project '{slug}' is not on the website")
        return 1
    up = uploads_dir()
    if up is None:
        print("! UPLOADS is not set")
        return 1
    targets = [i for i in meta["items"] if stem is None or i["stem"] == stem]
    if stem is not None and not targets:
        print(f"! Photo '{stem}' not found in '{slug}'")
        return 1

    if targets:
        groups = [(i.get("origin", meta["source"]["origin"]), i.get("src", meta["source"]["name"]), i) for i in targets]
    else:                                               # project without photos: only its folder and text
        groups = [(meta["source"]["origin"], meta["source"]["name"], None)]

    for origin, src, item in groups:
        if origin == "uploads":
            base = up / DONE / ((item or {}).get("done_as") or src)
            if not base.is_dir():
                base = up / src
        else:
            base = REPO / "projects" / src
        dest = up / ("_" + src)
        dest.mkdir(exist_ok=True)
        if not (dest / "project.md").exists():
            originals = sorted(base.glob("*.md")) if base.is_dir() else []
            if originals:
                shutil.copyfile(originals[0], dest / "project.md")      # keep the original text as it was
            else:
                write_draft_md(dest, meta)
        if item is not None:
            f = base / item["name"]
            if f.is_file():
                if origin == "uploads":
                    shutil.move(str(f), str(dest / f.name), copy_function=shutil.copyfile)
                else:
                    shutil.copyfile(f, dest / f.name)
                print(f"  moved {f.name} -> {dest.name}/")
            else:
                print(f"  ! original {item['name']} not found (folder {src!r} is gone); website copy removed only")
        if origin == "repo" and stem is None:
            removed.add(src)
        if origin == "uploads" and stem is None and item is None:
            print(f"  note: text saved in {dest.name}/project.md")

    if stem is None:
        shutil.rmtree(OUT / slug, ignore_errors=True)
        state.pop(slug, None)
        print(f"✓ Removed project: {meta['title']}")
    else:
        for s_ in ("-sm", "", "-full"):
            f = OUT / slug / "img" / f"{stem}{s_}.webp"
            if f.exists():
                f.unlink()
        meta["items"] = [i for i in meta["items"] if i["stem"] != stem]
        (OUT / slug / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
        state[slug] = meta
        print(f"✓ Removed photo {stem} from: {meta['title']}")
    save_removed(removed)
    render_site(state)
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) == 2 and args[0] == "--remove-project" and SLUG_RE.match(args[1]):
        sys.exit(remove(args[1]))
    if len(args) == 3 and args[0] == "--remove-photo" and SLUG_RE.match(args[1]) and SLUG_RE.match(args[2]):
        sys.exit(remove(args[1], args[2]))
    if args:
        print("Usage: projects.py | --remove-project SLUG | --remove-photo SLUG STEM")
        sys.exit(2)
    publish()
