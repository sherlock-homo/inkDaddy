#!/usr/bin/env bash
set -euo pipefail

APP_NAME="${INKDADDY_APP_NAME:-inkdaddy}"
CT_HOSTNAME="${INKDADDY_HOSTNAME:-inkdaddy}"
CT_ID="${INKDADDY_CT_ID:-}"
STORAGE="${INKDADDY_STORAGE:-local-lvm}"
TEMPLATE_STORAGE="${INKDADDY_TEMPLATE_STORAGE:-local}"
ROOTFS_SIZE_RAW="${INKDADDY_ROOTFS_SIZE:-12G}"
ROOTFS_SIZE="${ROOTFS_SIZE_RAW%G}"
ROOTFS_SIZE="${ROOTFS_SIZE%g}"
MEMORY_MB="${INKDADDY_MEMORY_MB:-2048}"
CORES="${INKDADDY_CORES:-2}"
BRIDGE="${INKDADDY_BRIDGE:-vmbr0}"
DEBIAN_TEMPLATE="${INKDADDY_TEMPLATE:-debian-12-standard_12.12-1_amd64.tar.zst}"
REPO_URL="${INKDADDY_REPO:-https://github.com/OWNER/inkDaddy.git}"
VERSION="${INKDADDY_VERSION:-main}"
LOCAL_ARCHIVE="${INKDADDY_LOCAL_ARCHIVE:-}"
DRY_RUN="${INKDADDY_DRY_RUN:-0}"
AUTO_UPDATE="${INKDADDY_AUTO_UPDATE:-1}"
UPDATE_ALLOW_APPLY="${INKDADDY_UPDATE_ALLOW_APPLY:-1}"
UPDATE_CHECK_INTERVAL_SECONDS="${INKDADDY_UPDATE_CHECK_INTERVAL_SECONDS:-3600}"

log() {
  printf '[inkDaddy] %s\n' "$*"
}

run() {
  log "$*"
  if [[ "$DRY_RUN" != "1" ]]; then
    "$@"
  fi
}

need_root() {
  if [[ "${EUID}" -ne 0 ]]; then
    if [[ "$DRY_RUN" == "1" ]]; then
      log "Dry run: continuing without root because no host changes will be made."
      return
    fi
    log "Run this installer as root on a Proxmox VE host."
    exit 1
  fi
}

choose_ct_id() {
  if [[ -n "$CT_ID" ]]; then
    printf '%s\n' "$CT_ID"
    return
  fi
  if command -v pct >/dev/null 2>&1; then
    local existing
    existing="$(pct list | awk -v name="$CT_HOSTNAME" 'NR > 1 && $NF == name { print $1; exit }')"
    if [[ -n "$existing" ]]; then
      printf '%s\n' "$existing"
      return
    fi
  fi
  if [[ "$DRY_RUN" == "1" ]] && ! command -v pvesh >/dev/null 2>&1; then
    printf '999\n'
    return
  fi
  pvesh get /cluster/nextid
}

ensure_template() {
  if [[ "$DRY_RUN" == "1" ]]; then
    log "Dry run: would ensure Debian template ${DEBIAN_TEMPLATE} exists on ${TEMPLATE_STORAGE}."
    return
  fi
  if ! pveam list "$TEMPLATE_STORAGE" | grep -q "$DEBIAN_TEMPLATE"; then
    run pveam update
    run pveam download "$TEMPLATE_STORAGE" "$DEBIAN_TEMPLATE"
  fi
}

create_container() {
  local id="$1"
  local template="${TEMPLATE_STORAGE}:vztmpl/${DEBIAN_TEMPLATE}"
  if [[ "$DRY_RUN" == "1" ]]; then
    log "Dry run: would create or reuse LXC ${id} (${CT_HOSTNAME})."
    return
  fi
  if pct status "$id" >/dev/null 2>&1; then
    log "Container $id already exists; leaving it in place for non-destructive reinstall/update."
    return
  fi
  run pct create "$id" "$template" \
    --hostname "$CT_HOSTNAME" \
    --unprivileged 1 \
    --cores "$CORES" \
    --memory "$MEMORY_MB" \
    --rootfs "${STORAGE}:${ROOTFS_SIZE}" \
    --net0 "name=eth0,bridge=${BRIDGE},ip=dhcp" \
    --features nesting=0 \
    --onboot 1 \
    --start 1
}

