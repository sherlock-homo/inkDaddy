#!/usr/bin/env bash
set -euo pipefail

DATA_DIR="${INKDADDY_DATA_DIR:-/opt/inkdaddy/data}"
BACKUP_DIR="${INKDADDY_BACKUP_DIR:-${DATA_DIR}/backups}"
INCLUDE_PHOTOS=1

if [[ "${1:-}" == "--metadata-only" ]]; then
  INCLUDE_PHOTOS=0
fi

mkdir -p "$BACKUP_DIR"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
archive="${BACKUP_DIR}/inkdaddy-backup-${stamp}.tar.gz"

args=(--create --gzip --file "$archive" --directory "$DATA_DIR")
paths=(inkdaddy.db secrets.json dashboards frames)
if [[ "$INCLUDE_PHOTOS" == "1" ]]; then
  paths+=(originals processed previews)
fi

tar "${args[@]}" "${paths[@]}" 2>/dev/null || true
printf '%s\n' "$archive"
