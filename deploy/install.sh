#!/usr/bin/env bash
# NEBANK — one-command clean install for Ubuntu 24.04 (London VPS, 104.194.143.122).
# Cleans the server, installs Docker, builds and starts NEBANK behind auto-HTTPS.
#
# Usage (paste as-is, replace only the token value):
#   BOT_TOKEN='123456:your-token-from-botfather' bash deploy/install.sh
#
set -euo pipefail

cd "$(dirname "$0")/.."
ROOT="$(pwd)"
DOMAIN="104-194-143-122.sslip.io"

say() { printf "\n\033[1;33m==> %s\033[0m\n" "$*"; }

# --- 1. .env -----------------------------------------------------------------
if [ ! -f .env ]; then
  cp .env.example .env
fi
if [ -n "${BOT_TOKEN:-}" ]; then
  # write/replace BOT_TOKEN line in .env
  if grep -q '^BOT_TOKEN=' .env; then
    sed -i "s|^BOT_TOKEN=.*|BOT_TOKEN=${BOT_TOKEN}|" .env
  else
    echo "BOT_TOKEN=${BOT_TOKEN}" >> .env
  fi
fi
if ! grep -q '^BOT_TOKEN=..*' .env; then
  echo "ERROR: BOT_TOKEN is empty. Re-run as:  BOT_TOKEN='your-token' bash deploy/install.sh" >&2
  exit 1
fi

# --- 2. Docker ---------------------------------------------------------------
if ! command -v docker >/dev/null 2>&1; then
  say "Installing Docker"
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -y
  apt-get install -y ca-certificates curl gnupg
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
    > /etc/apt/sources.list.d/docker.list
  apt-get update -y
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  systemctl enable --now docker
fi

# --- 3. Clean the server (free 80/443, remove prior NEBANK) ------------------
say "Cleaning previous services"
systemctl stop nginx apache2 caddy 2>/dev/null || true
systemctl disable nginx apache2 caddy 2>/dev/null || true
docker compose -f "$ROOT/docker-compose.yml" down --remove-orphans 2>/dev/null || true
if [ "${1:-}" = "--wipe" ]; then
  say "Wiping NEBANK volumes (database reset)"
  docker compose -f "$ROOT/docker-compose.yml" down -v 2>/dev/null || true
fi

# --- 4. Build & start --------------------------------------------------------
say "Building and starting NEBANK (this takes a few minutes on first run)"
docker compose -f "$ROOT/docker-compose.yml" up -d --build

# --- 5. Wait for health ------------------------------------------------------
say "Waiting for the app to become healthy"
for i in $(seq 1 60); do
  if docker compose -f "$ROOT/docker-compose.yml" exec -T app curl -fsS http://localhost:8000/healthz >/dev/null 2>&1; then
    break
  fi
  sleep 3
done

say "Done. NEBANK is live."
echo "  Mini App:  https://${DOMAIN}"
echo "  Bot:       https://t.me/nebanknebot"
echo "  Webhook:   set automatically on startup"
echo
echo "  Logs:      docker compose logs -f app"
echo "  Restart:   bash deploy/restart.sh"
echo "  Status:    docker compose ps"