ensure_container_started() {
  local id="$1"
  if [[ "$DRY_RUN" == "1" ]]; then
    log "Dry run: would ensure LXC ${id} is running."
    return
  fi
  if ! pct status "$id" | grep -q "status: running"; then
    run pct start "$id"
  fi
}

derive_github_repo() {
  local raw="${INKDADDY_GITHUB_REPO:-$REPO_URL}"
  raw="${raw%.git}"
  raw="${raw#git@github.com:}"
  raw="${raw#https://github.com/}"
  raw="${raw#http://github.com/}"
  raw="${raw#/}"
  raw="${raw%/}"
  if [[ "$raw" == OWNER/* || "$raw" != */* ]]; then
    return 0
  fi
  printf '%s\n' "$raw"
}

install_source_from_archive() {
  local id="$1"
  if [[ ! -f "$LOCAL_ARCHIVE" ]]; then
    log "INKDADDY_LOCAL_ARCHIVE does not exist: ${LOCAL_ARCHIVE}"
    exit 1
  fi
  run pct exec "$id" -- bash -lc "mkdir -p /opt/inkdaddy /opt/inkdaddy/data /opt/inkdaddy/bin"
  run pct exec "$id" -- bash -lc "rm -rf /opt/inkdaddy/src.new && mkdir -p /opt/inkdaddy/src.new"
  run pct push "$id" "$LOCAL_ARCHIVE" /tmp/inkdaddy-src.tar.gz
  run pct exec "$id" -- bash -lc "tar -xzf /tmp/inkdaddy-src.tar.gz -C /opt/inkdaddy/src.new && test -f /opt/inkdaddy/src.new/pyproject.toml"
  run pct exec "$id" -- bash -lc "rm -rf /opt/inkdaddy/src.prev && if [ -d /opt/inkdaddy/src ]; then mv /opt/inkdaddy/src /opt/inkdaddy/src.prev; fi && mv /opt/inkdaddy/src.new /opt/inkdaddy/src"
}

install_source_from_git() {
  local id="$1"
  run pct exec "$id" -- bash -lc "mkdir -p /opt/inkdaddy/src /opt/inkdaddy/data /opt/inkdaddy/bin"
  run pct exec "$id" -- bash -lc "if [ ! -d /opt/inkdaddy/src/.git ]; then git clone ${REPO_URL} /opt/inkdaddy/src; fi"
  run pct exec "$id" -- bash -lc "cd /opt/inkdaddy/src && git fetch --all --tags && git checkout ${VERSION}"
}

