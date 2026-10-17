#!/usr/bin/env python3
"""JohorStudio.com webmaster panel (webmaster.johorstudio.com).

A small page with buttons to publish project folders and to update the website
from GitHub, a list of new upload folders (not yet published), the published
projects with buttons to remove a project or a photo, and a link to the Silex editor.
No extra packages needed (Python standard library only).

Protection: put it behind Cloudflare Access. Requests that come through
Cloudflare must carry an Access login whose email is in ADMIN_EMAILS.
Requests straight from the home network (http://192.168.0.100:8090) are allowed.

Environment:
  ADMIN_EMAILS  comma separated emails allowed through Cloudflare Access
  EDITOR_URL    link to Silex, e.g. https://editor.johorstudio.com
  UPLOADS       upload folder inside the container (default /uploads)
  PORT          default 8090
"""
import datetime
import html
import json
import os
import pathlib
import re
import subprocess
import sys
import threading
from urllib.parse import urlparse, parse_qs
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

REPO = pathlib.Path(__file__).resolve().parent.parent
UPLOADS = pathlib.Path(os.environ.get("UPLOADS", "/uploads"))
EMAILS = {e.strip().lower() for e in os.environ.get("ADMIN_EMAILS", "").split(",") if e.strip()}
EDITOR_URL = os.environ.get("EDITOR_URL", "")
PORT = int(os.environ.get("PORT", "8090"))
IMG_EXT = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".heic", ".heif"}
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,80}$")
OUT = REPO / "site" / "projects"

state = {"running": None, "started": None, "finished": None, "ok": None, "log": ""}
lock = threading.Lock()
e = html.escape


KL = datetime.timezone(datetime.timedelta(hours=8))  # Asia/Kuala_Lumpur, no DST


def now():
    return datetime.datetime.now(KL).strftime("%d %b %Y, %H:%M:%S")


def run_job(name, steps):
    def work():
        log = []
        ok = True
        for label, cmd in steps:
            log.append(f"$ {label}")
            state["log"] = "\n".join(log)
            p = subprocess.Popen(cmd, cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                 env={**os.environ, "UPLOADS": str(UPLOADS), "PYTHONUNBUFFERED": "1"})
            for line in p.stdout:
                log.append(line.rstrip())
                state["log"] = "\n".join(log[-400:])
            if p.wait() != 0:
                ok = False
                log.append(f"!! {label} failed (exit {p.returncode})")
                break
        state.update(running=None, finished=now(), ok=ok, log="\n".join(log[-400:]))
        lock.release()

    if not lock.acquire(blocking=False):
        return False
    state.update(running=name, started=now(), finished=None, ok=None, log="")
    threading.Thread(target=work, daemon=True).start()
    return True


PUBLISH = ("Publish projects", [sys.executable, "tools/projects.py"])
PULL = ("Get latest version from GitHub", ["git", "pull", "--ff-only"])


def folders():
    """New project folders in the root of the upload share (not yet published).
    Folders starting with _ (drafts, _DONE) and hidden folders are left out."""
    out = []
    if not UPLOADS.is_dir():
        return out
    for f in sorted(UPLOADS.iterdir()):
        if not f.is_dir() or f.name.startswith((".", "@", "_")):
            continue
        photos = sum(1 for p in f.iterdir() if p.is_file() and p.suffix.lower() in IMG_EXT and not p.name.startswith("."))
        out.append({"name": f.name, "photos": photos, "md": any(f.glob("*.md"))})
    return out


def published():
    """Projects on the website, newest first, with their photos (from site/projects/<slug>/meta.json)."""
    out = []
    if not OUT.is_dir():
        return out
    for d in OUT.iterdir():
        mf = d / "meta.json"
        if not (d.is_dir() and mf.exists()):
            continue
        try:
            m = json.loads(mf.read_text(encoding="utf-8"))
        except Exception:
            continue
        out.append({"slug": d.name, "title": m.get("title", d.name), "date": m.get("date", ""),
                    "sort": m.get("sort", ""), "hidden": bool(m.get("hidden")),
                    "photos": [{"stem": i["stem"], "name": i["name"]} for i in m.get("items", [])]})
    return sorted(out, key=lambda p: (p["sort"] or "0000", p["title"].lower()), reverse=True)


