#!/usr/bin/env bash
# Rebuild and restart NEBANK after pulling new code (keeps the database).
set -euo pipefail
cd "$(dirname "$0")/.."
docker compose up -d --build
docker compose ps