install_inside_container() {
  local id="$1"
  local github_repo
  github_repo="$(derive_github_repo)"
  run pct exec "$id" -- bash -lc "apt-get update && apt-get install -y git curl ca-certificates python3 python3-venv python3-pip python3-dev build-essential libjpeg-dev zlib1g-dev nodejs npm avahi-daemon nginx"
  if [[ -n "$LOCAL_ARCHIVE" ]]; then
    install_source_from_archive "$id"
  else
    install_source_from_git "$id"
  fi
  run pct exec "$id" -- bash -lc "cd /opt/inkdaddy/src && python3 -m venv /opt/inkdaddy/venv && /opt/inkdaddy/venv/bin/pip install --upgrade pip && /opt/inkdaddy/venv/bin/pip install -e ."
  run pct exec "$id" -- bash -lc "cd /opt/inkdaddy/src/hub/frontend && npm ci && npm run build"
  run pct exec "$id" -- bash -lc "install -m 0755 /opt/inkdaddy/src/installer/update.sh /opt/inkdaddy/bin/inkdaddy-update"
  run pct exec "$id" -- bash -lc "install -m 0755 /opt/inkdaddy/src/installer/backup.sh /opt/inkdaddy/bin/inkdaddy-backup"
  run pct exec "$id" -- bash -lc "install -m 0755 /opt/inkdaddy/src/installer/restore.sh /opt/inkdaddy/bin/inkdaddy-restore"
  run pct exec "$id" -- bash -lc "install -m 0755 /opt/inkdaddy/src/installer/uninstall.sh /opt/inkdaddy/bin/inkdaddy-uninstall"
  run pct exec "$id" -- bash -lc "mkdir -p /opt/inkdaddy/config && cat >/opt/inkdaddy/config/inkdaddy.env <<ENV
INKDADDY_DATA_DIR=/opt/inkdaddy/data
INKDADDY_REPO=${REPO_URL}
INKDADDY_GITHUB_REPO=${github_repo}
INKDADDY_AUTO_UPDATE=${AUTO_UPDATE}
INKDADDY_UPDATE_ALLOW_APPLY=${UPDATE_ALLOW_APPLY}
INKDADDY_UPDATE_CHECK_INTERVAL_SECONDS=${UPDATE_CHECK_INTERVAL_SECONDS}
INKDADDY_UPDATE_COMMAND=/opt/inkdaddy/bin/inkdaddy-update
ENV
chmod 0600 /opt/inkdaddy/config/inkdaddy.env"
  run pct exec "$id" -- bash -lc "cat >/etc/systemd/system/inkdaddy.service <<'UNIT'
[Unit]
Description=inkDaddy hub
After=network-online.target
Wants=network-online.target

[Service]
EnvironmentFile=-/opt/inkdaddy/config/inkdaddy.env
WorkingDirectory=/opt/inkdaddy/src
ExecStart=/opt/inkdaddy/venv/bin/uvicorn inkdaddy_hub.main:app --app-dir hub --host 127.0.0.1 --port 8080
Restart=on-failure
User=root

[Install]
WantedBy=multi-user.target
UNIT"
  run pct exec "$id" -- bash -lc "cat >/etc/systemd/system/inkdaddy-worker.service <<'UNIT'
[Unit]
Description=inkDaddy worker
After=network-online.target inkdaddy.service

[Service]
EnvironmentFile=-/opt/inkdaddy/config/inkdaddy.env
WorkingDirectory=/opt/inkdaddy/src
ExecStart=/opt/inkdaddy/venv/bin/python -m inkdaddy_hub.worker
Restart=on-failure
User=root

[Install]
WantedBy=multi-user.target
UNIT"
  run pct exec "$id" -- bash -lc "cat >/etc/nginx/sites-available/inkdaddy <<'NGINX'
server {
  listen 80 default_server;
  server_name inkdaddy.local _;
  client_max_body_size 128m;
  location / {
    proxy_pass http://127.0.0.1:8080;
    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;
  }
}
NGINX
ln -sf /etc/nginx/sites-available/inkdaddy /etc/nginx/sites-enabled/inkdaddy
rm -f /etc/nginx/sites-enabled/default"
  run pct exec "$id" -- bash -lc "cat >/etc/avahi/services/inkdaddy.service <<'AVAHI'
<?xml version=\"1.0\" standalone='no'?>
<!DOCTYPE service-group SYSTEM \"avahi-service.dtd\">
<service-group>
  <name replace-wildcards=\"yes\">inkdaddy</name>
  <service>
    <type>_http._tcp</type>
    <port>80</port>
  </service>
</service-group>
AVAHI"
  run pct exec "$id" -- bash -lc "systemctl daemon-reload && systemctl enable --now avahi-daemon inkdaddy.service inkdaddy-worker.service && systemctl restart inkdaddy.service inkdaddy-worker.service && nginx -t && systemctl restart nginx"
}

main() {
  need_root
  local id
  id="$(choose_ct_id)"
  if [[ -n "$LOCAL_ARCHIVE" ]]; then
    log "Installing inkDaddy into LXC $id (${CT_HOSTNAME}) from local archive ${LOCAL_ARCHIVE}"
  else
    log "Installing inkDaddy into LXC $id (${CT_HOSTNAME}) from ${REPO_URL}@${VERSION}"
  fi
  ensure_template
  create_container "$id"
  ensure_container_started "$id"
  install_inside_container "$id"
  log "Install complete. Open http://inkdaddy.local"
}

main "$@"
