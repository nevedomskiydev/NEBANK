#!/usr/bin/env bash
# Build the single delivery archive: nebank.zip (TZ §18).
set -euo pipefail
cd "$(dirname "$0")/.."
OUT="nebank.zip"
rm -f "$OUT"

# Exclude build/dev artifacts; ship source + deploy + docs.
zip -r "$OUT" . \
  -x '*.git*' \
  -x '*/node_modules/*' \
  -x '*/.venv/*' '*/venv/*' \
  -x '*/__pycache__/*' '*.pyc' \
  -x '*/dist/*' '*/build/*' \
  -x '*.zip' \
  -x '*/.pytest_cache/*' \
  -x '*.db' '*.sqlite' \
  -x '*/data/*' >/dev/null

echo "Created $OUT ($(du -h "$OUT" | cut -f1))"
