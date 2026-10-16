#!/bin/sh
# Publish project folders as project pages.  Usage:  ./publish.sh
set -e
cd "$(dirname "$0")"
docker compose run --rm publish
