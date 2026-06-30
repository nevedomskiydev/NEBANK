#!/usr/bin/env bash
# Restart NEBANK (no rebuild). Use after editing .env.
set -euo pipefail
cd "$(dirname "$0")/.."
docker compose restart app caddy
docker compose ps
