#!/usr/bin/env python3
"""JohorStudio.com webmaster panel (webmaster.johorstudio.com).

A small page with buttons to publish project folders and to update the website
from GitHub, a list of the upload folders, and a link to the Silex editor.
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
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

REPO = pathlib.Path(__file__).resolve().parent.parent
UPLOADS = pathlib.Path(os.environ.get("UPLOADS", "/uploads"))
EMAILS = {e.strip().lower() for e in os.environ.get("ADMIN_EMAILS", "").split(",") if e.strip()}
EDITOR_URL = os.environ.get("EDITOR_URL", "")
PORT = int(os.environ.get("PORT", "8090"))
IMG_EXT = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".heic", ".heif"}

state = {"running": None, "started": None, "finished": None, "ok": None, "log": ""}
lock = threading.Lock()
e = html.escape


def now():
    return datetime.datetime.now().strftime("%d %b %Y, %H:%M:%S")


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
    out = []
    if not UPLOADS.is_dir():
        return out
    for f in sorted(UPLOADS.iterdir()):
        if not f.is_dir() or f.name.startswith((".", "@")):
            continue
        photos = sum(1 for p in f.iterdir() if p.is_file() and p.suffix.lower() in IMG_EXT and not p.name.startswith("."))
        has_md = any(f.glob("*.md"))
        out.append({"name": f.name, "photos": photos, "md": has_md, "draft": f.name.startswith("_")})
    return out


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
.tag{font-size:12px;padding:2px 8px;border-radius:99px;background:var(--soft);color:var(--teal)}.warn{background:#fbecec;color:var(--bad)}
</style></head><body><div class="wrap">
<p class="muted">JohorStudio.com</p><h1>Webmaster</h1>
<p class="muted">Website version: <span id="git">{git}</span></p>

<div class="card"><div class="row">
<button data-job="publish">Publish projects</button>
<button data-job="update" class="btn-line">Update from GitHub and publish</button>
<a class="btn btn-line" href="https://johorstudio.com" target="_blank" rel="noopener">Open website</a>
{editor}
</div>
<p class="muted" style="margin:12px 0 0">Publish: turns the folders below into project posts. Update: gets Claude's latest changes, then publishes.</p></div>

<h2>Status</h2>
<div class="card"><p id="status" class="muted" style="margin:0 0 8px">{status}</p><pre id="log">{log}</pre></div>

<h2>Upload folder</h2>
<p class="muted">Copy project folders into the <b>website-uploads</b> share. Name: <code>20261103 Event name</code>, with photos and a <code>project.md</code>. Folders starting with _ are drafts.</p>
<div class="card"><table><thead><tr><th>Folder</th><th>Photos</th><th></th></tr></thead><tbody>{rows}</tbody></table></div>
</div>
<script>
function poll(){fetch("status").then(r=>r.json()).then(s=>{
 document.getElementById("log").textContent=s.log||"";
 var st=document.getElementById("status");
 st.textContent=s.running?("Running: "+s.running+" (started "+s.started+")"):(s.finished?((s.ok?"Finished ":"Failed ")+s.finished):"Nothing has run yet.");
 document.querySelectorAll("button[data-job]").forEach(b=>b.disabled=!!s.running);
 if(s.git)document.getElementById("git").textContent=s.git;
 if(s.running)setTimeout(poll,1500);});}
document.querySelectorAll("button[data-job]").forEach(b=>b.onclick=function(){
 b.disabled=true;fetch(b.dataset.job,{method:"POST"}).then(()=>setTimeout(poll,400));});
poll();
</script></body></html>"""


def render():
    rows = "".join(
        f"<tr><td>{e(f['name'])}</td><td>{f['photos']}</td><td>"
        + ("<span class='tag'>draft</span> " if f["draft"] else "")
        + ("" if f["md"] else "<span class='tag'>no project.md, using folder name</span>")
        + "</td></tr>" for f in folders()) or "<tr><td colspan='3' class='muted'>No folders yet.</td></tr>"
    editor = f'<a class="btn btn-line" href="{e(EDITOR_URL)}" target="_blank" rel="noopener">Open Silex editor</a>' if EDITOR_URL else ""
    status = "Running: " + state["running"] if state["running"] else "Ready."
    return (PAGE.replace("{git}", e(git_info())).replace("{editor}", editor).replace("{status}", e(status))
            .replace("{log}", e(state["log"])).replace("{rows}", rows))


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
        if self.path.split("?")[0] == "/status":
            return self.send(200, json.dumps({**state, "git": git_info()}), "application/json")
        if self.path.split("?")[0] == "/":
            return self.send(200, render())
        self.send(404, "Not found", "text/plain")

    def do_POST(self):
        if not self.allowed():
            return self.send(403, "Forbidden", "text/plain")
        origin = self.headers.get("Origin") or ""
        host = self.headers.get("Host") or ""
        if origin and re.sub(r"^https?://", "", origin) != host:
            return self.send(403, "Bad origin", "text/plain")
        path = self.path.split("?")[0]
        if path == "/publish":
            started = run_job("Publish projects", [PUBLISH])
        elif path == "/update":
            started = run_job("Update from GitHub and publish", [PULL, PUBLISH])
        else:
            return self.send(404, "Not found", "text/plain")
        self.send(202 if started else 409, json.dumps({"started": started}), "application/json")

    def log_message(self, fmt, *args):
        sys.stderr.write("%s %s\n" % (self.address_string(), fmt % args))


if __name__ == "__main__":
    print(f"Webmaster panel on port {PORT}, uploads: {UPLOADS}, allowed emails: {', '.join(sorted(EMAILS)) or 'none'}")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
