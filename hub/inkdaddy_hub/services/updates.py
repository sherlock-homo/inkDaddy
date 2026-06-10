from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from ..config import HubSettings, get_settings

GITHUB_API_VERSION = "2022-11-28"
FIRMWARE_SUFFIXES = (".gbl", ".bin", ".hex")
SOURCE_SUFFIXES = (".tar.gz", ".tgz")


class UpdateError(RuntimeError):
    """Raised when an update check or update launch cannot complete."""


@dataclass(frozen=True)
class ReleaseAsset:
    name: str
    browser_download_url: str
    size: int | None = None
    digest: str | None = None
    content_type: str | None = None

    @classmethod
    def from_api(cls, payload: dict[str, Any]) -> "ReleaseAsset":
        return cls(
            name=str(payload.get("name") or ""),
            browser_download_url=str(payload.get("browser_download_url") or ""),
            size=int(payload["size"]) if payload.get("size") is not None else None,
            digest=str(payload.get("digest")) if payload.get("digest") else None,
            content_type=str(payload.get("content_type")) if payload.get("content_type") else None,
        )

    @property
    def sha256(self) -> str | None:
        if self.digest and self.digest.startswith("sha256:"):
            return self.digest.split(":", 1)[1]
        return None


@dataclass(frozen=True)
class GitHubRelease:
    tag_name: str
    name: str | None
    body: str | None
    html_url: str | None
    tarball_url: str | None
    published_at: str | None
    prerelease: bool
    assets: tuple[ReleaseAsset, ...]

    @classmethod
    def from_api(cls, payload: dict[str, Any]) -> "GitHubRelease":
        assets = tuple(ReleaseAsset.from_api(item) for item in payload.get("assets", []))
        return cls(
            tag_name=str(payload.get("tag_name") or ""),
            name=str(payload.get("name")) if payload.get("name") is not None else None,
            body=str(payload.get("body")) if payload.get("body") is not None else None,
            html_url=str(payload.get("html_url")) if payload.get("html_url") else None,
            tarball_url=str(payload.get("tarball_url")) if payload.get("tarball_url") else None,
            published_at=str(payload.get("published_at")) if payload.get("published_at") else None,
            prerelease=bool(payload.get("prerelease", False)),
            assets=assets,
        )


@dataclass(frozen=True)
class UpdatePolicy:
    repository: str | None
    auto_apply: bool
    apply_allowed: bool
    check_interval_seconds: int
    command: str


@dataclass(frozen=True)
class HubUpdateInfo:
    current_version: str
    latest_version: str | None
    update_available: bool
    status: str
    repository: str | None
    release_channel: str
    release_notes: str | None = None
    release_url: str | None = None
    source_asset_url: str | None = None
    source_sha256: str | None = None
    tarball_url: str | None = None
    error: str | None = None


@dataclass(frozen=True)
class FirmwareUpdateInfo:
    board: str
    current_version: str | None
    latest_version: str | None
    update_available: bool
    status: str
    release_url: str | None = None
    artifact_url: str | None = None
    artifact_name: str | None = None
    size_bytes: int | None = None
    sha256: str | None = None
    release_notes: str | None = None
    min_bootloader_version: str | None = None
    battery_threshold_percent: int = 40
    requires_external_power: bool = False
    error: str | None = None


def normalize_github_repo(raw: str | None) -> str | None:
    if not raw:
        return None
    value = raw.strip()
    if not value or "OWNER/" in value or value.endswith("/OWNER/inkDaddy.git"):
        return None
    value = value.removesuffix(".git")
    if value.startswith("git@github.com:"):
        value = value.removeprefix("git@github.com:")
    elif value.startswith("https://github.com/"):
        value = value.removeprefix("https://github.com/")
    elif value.startswith("http://github.com/"):
        value = value.removeprefix("http://github.com/")
    value = value.strip("/")
    parts = value.split("/")
    if len(parts) != 2 or not all(parts):
        return None
    return f"{parts[0]}/{parts[1]}"


def update_policy(settings: HubSettings | None = None) -> UpdatePolicy:
    settings = settings or get_settings()
    return UpdatePolicy(
        repository=normalize_github_repo(settings.github_repo),
        auto_apply=settings.auto_update_enabled,
        apply_allowed=settings.update_allow_apply,
        check_interval_seconds=settings.update_check_interval_seconds,
        command=str(settings.update_command),
    )


