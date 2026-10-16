#!/bin/bash
# JohorStudio.com: install or update the website on TrueNAS SCALE (24.10 or newer).
# Run as root in the TrueNAS shell:
#   curl -fsSL https://raw.githubusercontent.com/RafieRosliputra/johorstudio-website/main/deploy/setup-truenas.sh -o /tmp/js.sh && bash /tmp/js.sh
# Safe to run again: it keeps what exists and only adds or updates.
set -euo pipefail

POOL=ssd
BASE=/mnt/$POOL/website
REPO=$BASE/repo
UPLOADS=$BASE/uploads
SILEX=$BASE/silex
APP=johorstudio
IMAGE=johorstudio-tools:local
GIT_URL=https://github.com/RafieRosliputra/johorstudio-website.git

say() { printf '\n\033[1;36m== %s\033[0m\n' "$*"; }
[ "$(id -u)" = 0 ] || { echo "Run this as root (sudo -i first)."; exit 1; }
command -v midclt >/dev/null || { echo "This is not TrueNAS SCALE (midclt missing)."; exit 1; }
[ -d /mnt/$POOL ] || { echo "Pool /mnt/$POOL not found."; exit 1; }

mc() { midclt call "$@"; }
dataset() {  # dataset <name> [SMB]
  if [ "$(mc pool.dataset.query "[[\"id\",\"=\",\"$1\"]]" | python3 -c 'import json,sys;print(len(json.load(sys.stdin)))')" = 0 ]; then
    if [ "${2:-}" = SMB ]; then mc pool.dataset.create "{\"name\":\"$1\",\"share_type\":\"SMB\"}" >/dev/null
    else mc pool.dataset.create "{\"name\":\"$1\"}" >/dev/null; fi
    echo "created dataset $1"
  else echo "dataset $1 already exists"; fi
}

say "1/7 Datasets and folders"
dataset $POOL/website
dataset $POOL/website/uploads SMB
mkdir -p "$SILEX/storage" "$SILEX/hosting"

say "2/7 Website files from GitHub"
if [ -d "$REPO/.git" ]; then
  docker run --rm -v "$REPO":/git alpine/git pull --ff-only
else
  docker run --rm -v "$BASE":/git alpine/git clone "$GIT_URL" repo
fi

mkdir -p "$REPO/site/pages"   # pages published from Silex appear at johorstudio.com/pages/

say "3/7 Tools image (publisher + webmaster panel)"
docker build -q -t "$IMAGE" "$REPO/tools"

say "4/7 SMB share 'website-uploads' for project folders"
if [ "$(mc sharing.smb.query '[["name","=","website-uploads"]]' | python3 -c 'import json,sys;print(len(json.load(sys.stdin)))')" = 0 ]; then
  mc sharing.smb.create "{\"path\":\"$UPLOADS\",\"name\":\"website-uploads\",\"comment\":\"JohorStudio.com project folders\"}" >/dev/null && echo "share created"
else echo "share already exists"; fi
mc service.update cifs '{"enable": true}' >/dev/null || true
mc service.start cifs >/dev/null || true

say "5/7 Building the website pages (first time takes 10 to 20 minutes)"
docker run --rm -v "$REPO":/work -v "$UPLOADS":/uploads:ro -e UPLOADS=/uploads "$IMAGE" tools/projects.py

say "6/7 Cloudflare Tunnel token"
TOKEN_FILE=$BASE/.tunnel-token
if [ -s "$TOKEN_FILE" ]; then
  echo "using the token saved earlier ($TOKEN_FILE)"
else
  echo "Paste the Cloudflare Tunnel token (long text starting with eyJ), then press Enter."
  echo "Leave empty and press Enter to skip; the site still works at http://192.168.0.100:8080"
  read -r TOKEN || TOKEN=""
  if [ -n "$TOKEN" ]; then umask 077; printf '%s' "$TOKEN" > "$TOKEN_FILE"; fi
fi
SECRET_FILE=$BASE/.silex-secret
[ -s "$SECRET_FILE" ] || (umask 077; openssl rand -base64 32 | tr -d '\n' > "$SECRET_FILE")

say "7/7 TrueNAS app '$APP'"
python3 - "$REPO/deploy/truenas-app.yaml" "$SECRET_FILE" "$TOKEN_FILE" "$APP" <<'PY'
import json, os, subprocess, sys
yaml_path, secret_file, token_file, app = sys.argv[1:5]
text = open(yaml_path).read()
text = text.replace("CHANGE-to-a-long-random-string", open(secret_file).read().strip())
token = open(token_file).read().strip() if os.path.exists(token_file) else ""
if token:
    text = text.replace("CHANGE-cloudflare-tunnel-token", token)
else:  # no token yet: leave the tunnel service out
    start = text.index("  tunnel:")
    text = text[:start].rstrip() + "\n"
def mc(*args):
    return subprocess.run(["midclt", "call", *args], check=True, capture_output=True, text=True).stdout
exists = json.loads(mc("app.query", json.dumps([["name", "=", app]])))
if exists:
    subprocess.run(["midclt", "call", "-j", "app.update", app,
                    json.dumps({"custom_compose_config_string": text})], check=True)
    print(f"updated app {app}")
else:
    subprocess.run(["midclt", "call", "-j", "app.create",
                    json.dumps({"custom_app": True, "app_name": app, "custom_compose_config_string": text})], check=True)
    print(f"created app {app}")
PY

say "Done"
echo "Website:    http://192.168.0.100:8080"
echo "Webmaster:  http://192.168.0.100:8090"
echo "Silex:      http://192.168.0.100:6805"
echo "Uploads:    smb://192.168.0.100/website-uploads"
echo "The app is listed in TrueNAS under Apps > Installed > $APP"
