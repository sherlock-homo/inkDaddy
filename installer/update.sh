#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="${INKDADDY_INSTALL_DIR:-/opt/inkdaddy}"
SRC_DIR="${INKDADDY_SRC_DIR:-${INSTALL_DIR}/src}"
CONFIG_FILE="${INKDADDY_CONFIG_FILE:-${INSTALL_DIR}/config/inkdaddy.env}"
REQUESTED_VERSION="${INKDADDY_UPDATE_VERSION:-${INKDADDY_TARGET_VERSION:-${INKDADDY_VERSION:-latest}}}"
VERSION="$REQUESTED_VERSION"
REPO_RAW="${INKDADDY_GITHUB_REPO:-${INKDADDY_REPO:-}}"
RELEASE_ASSET_URL="${INKDADDY_RELEASE_ASSET_URL:-}"
RELEASE_TARBALL_URL="${INKDADDY_RELEASE_TARBALL_URL:-}"
RELEASE_SHA256="${INKDADDY_RELEASE_SHA256:-}"
ALLOW_UNSIGNED="${INKDADDY_ALLOW_UNSIGNED_UPDATE:-0}"
WORK_DIR="${INKDADDY_UPDATE_WORK_DIR:-${INSTALL_DIR}/updates}"
HEALTH_URL="${INKDADDY_HEALTH_URL:-http://127.0.0.1:8080/api/health}"
HEALTH_ATTEMPTS="${INKDADDY_HEALTH_ATTEMPTS:-30}"
HEALTH_DELAY_SECONDS="${INKDADDY_HEALTH_DELAY_SECONDS:-2}"

