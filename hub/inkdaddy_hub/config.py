from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = REPO_ROOT / ".inkdaddy-data"


@dataclass(frozen=True)
class HubSettings:
    app_name: str = "inkDaddy"
    version: str = "0.1.1"
    host: str = "0.0.0.0"
    port: int = 8080
    data_dir: Path = DEFAULT_DATA_DIR
    database_url: str = f"sqlite:///{DEFAULT_DATA_DIR / 'inkdaddy.db'}"
    secrets_path: Path = DEFAULT_DATA_DIR / "secrets.json"
    frontend_dist: Path = Path(__file__).resolve().parents[1] / "frontend" / "dist"
    default_width: int = 800
    default_height: int = 480
    default_palette: str = "waveshare_7color_6"
    default_refresh_minutes: int = 30
    min_refresh_minutes: int = 10
    max_refresh_minutes: int = 3600
    provisioning_timeout_seconds: int = 300
    startup_join_timeout_seconds: int = 30
    github_repo: str | None = None
    github_token: str | None = None
    update_command: Path = Path("/opt/inkdaddy/bin/inkdaddy-update")
    update_allow_apply: bool = False
    auto_update_enabled: bool = False
    update_check_interval_seconds: int = 3600

    @classmethod
    def from_env(cls) -> "HubSettings":
        data_dir = Path(os.getenv("INKDADDY_DATA_DIR", str(DEFAULT_DATA_DIR)))
        repo = os.getenv("INKDADDY_GITHUB_REPO") or os.getenv("INKDADDY_REPO")
        return cls(
            app_name=os.getenv("INKDADDY_APP_NAME", "inkDaddy"),
            version=os.getenv("INKDADDY_VERSION", "0.1.1"),
            host=os.getenv("INKDADDY_HOST", "0.0.0.0"),
            port=int(os.getenv("INKDADDY_PORT", "8080")),
            data_dir=data_dir,
            database_url=os.getenv("INKDADDY_DATABASE_URL", f"sqlite:///{data_dir / 'inkdaddy.db'}"),
            secrets_path=Path(os.getenv("INKDADDY_SECRETS_PATH", str(data_dir / "secrets.json"))),
            frontend_dist=Path(
                os.getenv(
                    "INKDADDY_FRONTEND_DIST",
                    str(Path(__file__).resolve().parents[1] / "frontend" / "dist"),
                )
            ),
            default_width=int(os.getenv("INKDADDY_DEFAULT_WIDTH", "800")),
            default_height=int(os.getenv("INKDADDY_DEFAULT_HEIGHT", "480")),
            default_palette=os.getenv("INKDADDY_DEFAULT_PALETTE", "waveshare_7color_6"),
            default_refresh_minutes=int(os.getenv("INKDADDY_DEFAULT_REFRESH_MINUTES", "30")),
            github_repo=repo,
            github_token=os.getenv("INKDADDY_GITHUB_TOKEN"),
            update_command=Path(os.getenv("INKDADDY_UPDATE_COMMAND", "/opt/inkdaddy/bin/inkdaddy-update")),
            update_allow_apply=os.getenv("INKDADDY_UPDATE_ALLOW_APPLY", "0") == "1",
            auto_update_enabled=os.getenv("INKDADDY_AUTO_UPDATE", "0") == "1",
            update_check_interval_seconds=int(os.getenv("INKDADDY_UPDATE_CHECK_INTERVAL_SECONDS", "3600")),
        )

    def ensure_data_dirs(self) -> None:
        for name in (
            "originals",
            "processed",
            "previews",
            "frames",
            "dashboards",
            "backups",
            "jobs",
            "updates",
        ):
            (self.data_dir / name).mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> HubSettings:
    return HubSettings.from_env()