def git_info():
    try:
        r = subprocess.run(["git", "log", "-1", "--format=%h · %cd · %s", "--date=format:%d %b %Y %H:%M"],
                           cwd=REPO, capture_output=True, text=True, timeout=10)
        return r.stdout.strip() or r.stderr.strip()
    except Exception as err:
        return str(err)


PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Webmaster | JohorStudio.com</title>
<meta name="robots" content="noindex">
<style>
:root{--ink:#1f2629;--muted:#5f6b70;--line:#dde3e5;--bg:#f4f6f6;--teal:#1f6f68;--soft:#dff1ee;--bad:#a33}
*{box-sizing:border-box}body{margin:0;font:16px/1.5 system-ui,-apple-system,Segoe UI,sans-serif;color:var(--ink);background:var(--bg)}
.wrap{max-width:900px;margin:0 auto;padding:24px 16px 64px}h1{font-size:28px;margin:8px 0 4px}h2{font-size:19px;margin:32px 0 10px}
.muted{color:var(--muted)}.card{background:#fff;border:1px solid var(--line);border-radius:8px;padding:16px 18px;margin:12px 0}
.row{display:flex;flex-wrap:wrap;gap:10px;align-items:center}
button,.btn{font:600 15px system-ui,sans-serif;border:0;border-radius:6px;padding:11px 16px;background:var(--teal);color:#fff;cursor:pointer;text-decoration:none;display:inline-block}
.btn-line{background:#fff;color:var(--teal);border:1px solid var(--teal)}button[disabled]{opacity:.5;cursor:wait}
pre{background:#14191b;color:#d6e2e0;padding:14px;border-radius:8px;max-height:420px;overflow:auto;font-size:13px;white-space:pre-wrap}
table{width:100%;border-collapse:collapse;font-size:15px}td,th{text-align:left;padding:8px 6px;border-bottom:1px solid var(--line)}
.photo-list{margin:6px 0 0 0;padding:0;list-style:none}.photo-list li{display:flex;justify-content:space-between;gap:10px;padding:4px 0;border-bottom:1px solid var(--line);font-size:14px}
.btn-danger{background:#fff;color:var(--bad);border:1px solid var(--bad);padding:6px 10px;font-size:13px}
.tag{font-size:12px;padding:2px 8px;border-radius:99px;background:var(--soft);color:var(--teal)}.warn{background:#fbecec;color:var(--bad)}
</style></head><body><div class="wrap">
<p class="muted">JohorStudio.com</p><h1>Webmaster</h1>
<p class="muted">Website version: <span id="git">{git}</span></p>

<div class="card"><div class="row">
<button data-job="publish">Publish projects</button>
<button data-job="update" class="btn-line">Update from GitHub and publish</button>
<a class="btn btn-line" href="https://johorstudio.com" target="_blank" rel="noopener">Open website</a>
{editor}
<a class="btn btn-line" href="guide">Guide &amp; commands</a>
<a class="btn btn-line" href="handover">Handover guide</a>
</div>
<p class="muted" style="margin:12px 0 0">Publish: adds the new folders below to the website, then moves each one into <b>_DONE</b>. Update: gets Claude's latest changes, then publishes.</p></div>

<h2>Status</h2>
<div class="card"><p id="status" class="muted" style="margin:0 0 8px">{status}</p><pre id="log">{log}</pre></div>

<h2>New folders</h2>
<p class="muted">Folders in the root of <b>website-uploads</b> that are not published yet. Name: <code>20261103 Event name</code>, with photos and a <code>project.md</code>. After Publish they move to <b>_DONE</b>, and you can delete them there.</p>
<div class="card"><table><thead><tr><th>Folder</th><th>Photos</th><th></th></tr></thead><tbody>{rows}</tbody></table></div>

<h2>On the website</h2>
<p class="muted">Remove a project, or one photo from it. The photos and <code>project.md</code> are moved into a folder named <code>_Folder name</code> in <b>website-uploads</b>.</p>
<div class="card">{published}</div>
</div>
<script>
var wasRunning=false;
function poll(){fetch("status").then(r=>r.json()).then(s=>{
 document.getElementById("log").textContent=s.log||"";
 var st=document.getElementById("status");
 st.textContent=s.running?("Running: "+s.running+" (started "+s.started+")"):(s.finished?((s.ok?"Finished ":"Failed ")+s.finished):"Nothing has run yet.");
 document.querySelectorAll("button[data-job],button[data-post]").forEach(b=>b.disabled=!!s.running);
 if(s.git)document.getElementById("git").textContent=s.git;
 if(s.running){wasRunning=true;setTimeout(poll,1500);}
 else if(wasRunning){wasRunning=false;location.reload();}});}
document.querySelectorAll("button[data-job]").forEach(b=>b.onclick=function(){
 b.disabled=true;fetch(b.dataset.job,{method:"POST"}).then(()=>setTimeout(poll,400));});
document.querySelectorAll("button[data-post]").forEach(b=>b.onclick=function(){
 if(!confirm(b.dataset.msg))return;
 b.disabled=true;fetch(b.dataset.post,{method:"POST"}).then(()=>setTimeout(poll,400));});
poll();
</script></body></html>"""


def render_published():
    items = published()
    if not items:
        return "<p class='muted'>Nothing published yet.</p>"
    parts = []
    for p in items:
        label = e(p["title"]) + (f" <span class='tag'>hidden</span>" if p["hidden"] else "")
        photos = "".join(
            f"<li><span>{e(x['name'])}</span>"
            f"<button class='btn-danger' data-post='remove-photo?slug={e(p['slug'])}&amp;stem={e(x['stem'])}' "
            f"data-msg='Remove this photo from {e(p['title'])}? The original goes to _{e(p['slug'])} in website-uploads.'>Remove photo</button></li>"
            for x in p["photos"])
        parts.append(
            f"<div style='padding:10px 0;border-bottom:1px solid var(--line)'>"
            f"<div class='row' style='justify-content:space-between'><div><b>{label}</b><div class='muted' style='font-size:14px'>"
            f"{e(p['date'])} · {len(p['photos'])} photos</div></div>"
            f"<button class='btn-danger' data-post='remove-project?slug={e(p['slug'])}' "
            f"data-msg='Remove the whole project {e(p['title'])} from the website? Photos and project.md go to _ folder in website-uploads.'>Remove project</button></div>"
            f"<details><summary class='muted' style='font-size:14px;cursor:pointer'>Photos</summary>"
            f"<ul class='photo-list'>{photos or '<li class=muted>No photos</li>'}</ul></details></div>")
    return "".join(parts)


def render():
    rows = "".join(
        f"<tr><td>{e(f['name'])}</td><td>{f['photos']}</td><td>"
        + ("" if f["md"] else "<span class='tag'>no project.md, using folder name</span>")
        + "</td></tr>" for f in folders()) or "<tr><td colspan='3' class='muted'>No new folders.</td></tr>"
    editor = f'<a class="btn btn-line" href="{e(EDITOR_URL)}" target="_blank" rel="noopener">Open Silex editor</a>' if EDITOR_URL else ""
    status = "Running: " + state["running"] if state["running"] else "Ready."
    return (PAGE.replace("{git}", e(git_info())).replace("{editor}", editor).replace("{status}", e(status))
            .replace("{log}", e(state["log"])).replace("{rows}", rows).replace("{published}", render_published()))


GUIDE = [
    {"title": "Check website snapshots", "where": "TrueNAS Shell",
     "cmd": "zfs list -t snapshot -r ssd/website",
     "explain": "Lists the website snapshots. Names like ssd/website@webauto-... are website snapshots. If you see ssd/website/uploads@..., that did not come from this script, so it can be deleted.",
     "run": None},
    {"title": "Take a snapshot now", "where": "TrueNAS Shell",
     "cmd": "/mnt/ssd/scripts/snap-website.sh",
     "explain": "The script only takes a new snapshot if 14 days have passed since the last one. Once the new snapshot is verified, it deletes the older ones and keeps the 2 newest. Usually you don't need to run it manually, because the cron job runs it every day at 03:00.",
     "run": None},
    {"title": "Check visitors (Umami)", "where": "Browser: ana.johorstudio.com (login)",
     "cmd": "https://ana.johorstudio.com",
     "explain": "Opens the Umami analytics dashboard. It shows visitors, page views and button clicks: WhatsApp, booking, email, phone and enquiry form submissions. Change the admin password if you have not done so yet.",
     "run": None},
    {"title": "Umami snapshot cron job", "where": "TrueNAS web UI: System, Advanced Settings, Cron Jobs (name: snapshot umami)",
     "cmd": "Command: /mnt/ssd/scripts/snap-umami.sh | Run as: root | Daily 03:30 AM",
     "explain": "Takes a daily snapshot of the Umami data (ssd/umami) and keeps the 7 newest. Check here if you want to change the time or disable it.",
     "run": None},
    {"title": "Snapshot cron job", "where": "TrueNAS web UI: System, Advanced Settings, Cron Jobs",
     "cmd": "Command: /mnt/ssd/scripts/snap-website.sh | Run as: root | Daily 03:00 AM",
     "explain": "The setting that runs the snapshot script every day. Check here if you want to change the time or disable it.",
     "run": None},
    {"title": "Full backup (tar)", "where": "TrueNAS Shell",
     "cmd": "cd /mnt/ssd/website && tar czf /mnt/ssd/website-backup-$(date +%F-%H%M).tar.gz repo uploads silex",
     "explain": "A full copy of repo, uploads and silex in one file. It is slow and large. Use it before big changes, and keep a copy outside TrueNAS.",
     "run": None},
    {"title": "Delete old tar backups", "where": "TrueNAS Shell",
     "cmd": "rm -f /mnt/ssd/website-backup-*.tar.gz",
     "explain": "Deletes all tar backup files. This cannot be undone. Only do it after you have confirmed a copy outside TrueNAS.",
     "run": None},
    {"title": "Delete one snapshot", "where": "TrueNAS Shell",
     "cmd": "zfs destroy ssd/website@NAME_OF_SNAPSHOT",
     "explain": "Deletes one snapshot. Replace NAME_OF_SNAPSHOT with the real name from the list. Never delete the newest snapshot.",
     "run": None},
    {"title": "Check repo status", "where": "Webmaster (Run)",
     "cmd": "git -C /work status -sb",
     "explain": "Shows the branch and any changed files. If there are changed files outside site/, do not press Update yet.",
     "run": ["git", "-C", "/work", "status", "-sb"]},
    {"title": "Latest commits", "where": "Webmaster (Run)",
     "cmd": "git -C /work log --oneline -3",
     "explain": "The three latest commits in the repo on TrueNAS.",
     "run": ["git", "-C", "/work", "log", "--oneline", "-3"]},
    {"title": "Website size", "where": "Webmaster (Run)",
     "cmd": "du -sh --apparent-size /work/site /work/projects /work/media /work/.git /uploads",
     "explain": "Size of each part of the website. Compare these numbers after an Update.",
     "run": ["du", "-sh", "--apparent-size", "/work/site", "/work/projects", "/work/media", "/work/.git", "/uploads"]},
    {"title": "Contents of website-uploads", "where": "Webmaster (Run)",
     "cmd": "ls -A /uploads",
     "explain": "Lists the folders in website-uploads. Folders starting with _ are removed project originals, plus _DONE.",
     "run": ["ls", "-A", "/uploads"]},
    {"section": "For later", "title": "Check disk space", "where": "TrueNAS Shell",
     "cmd": "df -h /mnt/ssd && zfs list -o name,used,avail ssd/website",
     "explain": "Shows free space on the ssd pool and how much the website uses.",
     "run": None},
    {"section": "For later", "title": "List snapshots in the folder", "where": "TrueNAS Shell",
     "cmd": "ls /mnt/ssd/website/.zfs/snapshot/",
     "explain": "Lists the snapshot names for the website. Use this folder to pick a file from an old snapshot.",
     "run": None},
    {"section": "For later", "title": "Restore one file from a snapshot", "where": "TrueNAS Shell",
     "cmd": "cp -a /mnt/ssd/website/.zfs/snapshot/NAME_OF_SNAPSHOT/ITEM /mnt/ssd/website/ITEM",
     "explain": "Takes one file or folder from an old snapshot without rolling back the whole website. Replace NAME_OF_SNAPSHOT and ITEM with real names (example: repo/site/index.html). Check the paths before pressing Enter.",
     "run": None},
    {"section": "For later", "title": "Check a tar backup can be read", "where": "TrueNAS Shell",
     "cmd": "tar tzf /mnt/ssd/website-backup-NAME.tar.gz | head -20",
     "explain": "Makes sure the tar backup is not corrupted by listing its first contents. Run this before deleting old backups.",
     "run": None},
    {"section": "For later", "title": "Roll back the whole website (emergency only)", "where": "TrueNAS Shell",
     "cmd": "zfs rollback ssd/website@NAME_OF_SNAPSHOT",
     "explain": "Returns the whole website folder to the snapshot state. Every change after that snapshot is lost. Use only in an emergency, and only after you have made a fresh copy.",
     "run": None},
    {"section": "For later", "title": "Restart webmaster", "where": "TrueNAS web UI: Apps, webmaster",
     "cmd": "Apps → webmaster → Restart",
     "explain": "Needed after admin.py changes on GitHub, so the new code is loaded. A restart does not delete anything.",
     "run": None},
]

GUIDE_PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Guide | Webmaster</title>
<meta name="robots" content="noindex">
<style>
:root{--ink:#1f2629;--muted:#5f6b70;--line:#dde3e5;--bg:#f4f6f6;--teal:#1f6f68}
*{box-sizing:border-box}body{margin:0;font:16px/1.5 system-ui,-apple-system,Segoe UI,sans-serif;color:var(--ink);background:var(--bg)}
.wrap{max-width:900px;margin:0 auto;padding:24px 16px 64px}h1{font-size:28px;margin:8px 0 4px}
.muted{color:var(--muted);font-size:14px}.card{background:#fff;border:1px solid var(--line);border-radius:8px;padding:14px 16px;margin:12px 0}
.row{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
button{font:600 14px system-ui,sans-serif;border:0;border-radius:6px;padding:9px 14px;background:var(--teal);color:#fff;cursor:pointer}
.btn-line{background:#fff;color:var(--teal);border:1px solid var(--teal)}
pre{background:#14191b;color:#d6e2e0;padding:12px;border-radius:8px;overflow:auto;font-size:13px;white-space:pre-wrap;word-break:break-all}
a{color:var(--teal)}
</style></head><body><div class="wrap">
<p class="muted"><a href="./">&larr; Back to Webmaster</a></p><h1>Guide &amp; commands</h1>
<p class="muted">Press <b>Explain</b> to read what a command does. <b>Run</b> runs read-only checks directly from the webmaster. For TrueNAS Shell commands, press <b>Copy → TrueNAS Shell</b>, then paste into the TrueNAS Shell.</p>
{cards}
</div><script>
document.querySelectorAll("[data-explain]").forEach(function(b){b.onclick=function(){var d=document.getElementById("ex-"+b.dataset.explain);d.hidden=!d.hidden;};});
document.querySelectorAll("[data-run]").forEach(function(b){b.onclick=function(){var id=b.dataset.run;document.getElementById("ex-"+id).hidden=false;var o=document.getElementById("out-"+id);o.hidden=false;o.textContent="Running...";
 fetch("run?id="+id).then(function(r){return r.json();}).then(function(j){o.textContent=j.output;}).catch(function(){o.textContent="Failed";});};});
document.querySelectorAll("[data-copy]").forEach(function(b){b.onclick=function(){navigator.clipboard.writeText(b.dataset.copy).then(function(){b.textContent="Copied";});};});
</script></body></html>"""


def render_guide():
    cards, section = [], None
    for i, g in enumerate(GUIDE):
        gid = f"g{i}"
        if g.get("section", "Now") != section:
            section = g.get("section", "Now")
            cards.append(f"<h2 style='font-size:19px;margin:28px 0 4px'>{e(section)}</h2>")
        if g["run"]:
            action = f"<button data-run='{gid}'>Run</button>"
        elif g["where"].startswith("TrueNAS Shell"):
            action = f"<button class='btn-line' data-copy='{e(g['cmd'])}'>Copy → TrueNAS Shell</button>"
        else:
            action = ""
        cards.append(
            f"<div class='card'><div class='row' style='justify-content:space-between'>"
            f"<div><b>{e(g['title'])}</b><div class='muted'>Where: {e(g['where'])}</div></div>"
            f"<div class='row'><button class='btn-line' data-explain='{gid}'>Explain</button>{action}</div></div>"
            f"<div id='ex-{gid}' hidden style='margin-top:10px'><p style='margin:0 0 8px'>{e(g['explain'])}</p>"
            f"<pre>{e(g['cmd'])}</pre><pre id='out-{gid}' hidden></pre></div></div>")
    return GUIDE_PAGE.replace("{cards}", "".join(cards))


class Handler(BaseHTTPRequestHandler):
    server_version = "webmaster"

    def allowed(self):
        if "cf-connecting-ip" not in {k.lower() for k in self.headers.keys()}:
            return True                                   # straight from the home network
        email = (self.headers.get("Cf-Access-Authenticated-User-Email") or "").lower()
        return bool(email) and email in EMAILS

    def send(self, code, body, ctype="text/html; charset=utf-8"):
        data = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Frame-Options", "DENY")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if not self.allowed():
            return self.send(403, "Forbidden", "text/plain")
        url = urlparse(self.path)
        if url.path == "/status":
            return self.send(200, json.dumps({**state, "git": git_info()}), "application/json")
        if url.path == "/":
            return self.send(200, render())
        if url.path == "/guide":
            return self.send(200, render_guide())
        if url.path == "/handover":
            return self.send(200, (REPO / "tools" / "handover.html").read_text(encoding="utf-8"))
        if url.path == "/run":
            gid = (parse_qs(url.query).get("id") or [""])[0]
            idx = int(gid[1:]) if gid[:1] == "g" and gid[1:].isdigit() else -1
            if not 0 <= idx < len(GUIDE) or not GUIDE[idx]["run"]:
                return self.send(404, "Not found", "text/plain")
            try:
                r = subprocess.run(GUIDE[idx]["run"], cwd=REPO, capture_output=True, text=True, timeout=120)
                out = (r.stdout + r.stderr).strip() or "(tiada output)"
            except Exception as err:
                out = str(err)
            return self.send(200, json.dumps({"output": out}), "application/json")
        self.send(404, "Not found", "text/plain")

    def do_POST(self):
        if not self.allowed():
            return self.send(403, "Forbidden", "text/plain")
        origin = self.headers.get("Origin") or ""
        host = self.headers.get("Host") or ""
        if origin and re.sub(r"^https?://", "", origin) != host:
            return self.send(403, "Bad origin", "text/plain")
        url = urlparse(self.path)
        path, qs = url.path, parse_qs(url.query)
        slug = (qs.get("slug") or [""])[0]
        stem = (qs.get("stem") or [""])[0]
        if path == "/publish":
            started = run_job("Publish projects", [PUBLISH])
        elif path == "/update":
            started = run_job("Update from GitHub and publish", [PULL, PUBLISH])
        elif path == "/remove-project" and SLUG_RE.match(slug):
            started = run_job(f"Remove project {slug}", [(f"remove {slug}", [sys.executable, "tools/projects.py", "--remove-project", slug])])
        elif path == "/remove-photo" and SLUG_RE.match(slug) and SLUG_RE.match(stem):
            started = run_job(f"Remove photo {stem} from {slug}",
                              [(f"remove {stem} from {slug}", [sys.executable, "tools/projects.py", "--remove-photo", slug, stem])])
        elif path in ("/remove-project", "/remove-photo"):
            return self.send(400, "Bad request", "text/plain")
        else:
            return self.send(404, "Not found", "text/plain")
        self.send(202 if started else 409, json.dumps({"started": started}), "application/json")

    def log_message(self, fmt, *args):
        sys.stderr.write("%s %s\n" % (self.address_string(), fmt % args))


if __name__ == "__main__":
    print(f"Webmaster panel on port {PORT}, uploads: {UPLOADS}, allowed emails: {', '.join(sorted(EMAILS)) or 'none'}")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
