from __future__ import annotations

from pathlib import Path

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.staticfiles import StaticFiles
except ModuleNotFoundError as exc:  # pragma: no cover - dependency bootstrap path
    raise RuntimeError(
        "FastAPI is required to run the hub. Install dependencies with "
        '`pip install -e ".[dev]"` from the repository root.'
    ) from exc

from .api import dashboards, devices, diagnostics, health, home_assistant, integrations, photos, setup, settings, simulator, updates
from .config import get_settings
from .database import init_db


def create_app() -> FastAPI:
    hub_settings = get_settings()
    app = FastAPI(title="inkDaddy Hub", version=hub_settings.version)
    init_db()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://inkdaddy.local", "http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(setup.router)
    app.include_router(settings.router)
    app.include_router(integrations.router)
    app.include_router(home_assistant.router)
    app.include_router(dashboards.router)
    app.include_router(photos.router)
    app.include_router(devices.router)
    app.include_router(simulator.router)
    app.include_router(updates.router)
    app.include_router(diagnostics.router)

    dist = Path(hub_settings.frontend_dist)
    if dist.exists():
        app.mount("/", StaticFiles(directory=dist, html=True), name="frontend")
    return app


app = create_app()
