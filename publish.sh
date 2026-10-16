#!/bin/sh
# Publish project folders as project pages (same as the button on the webmaster panel).
# Usage on TrueNAS:  /mnt/ssd/website/repo/publish.sh
set -e
cd "$(dirname "$0")"
UPLOADS_DIR=${UPLOADS_DIR:-/mnt/ssd/website/uploads}
docker image inspect johorstudio-tools:local >/dev/null 2>&1 || docker build -q -t johorstudio-tools:local tools
docker run --rm -v "$PWD":/work -v "$UPLOADS_DIR":/uploads:ro -e UPLOADS=/uploads johorstudio-tools:local tools/projects.py
