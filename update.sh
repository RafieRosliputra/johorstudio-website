#!/bin/sh
# Get Claude's latest changes from GitHub, then publish (same as the "Update" button on the webmaster panel).
# Usage on TrueNAS:  /mnt/ssd/website/repo/update.sh
set -e
cd "$(dirname "$0")"
docker run --rm -v "$PWD":/git alpine/git pull --ff-only
docker build -q -t johorstudio-tools:local tools
"$(dirname "$0")/publish.sh"
