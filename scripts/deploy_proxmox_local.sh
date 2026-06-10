#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROXMOX_HOST="${PROXMOX_HOST:-10.0.0.118}"
PROXMOX_USER="${PROXMOX_USER:-root}"
REMOTE="${PROXMOX_USER}@${PROXMOX_HOST}"
LOCAL_ARCHIVE="${INKDADDY_LOCAL_ARCHIVE_PATH:-/private/tmp/inkdaddy-src.tar.gz}"
REMOTE_ARCHIVE="${INKDADDY_REMOTE_ARCHIVE:-/tmp/inkdaddy-src.tar.gz}"
REMOTE_INSTALLER="${INKDADDY_REMOTE_INSTALLER:-/tmp/inkdaddy-install.sh}"
DRY_RUN="${INKDADDY_DRY_RUN:-0}"
SSH_BATCH_MODE="${INKDADDY_SSH_BATCH_MODE:-yes}"
SSH_KEY="${INKDADDY_SSH_KEY:-$HOME/.ssh/inkdaddy_codex_ed25519}"

SSH_OPTS=(
  -o BatchMode="$SSH_BATCH_MODE"
  -o StrictHostKeyChecking=accept-new
)

if [[ -f "$SSH_KEY" ]]; then
  SSH_OPTS+=(-i "$SSH_KEY" -o IdentitiesOnly=yes)
fi

log() {
  printf '[inkDaddy deploy] %s\n' "$*"
}

log "Packaging ${ROOT_DIR} -> ${LOCAL_ARCHIVE}"
COPYFILE_DISABLE=1 tar \
  --no-xattrs \
  --exclude .git \
  --exclude .venv \
  --exclude hub/frontend/node_modules \
  --exclude hub/frontend/dist \
  --exclude 'hub/*.egg-info' \
  --exclude scripts/__pycache__ \
  -czf "$LOCAL_ARCHIVE" \
  -C "$ROOT_DIR" \
  .

log "Copying archive and installer to ${REMOTE}"
scp "${SSH_OPTS[@]}" "$LOCAL_ARCHIVE" "${REMOTE}:${REMOTE_ARCHIVE}"
scp "${SSH_OPTS[@]}" "${ROOT_DIR}/installer/install.sh" "${REMOTE}:${REMOTE_INSTALLER}"

log "Running installer on ${REMOTE} (INKDADDY_DRY_RUN=${DRY_RUN})"
ssh "${SSH_OPTS[@]}" "$REMOTE" \
  "chmod +x '${REMOTE_INSTALLER}' && INKDADDY_LOCAL_ARCHIVE='${REMOTE_ARCHIVE}' INKDADDY_DRY_RUN='${DRY_RUN}' bash '${REMOTE_INSTALLER}'"

log "Deployment command completed."
