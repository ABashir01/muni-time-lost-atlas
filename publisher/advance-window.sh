#!/bin/sh
set -eu

FLAG_PATH="${MAINTENANCE_FLAG_PATH:-}"
PUBLICATION_ROOT="${PUBLICATION_ROOT:-/app/artifacts/publications/b7_rolling_historical_publication}"
LATEST_MANIFEST_PATH="$PUBLICATION_ROOT/latest.json"
CHECK_OUTPUT_FILE="$(mktemp)"

cleanup() {
  rm -f "$CHECK_OUTPUT_FILE"
}

trap cleanup EXIT

ensure_flag_dir() {
  if [ -n "$FLAG_PATH" ]; then
    mkdir -p "$(dirname "$FLAG_PATH")"
  fi
}

enable_maintenance() {
  if [ -n "$FLAG_PATH" ]; then
    : >"$FLAG_PATH"
  fi
}

disable_maintenance() {
  if [ -n "$FLAG_PATH" ]; then
    rm -f "$FLAG_PATH"
  fi
}

python -m muni_lta_pipeline.rolling_historical_publication check-newest-available >"$CHECK_OUTPUT_FILE"

AVAILABLE="$(python - "$CHECK_OUTPUT_FILE" <<'PY'
import json, sys
payload = json.load(open(sys.argv[1], encoding="utf-8"))
print("true" if payload.get("available") else "false")
PY
)"

if [ "$AVAILABLE" != "true" ]; then
  cat "$CHECK_OUTPUT_FILE"
  exit 0
fi

LATEST_AVAILABLE_MONTH="$(python - "$CHECK_OUTPUT_FILE" <<'PY'
import json, sys
payload = json.load(open(sys.argv[1], encoding="utf-8"))
print(payload.get("historic_month", ""))
PY
)"

CURRENT_PUBLISHED_MONTH=""
if [ -f "$LATEST_MANIFEST_PATH" ]; then
  CURRENT_PUBLISHED_MONTH="$(python - "$LATEST_MANIFEST_PATH" <<'PY'
import json, sys
payload = json.load(open(sys.argv[1], encoding="utf-8"))
months = payload.get("publication_months") or []
print(months[-1] if months else "")
PY
)"
fi

if [ -n "$CURRENT_PUBLISHED_MONTH" ] && [ "$CURRENT_PUBLISHED_MONTH" = "$LATEST_AVAILABLE_MONTH" ]; then
  cat "$CHECK_OUTPUT_FILE"
  exit 0
fi

ensure_flag_dir
enable_maintenance

if python -m muni_lta_pipeline.rolling_historical_publication advance-window "$@"; then
  disable_maintenance
else
  echo "Advance failed; leaving maintenance mode enabled." >&2
  exit 1
fi
