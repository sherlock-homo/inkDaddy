#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="${1:-}"
DIST_DIR="${INKDADDY_DIST_DIR:-${ROOT_DIR}/dist/releases}"
FIRMWARE_BOARD="${INKDADDY_FIRMWARE_BOARD:-xiao_mg24}"
FIRMWARE_BINARY="${INKDADDY_FIRMWARE_BINARY:-}"

if [[ -z "$VERSION" ]]; then
  VERSION="$(python3 - "$ROOT_DIR/pyproject.toml" <<'PY'
import re
import sys

text = open(sys.argv[1], encoding="utf-8").read()
match = re.search(r'^version = "([^"]+)"', text, re.MULTILINE)
if not match:
    raise SystemExit("Unable to read project version from pyproject.toml")
print("v" + match.group(1).removeprefix("v"))
PY
)"
fi

mkdir -p "$DIST_DIR"

SOURCE_ARCHIVE="${DIST_DIR}/inkdaddy-${VERSION}.tar.gz"
log() {
  printf '[inkDaddy release] %s\n' "$*"
}

checksum() {
  local file="$1"
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$file" | awk '{print $1}'
  else
    shasum -a 256 "$file" | awk '{print $1}'
  fi
}

log "Building source archive ${SOURCE_ARCHIVE}"
COPYFILE_DISABLE=1 tar \
  --no-xattrs \
  --exclude .git \
  --exclude .venv \
  --exclude dist \
  --exclude hub/frontend/node_modules \
  --exclude hub/frontend/dist \
  --exclude 'hub/*.egg-info' \
  --exclude scripts/__pycache__ \
  -czf "$SOURCE_ARCHIVE" \
  -C "$ROOT_DIR" \
  .

checksum "$SOURCE_ARCHIVE" > "${SOURCE_ARCHIVE}.sha256"

if [[ -n "$FIRMWARE_BINARY" ]]; then
  if [[ ! -f "$FIRMWARE_BINARY" ]]; then
    log "Firmware binary not found: ${FIRMWARE_BINARY}"
    exit 1
  fi
  FIRMWARE_ASSET="${DIST_DIR}/inkdaddy-firmware-${FIRMWARE_BOARD}-${VERSION}.gbl"
  cp "$FIRMWARE_BINARY" "$FIRMWARE_ASSET"
  FIRMWARE_SHA="$(checksum "$FIRMWARE_ASSET")"
  printf '%s\n' "$FIRMWARE_SHA" > "${FIRMWARE_ASSET}.sha256"
  cat > "${DIST_DIR}/inkdaddy-firmware-${FIRMWARE_BOARD}-${VERSION}.json" <<JSON
{
  "board": "${FIRMWARE_BOARD}",
  "version": "${VERSION}",
  "artifact_name": "$(basename "$FIRMWARE_ASSET")",
  "sha256": "${FIRMWARE_SHA}",
  "battery_threshold_percent": 40,
  "requires_external_power": false,
  "min_bootloader_version": null
}
JSON
fi

log "Release assets written to ${DIST_DIR}"
