#!/bin/sh
# Get Claude's latest changes from GitHub, then rebuild the project pages.  Usage:  ./update.sh
set -e
cd "$(dirname "$0")"
docker run --rm -v "$PWD":/git alpine/git pull
docker compose run --rm publish
