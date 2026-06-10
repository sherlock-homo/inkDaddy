#!/usr/bin/env bash
set -euo pipefail

DATA_DIR="${INKDADDY_DATA_DIR:-/opt/inkdaddy/data}"
archive="${1:-}"

if [[ -z "$archive" || ! -f "$archive" ]]; then
  printf 'Usage: inkdaddy-restore /path/to/backup.tar.gz\n' >&2
  exit 2
fi

systemctl stop inkdaddy-worker.service inkdaddy.service || true
mkdir -p "$DATA_DIR"
tar --extract --gzip --file "$archive" --directory "$DATA_DIR"
systemctl start inkdaddy.service inkdaddy-worker.service