def _github_headers(token: str | None = None) -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
        "User-Agent": "inkdaddy-hub",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _fetch_json(url: str, token: str | None = None, timeout: float = 15.0) -> dict[str, Any]:
    request = urllib.request.Request(url, headers=_github_headers(token), method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:160]
        raise UpdateError(f"GitHub API returned {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise UpdateError(f"GitHub API request failed: {exc.reason}") from exc


def fetch_latest_release(repository: str, token: str | None = None) -> GitHubRelease:
    payload = _fetch_json(f"https://api.github.com/repos/{repository}/releases/latest", token=token)
    return GitHubRelease.from_api(payload)


def _version_parts(value: str | None) -> tuple[int, ...] | None:
    if not value:
        return None
    cleaned = value.strip().removeprefix("v").split("-", 1)[0]
    if not re.fullmatch(r"\d+(\.\d+)*", cleaned):
        return None
    return tuple(int(part) for part in cleaned.split("."))


def is_newer_version(latest: str | None, current: str | None) -> bool:
    if not latest:
        return False
    latest_parts = _version_parts(latest)
    current_parts = _version_parts(current)
    if latest_parts is not None and current_parts is not None:
        width = max(len(latest_parts), len(current_parts))
        return latest_parts + (0,) * (width - len(latest_parts)) > current_parts + (0,) * (
            width - len(current_parts)
        )
    return latest != current


def select_source_asset(release: GitHubRelease) -> ReleaseAsset | None:
    candidates = [
        asset
        for asset in release.assets
        if asset.browser_download_url
        and asset.name.lower().endswith(SOURCE_SUFFIXES)
        and "firmware" not in asset.name.lower()
    ]
    if not candidates:
        return None
    return sorted(candidates, key=lambda asset: (0 if "inkdaddy" in asset.name.lower() else 1, asset.name))[0]


def select_firmware_asset(release: GitHubRelease, board: str) -> ReleaseAsset | None:
    normalized_board = board.lower().replace("-", "_")
    candidates = [
        asset
        for asset in release.assets
        if asset.browser_download_url
        and asset.name.lower().endswith(FIRMWARE_SUFFIXES)
        and normalized_board in asset.name.lower().replace("-", "_")
    ]
    if not candidates:
        return None
    return sorted(candidates, key=lambda asset: (0 if asset.name.lower().endswith(".gbl") else 1, asset.name))[0]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def get_hub_update_info(settings: HubSettings | None = None) -> HubUpdateInfo:
    settings = settings or get_settings()
    policy = update_policy(settings)
    if not policy.repository:
        return HubUpdateInfo(
            current_version=settings.version,
            latest_version=None,
            update_available=False,
            status="not_configured",
            repository=None,
            release_channel="github-releases",
            error="Set INKDADDY_GITHUB_REPO=owner/repo or INKDADDY_REPO=https://github.com/owner/repo.git.",
        )
    try:
        release = fetch_latest_release(policy.repository, settings.github_token)
    except UpdateError as exc:
        return HubUpdateInfo(
            current_version=settings.version,
            latest_version=None,
            update_available=False,
            status="error",
            repository=policy.repository,
            release_channel="github-releases",
            error=str(exc),
        )
    source_asset = select_source_asset(release)
    update_available = is_newer_version(release.tag_name, settings.version)
    return HubUpdateInfo(
        current_version=settings.version,
        latest_version=release.tag_name,
        update_available=update_available,
        status="update_available" if update_available else "current",
        repository=policy.repository,
        release_channel="github-releases",
        release_notes=release.body,
        release_url=release.html_url,
        source_asset_url=source_asset.browser_download_url if source_asset else None,
        source_sha256=source_asset.sha256 if source_asset else None,
        tarball_url=release.tarball_url,
    )


def get_firmware_update_info(
    board: str = "xiao_mg24", current_version: str | None = None, settings: HubSettings | None = None
) -> FirmwareUpdateInfo:
    settings = settings or get_settings()
    policy = update_policy(settings)
    if not policy.repository:
        return FirmwareUpdateInfo(
            board=board,
            current_version=current_version,
            latest_version=None,
            update_available=False,
            status="not_configured",
            error="Set INKDADDY_GITHUB_REPO or INKDADDY_REPO before checking firmware releases.",
        )
    try:
        release = fetch_latest_release(policy.repository, settings.github_token)
    except UpdateError as exc:
        return FirmwareUpdateInfo(
            board=board,
            current_version=current_version,
            latest_version=None,
            update_available=False,
            status="error",
            error=str(exc),
        )
    asset = select_firmware_asset(release, board)
    if not asset:
        return FirmwareUpdateInfo(
            board=board,
            current_version=current_version,
            latest_version=release.tag_name,
            update_available=False,
            status="no_firmware_asset",
            release_url=release.html_url,
            release_notes=release.body,
        )
    update_available = is_newer_version(release.tag_name, current_version)
    checksum = asset.sha256
    return FirmwareUpdateInfo(
        board=board,
        current_version=current_version,
        latest_version=release.tag_name,
        update_available=update_available,
        status="update_available" if update_available else "current",
        release_url=release.html_url,
        artifact_url=asset.browser_download_url,
        artifact_name=asset.name,
        size_bytes=asset.size,
        sha256=checksum,
        release_notes=release.body,
        error=None if checksum else "Firmware asset must include a GitHub sha256 digest or paired checksum asset.",
    )


def _job_log_path(settings: HubSettings) -> Path:
    jobs_dir = settings.data_dir / "jobs"
    jobs_dir.mkdir(parents=True, exist_ok=True)
    return jobs_dir / f"hub-update-{int(time.time())}.log"


def start_hub_update(
    version: str | None = None,
    settings: HubSettings | None = None,
    update_info: HubUpdateInfo | None = None,
) -> dict[str, Any]:
    settings = settings or get_settings()
    policy = update_policy(settings)
    requested_version = version or update_info.latest_version if update_info else version
    requested_version = requested_version or "latest"
    if not policy.apply_allowed:
        return {
            "accepted": False,
            "status": "apply_disabled",
            "detail": "Set INKDADDY_UPDATE_ALLOW_APPLY=1 on the hub service to allow update execution.",
            "requested_version": requested_version,
        }
    if not policy.repository and not update_info:
        return {
            "accepted": False,
            "status": "not_configured",
            "detail": "Set INKDADDY_GITHUB_REPO or INKDADDY_REPO before applying updates.",
            "requested_version": requested_version,
        }
    command = Path(policy.command)
    if not command.exists():
        return {
            "accepted": False,
            "status": "missing_update_command",
            "detail": f"Update command is not installed at {command}.",
            "requested_version": requested_version,
        }

    env = os.environ.copy()
    if policy.repository:
        env["INKDADDY_GITHUB_REPO"] = policy.repository
    env["INKDADDY_UPDATE_VERSION"] = requested_version
    if update_info:
        if update_info.source_asset_url:
            env["INKDADDY_RELEASE_ASSET_URL"] = update_info.source_asset_url
        if update_info.source_sha256:
            env["INKDADDY_RELEASE_SHA256"] = update_info.source_sha256
        if update_info.tarball_url:
            env["INKDADDY_RELEASE_TARBALL_URL"] = update_info.tarball_url

    log_path = _job_log_path(settings)
    log_handle = log_path.open("ab")
    process = subprocess.Popen(
        [str(command)],
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
        env=env,
    )
    return {
        "accepted": True,
        "status": "started",
        "pid": process.pid,
        "log_path": str(log_path),
        "requested_version": requested_version,
    }


def firmware_manifest_response(info: FirmwareUpdateInfo) -> dict[str, Any]:
    payload = asdict(info)
    payload["safe_update_required"] = [
        "battery_above_threshold_or_external_power",
        "hardware_target_match",
        "sha256_or_signature_valid",
        "rollback_capable_bootloader",
    ]
    return payload


def hub_update_response(info: HubUpdateInfo) -> dict[str, Any]:
    payload = asdict(info)
    payload["requires_backup"] = True
    return payload


def run_auto_update_cycle(settings: HubSettings | None = None) -> dict[str, Any]:
    settings = settings or get_settings()
    policy = update_policy(settings)
    if not policy.auto_apply:
        return {"status": "disabled", "detail": "INKDADDY_AUTO_UPDATE is not enabled."}
    info = get_hub_update_info(settings)
    if not info.update_available:
        return {"status": info.status, "latest_version": info.latest_version}
    return start_hub_update(info.latest_version, settings=settings, update_info=info)
