# inkDaddy

inkDaddy is a local-first management hub for battery-powered color ePaper
displays. The hub is designed to install as a normal Proxmox LXC guest, expose
`http://inkdaddy.local`, integrate with Home Assistant, render ePaper-ready
dashboard/photo frames, and manage display health plus future OTA updates.

This repository is intentionally structured as a monorepo:

- `hub/` - FastAPI backend, renderer, Home Assistant integration, and React UI.
- `firmware/xiao_mg24/` - primary Seeed XIAO MG24 firmware target using Silicon
  Labs SiSDK / Matter Extension.
- `installer/` - Proxmox helper-style install, update, backup, restore, and
  uninstall scripts.
- `docs/` - user and developer guides.
- `tests/` - backend, renderer, API, simulator, and fixture tests.

## Local Development

Backend:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
uvicorn inkdaddy_hub.main:app --app-dir hub --reload
```

Frontend:

```bash
cd hub/frontend
npm install
npm run dev
```

Pure-Python tests that do not require web dependencies:

```bash
PYTHONPATH=hub python3 -m unittest discover -s tests
```

Full test pass after installing dependencies:

```bash
pytest
cd hub/frontend && npm run typecheck && npm run build
```

## Proxmox Install Shape

The intended public install command is:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/OWNER/inkDaddy/main/installer/install.sh)"
```

Set `INKDADDY_REPO`, `INKDADDY_VERSION`, `INKDADDY_STORAGE`, and related
environment variables to pin source, version, storage, CPU, memory, or disk
defaults. See [docs/install.md](docs/install.md).

Automatic updates are release-driven. Point the LXC at the real repository with
`INKDADDY_REPO=https://github.com/<owner>/<repo>.git` or
`INKDADDY_GITHUB_REPO=<owner>/<repo>`, publish GitHub Releases with source
archive checksums, and the worker can apply the latest release through
`/opt/inkdaddy/bin/inkdaddy-update`. See [docs/update.md](docs/update.md) and
[docs/releases.md](docs/releases.md).

## Firmware Direction

The primary display target is Seeed XIAO MG24. Firmware work goes straight to
Silicon Labs SiSDK / Matter Extension and SLC-CLI. Zephyr is deliberately not a
v1 path. Matter/Thread is the control/status plane; full ePaper frame payloads
are transferred separately over Thread IPv6 using CoAP blockwise or chunked UDP.
