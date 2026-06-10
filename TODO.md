# inkDaddy TODO

## Phase 1 - Hub Backend Skeleton And Local Dev

- [x] Create monorepo directory structure.
- [x] Add this root `TODO.md` tracker.
- [x] Add Python package metadata and dependency declarations.
- [x] Scaffold FastAPI app, API routers, settings, and health endpoints.
- [x] Add SQLite/SQLAlchemy model definitions for core product data.
- [x] Add pure backend services for dashboard validation, palette packing, rendering, provisioning alternation, and Home Assistant response handling.
- [x] Add local development docs and root README.
- [x] Add first pure-Python test coverage for the dependency-light core.
- [ ] Wire Alembic migration generation and first migration after dependencies are installed.
- [ ] Replace in-memory API placeholders with database-backed repositories.

## Phase 2 - Proxmox Installer And Lifecycle Scripts

- [x] Add Proxmox helper-style installer script skeleton.
- [x] Add update, uninstall, backup, and restore helper scripts.
- [x] Add systemd and reverse-proxy installation shape in scripts.
- [x] Document dry-run and manual Proxmox test path.
- [x] Add local source archive install path for unpublished Proxmox deploys.
- [x] Add local-to-Proxmox archive deploy wrapper.
- [x] Create dedicated local SSH deploy key `~/.ssh/inkdaddy_codex_ed25519`.
- [x] Validate installer in a real Proxmox host.
  - 2026-06-10 deployed to Proxmox node `10.0.0.118` as CT `100` named `inkdaddy`; LXC IP `10.0.1.56`.
  - 2026-06-10 fixed blockers: SSH key auth, `pvesh get /cluster/nextid`, Debian template `12.12`, Proxmox rootfs size syntax, and Nginx restart after site install.
  - 2026-06-10 mDNS note: `inkdaddy.local` is already owned by cluster node `sashay` at `10.0.0.116` advertising legacy inkDaddy `version=0.4.0-container`; new rewrite is reachable at `http://10.0.1.56` and `http://inkdaddy-2.local`.
- [ ] Add shellcheck CI once dependencies are available.

## Phase 3 - Photo Processing And Frame Pipeline

- [x] Add image palette conversion and packed raw frame helpers.
- [x] Add deterministic ePaper preview and provisioning-screen renderer.
- [x] Add photo API placeholders.
- [x] Replace photo placeholders with SQLite-backed upload, metadata, preview, and raw-frame endpoints.
- [x] Add album create/list/detail/reorder APIs for photo playlists.
- [x] Persist uploads to originals/processed/previews/frames.
- [x] Add EXIF orientation, crop, fit, fill, playlists, albums, delete, rename, reorder.

## Phase 4 - Dashboard Schema And Renderer

- [x] Add dashboard YAML/dict schema validation.
- [x] Add 2 row x 4 column tile overlap detection.
- [x] Add sample dashboard fixture and docs.
- [ ] Add database-backed dashboard import/export.
- [ ] Add widget renderers for all required widget types.

## Phase 5 - Home Assistant Integration

- [x] Add HA API service helpers and token redaction.
- [x] Add HA config/test/entities API skeleton.
- [x] Document token-paste workflow.
- [x] Add generic integrations API/UI section with Home Assistant status.
- [x] Replace HA placeholders with persisted config, restricted token storage, live validation, and entity cache refresh.
- [x] Persist validated HA token in restricted secrets store.
- [x] Fetch and cache HA entities/devices from a live HA instance.

## Phase 6 - Modern Purple UI

- [x] Add React/Vite/TypeScript/Tailwind frontend scaffold.
- [x] Add approved purple operations dashboard shell and primary routes.
- [x] Add mobile-aware layout, loading/error states, and pairing state surfaces.
- [x] Install frontend dependencies and run browser visual verification.
- [x] Iterate UI against generated concept screenshot.

## Phase 7 - Display Simulator And Device APIs

- [x] Add simulator script.
- [x] Add device heartbeat, manifest, frame, config, and refresh-result API skeleton.
- [x] Add unjoined Matter join-screen alternation tests.
- [x] Replace device placeholders with SQLite-backed registry, heartbeat history, display assignment, and per-device frame publishing.
- [x] Add UI for device registration, simulator creation, refresh interval/content selection, and status history.
- [x] Exercise simulator against a running hub.

## Phase 8 - XIAO MG24 SiSDK Firmware MVP

- [x] Add SiSDK-first firmware design skeleton and HAL interfaces.
- [x] Add provisioning join-screen rendering contract with Matter QR/manual code/discriminator behavior.
- [x] Document SLC-CLI firmware workflow.
- [x] Add SiSDK scaffold validation script with strict build-machine checks.
- [ ] Create real SiSDK project from installed Silicon Labs tooling.
- [ ] Implement Thread join/resume, BLE/Matter commissioning, CoAP/UDP frame pull, battery/status, ePaper refresh, and deep sleep on hardware.

## Phase 9 - OTA And Releases

- [x] Add release/update docs and script skeletons.
- [x] Add hub and firmware update API placeholders.
- [x] Implement GitHub Release metadata fetching and checksum-aware hub update checks.
- [x] Add worker-driven automatic hub update execution through `/opt/inkdaddy/bin/inkdaddy-update`.
- [x] Add release asset builder for source archives, checksums, and optional XIAO MG24 firmware artifacts.
- [x] Add firmware OTA manifest endpoint and portable XIAO MG24 OTA safety-gate scaffold.
- [x] Add retrying hub-update health checks and safe post-health version stamping for Proxmox OTA.
- [ ] Implement SiSDK rollback-safe firmware OTA path on hardware.

## Phase 10 - Matter Control/Status Expansion

- [x] Reserve hub data model and firmware abstraction for Matter control/status.
- [ ] Implement Matter battery, status, selected content, refresh interval, identify, force refresh, and OTA state after MVP validation.

## Verification

- [x] Add tests for dashboard validation, tile collision, palette pack/unpack, Home Assistant mock responses, provisioning alternation, and API contract availability.
- [x] Run dependency-light local tests.
- [x] Install backend/frontend dependencies and run full test/build pass.
- [x] Validate Proxmox install.
- [ ] Validate XIAO MG24 firmware on hardware.