if [[ -f "$CONFIG_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  . "$CONFIG_FILE"
  set +a
  VERSION="$REQUESTED_VERSION"
  REPO_RAW="${INKDADDY_GITHUB_REPO:-${INKDADDY_REPO:-$REPO_RAW}}"
  HEALTH_URL="${INKDADDY_HEALTH_URL:-$HEALTH_URL}"
  HEALTH_ATTEMPTS="${INKDADDY_HEALTH_ATTEMPTS:-$HEALTH_ATTEMPTS}"
  HEALTH_DELAY_SECONDS="${INKDADDY_HEALTH_DELAY_SECONDS:-$HEALTH_DELAY_SECONDS}"
fi

log() {
  printf '[inkDaddy update] %s\n' "$*"
}

normalize_repo() {
  local raw="$1"
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

curl_json() {
  local url="$1"
  local output="$2"
  local headers=(-H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28")
  if [[ -n "${INKDADDY_GITHUB_TOKEN:-}" ]]; then
    headers+=(-H "Authorization: Bearer ${INKDADDY_GITHUB_TOKEN}")
  fi
  curl -fsSL "${headers[@]}" "$url" -o "$output"
}

curl_asset() {
  local url="$1"
  local output="$2"
  local headers=(-H "Accept: application/octet-stream")
  if [[ -n "${INKDADDY_GITHUB_TOKEN:-}" ]]; then
    headers+=(-H "Authorization: Bearer ${INKDADDY_GITHUB_TOKEN}")
  fi
  curl -fsSL "${headers[@]}" "$url" -o "$output"
}

json_field() {
  local file="$1"
  local expr="$2"
  python3 - "$file" "$expr" <<'PY'
import json
import sys

payload = json.load(open(sys.argv[1], encoding="utf-8"))
expr = sys.argv[2]
if expr == "tag":
    print(payload.get("tag_name") or "")
elif expr == "tarball":
    print(payload.get("tarball_url") or "")
elif expr == "source_asset":
    for asset in payload.get("assets", []):
        name = (asset.get("name") or "").lower()
        if name.endswith((".tar.gz", ".tgz")) and "firmware" not in name:
            print(asset.get("browser_download_url") or "")
            break
elif expr == "source_sha256":
    for asset in payload.get("assets", []):
        name = (asset.get("name") or "").lower()
        if name.endswith((".tar.gz", ".tgz")) and "firmware" not in name:
            digest = asset.get("digest") or ""
            print(digest.split(":", 1)[1] if digest.startswith("sha256:") else "")
            break
PY
}

update_config_version() {
  local resolved_version="$1"
  mkdir -p "$(dirname "$CONFIG_FILE")"
  touch "$CONFIG_FILE"
  chmod 0600 "$CONFIG_FILE"
  python3 - "$CONFIG_FILE" "$resolved_version" <<'PY'
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
version = sys.argv[2]
lines = path.read_text(encoding="utf-8").splitlines()
out = []
updated = False
for line in lines:
    if line.startswith("INKDADDY_VERSION="):
        out.append(f"INKDADDY_VERSION={version}")
        updated = True
    else:
        out.append(line)
if not updated:
    out.append(f"INKDADDY_VERSION={version}")
path.write_text("\n".join(out) + "\n", encoding="utf-8")
PY
}

read_source_version() {
  local pyproject="${1:-${SRC_DIR}/pyproject.toml}"
  if [[ ! -f "$pyproject" ]]; then
    return 0
  fi
  python3 - "$pyproject" <<'PY'
import re
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text(encoding="utf-8")
match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
if match:
    print(f"v{match.group(1)}")
PY
}

wait_for_health() {
  local attempts="$HEALTH_ATTEMPTS"
  local delay="$HEALTH_DELAY_SECONDS"
  local attempt

  for ((attempt = 1; attempt <= attempts; attempt += 1)); do
    if curl -fsS "$HEALTH_URL" >/dev/null; then
      return 0
    fi
    log "Health check attempt ${attempt}/${attempts} failed; retrying in ${delay}s"
    sleep "$delay"
  done

  return 1
}

install_source_tree() {
  local source_tree="$1"
  log "Updating Python environment"
  python3 -m venv "${INSTALL_DIR}/venv"
  "${INSTALL_DIR}/venv/bin/pip" install --upgrade pip
  "${INSTALL_DIR}/venv/bin/pip" install -e "$source_tree"

  if [[ -f "$source_tree/hub/frontend/package.json" ]]; then
    log "Building frontend"
    (cd "$source_tree/hub/frontend" && npm ci && npm run build)
  fi

  install -m 0755 "$source_tree/installer/update.sh" "${INSTALL_DIR}/bin/inkdaddy-update"
  install -m 0755 "$source_tree/installer/backup.sh" "${INSTALL_DIR}/bin/inkdaddy-backup"
  install -m 0755 "$source_tree/installer/restore.sh" "${INSTALL_DIR}/bin/inkdaddy-restore"
  install -m 0755 "$source_tree/installer/uninstall.sh" "${INSTALL_DIR}/bin/inkdaddy-uninstall"
}

prepare_release_source() {
  local archive="$1"
  local extract_dir="$2"
  local prepared_dir="$3"
  mkdir -p "$extract_dir" "$prepared_dir"
  tar -xzf "$archive" -C "$extract_dir"
  local candidate="$extract_dir"
  if [[ ! -f "$candidate/pyproject.toml" ]]; then
    local pyproject
    pyproject="$(find "$extract_dir" -mindepth 2 -maxdepth 2 -name pyproject.toml | head -n 1)"
    if [[ -z "$pyproject" ]]; then
      log "Downloaded archive does not contain pyproject.toml"
      exit 1
    fi
    candidate="$(dirname "$pyproject")"
  fi
  cp -a "$candidate"/. "$prepared_dir"/
}

rollback_code() {
  if [[ -d "${SRC_DIR}.rollback" ]]; then
    log "Rolling back source tree"
    rm -rf "${SRC_DIR}.failed"
    if [[ -d "$SRC_DIR" ]]; then
      mv "$SRC_DIR" "${SRC_DIR}.failed"
    fi
    mv "${SRC_DIR}.rollback" "$SRC_DIR"
    install_source_tree "$SRC_DIR" || true
    systemctl daemon-reload || true
    systemctl restart inkdaddy.service inkdaddy-worker.service || true
  fi
}

main() {
  local repo
  repo="$(normalize_repo "$REPO_RAW")"
  local stamp
  stamp="$(date -u +%Y%m%dT%H%M%SZ)"
  local release_dir="${WORK_DIR}/${stamp}"
  local release_json="${release_dir}/release.json"
  local archive="${release_dir}/source.tar.gz"
  local extract_dir="${release_dir}/extract"
  local prepared_dir="${release_dir}/src.new"
  local resolved_version="$VERSION"
  local previous_version
  previous_version="$(read_source_version "$SRC_DIR/pyproject.toml")"

  mkdir -p "$release_dir" "${INSTALL_DIR}/bin"

  if [[ -z "$RELEASE_ASSET_URL" && -z "$RELEASE_TARBALL_URL" && -n "$repo" ]]; then
    local api_url
    if [[ "$VERSION" == "latest" ]]; then
      api_url="https://api.github.com/repos/${repo}/releases/latest"
    else
      api_url="https://api.github.com/repos/${repo}/releases/tags/${VERSION}"
    fi
    log "Fetching GitHub release metadata for ${repo}@${VERSION}"
    curl_json "$api_url" "$release_json"
    resolved_version="$(json_field "$release_json" tag)"
    RELEASE_ASSET_URL="$(json_field "$release_json" source_asset)"
    RELEASE_SHA256="${RELEASE_SHA256:-$(json_field "$release_json" source_sha256)}"
    RELEASE_TARBALL_URL="$(json_field "$release_json" tarball)"
  fi

  if [[ -n "$RELEASE_ASSET_URL" ]]; then
    log "Downloading release source asset for ${resolved_version}"
    curl_asset "$RELEASE_ASSET_URL" "$archive"
  elif [[ -n "$RELEASE_TARBALL_URL" ]]; then
    log "Downloading GitHub release tarball for ${resolved_version}"
    curl_asset "$RELEASE_TARBALL_URL" "$archive"
  elif [[ -d "${SRC_DIR}/.git" && -n "$repo" ]]; then
    log "Updating git checkout ${repo}@${VERSION}"
    "${INSTALL_DIR}/bin/inkdaddy-backup" --metadata-only || true
    systemctl stop inkdaddy-worker.service inkdaddy.service || true
    git -C "$SRC_DIR" fetch --all --tags
    git -C "$SRC_DIR" checkout "$VERSION"
    install_source_tree "$SRC_DIR"
    systemctl daemon-reload
    systemctl restart inkdaddy.service inkdaddy-worker.service
    wait_for_health
    update_config_version "$VERSION"
    systemctl restart inkdaddy.service inkdaddy-worker.service
    wait_for_health
    log "Update complete"
    return
  else
    log "No GitHub release asset, tarball URL, or git checkout is configured."
    exit 1
  fi

  if [[ -n "$RELEASE_SHA256" ]]; then
    log "Verifying source archive SHA-256"
    printf '%s  %s\n' "$RELEASE_SHA256" "$archive" | sha256sum -c -
  elif [[ "$ALLOW_UNSIGNED" != "1" ]]; then
    log "Refusing unsigned update. Upload a release source asset with a GitHub SHA-256 digest or set INKDADDY_ALLOW_UNSIGNED_UPDATE=1."
    exit 1
  else
    log "Unsigned update allowed by INKDADDY_ALLOW_UNSIGNED_UPDATE=1"
  fi

  prepare_release_source "$archive" "$extract_dir" "$prepared_dir"

  log "Creating metadata backup"
  "${INSTALL_DIR}/bin/inkdaddy-backup" --metadata-only || true

  log "Stopping services"
  systemctl stop inkdaddy-worker.service inkdaddy.service || true

  rm -rf "${SRC_DIR}.rollback"
  if [[ -d "$SRC_DIR" ]]; then
    mv "$SRC_DIR" "${SRC_DIR}.rollback"
  fi
  mv "$prepared_dir" "$SRC_DIR"

  if install_source_tree "$SRC_DIR"; then
    update_config_version "$resolved_version"
    log "Restarting services"
    systemctl daemon-reload
    systemctl restart inkdaddy.service inkdaddy-worker.service
    log "Health check"
    if wait_for_health; then
      update_config_version "$resolved_version"
      systemctl restart inkdaddy.service inkdaddy-worker.service
      log "Health check after version stamp"
      if wait_for_health; then
        rm -rf "${SRC_DIR}.rollback"
        log "Update complete"
        return
      fi
    fi
  fi

  if [[ -n "$previous_version" ]]; then
    update_config_version "$previous_version" || true
  fi
  rollback_code
  log "Update failed; rolled back where practical."
  exit 1
}

main "$@"
