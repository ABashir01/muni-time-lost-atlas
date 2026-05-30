#!/bin/sh
set -eu

FLAG_PATH="${MAINTENANCE_FLAG_PATH:-}"

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

ensure_flag_dir
enable_maintenance

if python -m muni_lta_pipeline.rolling_historical_publication bootstrap-window "$@"; then
  disable_maintenance
else
  echo "Bootstrap failed; leaving maintenance mode enabled." >&2
  exit 1
fi
