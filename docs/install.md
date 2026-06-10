# Install Guide

Run the helper from a Proxmox VE host shell as root:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/OWNER/inkDaddy/main/installer/install.sh)"
```

Useful overrides:

```bash
INKDADDY_REPO=https://github.com/OWNER/inkDaddy.git \
INKDADDY_VERSION=v0.1.0 \
INKDADDY_STORAGE=local-lvm \
INKDADDY_ROOTFS_SIZE=12G \
INKDADDY_MEMORY_MB=2048 \
INKDADDY_CORES=2 \
bash -c "$(curl -fsSL https://raw.githubusercontent.com/OWNER/inkDaddy/main/installer/install.sh)"
```

Automatic self-update is configured from the same repository value. For a real
deployment, replace `OWNER/inkDaddy` with your actual repo and keep these enabled
if the hub should apply new GitHub Releases without manual SSH:

```bash
INKDADDY_REPO=https://github.com/OWNER/inkDaddy.git \
INKDADDY_AUTO_UPDATE=1 \
INKDADDY_UPDATE_ALLOW_APPLY=1 \
bash -c "$(curl -fsSL https://raw.githubusercontent.com/OWNER/inkDaddy/main/installer/install.sh)"
```

For private repositories, add `INKDADDY_GITHUB_TOKEN` manually to
`/opt/inkdaddy/config/inkdaddy.env` after install and keep that file at `0600`.

`INKDADDY_ROOTFS_SIZE` accepts values like `12` or `12G`; the installer sends
the numeric GiB value expected by `pct`.

The installer creates an unprivileged Debian LXC named `inkdaddy`, installs the
hub into `/opt/inkdaddy`, stores durable data under `/opt/inkdaddy/data`, starts
systemd services, configures Nginx on port 80, and advertises `inkdaddy.local`
with Avahi.

Re-running the installer reuses an existing LXC whose name matches
`INKDADDY_HOSTNAME` instead of allocating a new CT ID.

If Avahi reports a hostname conflict, another device already owns
`inkdaddy.local`; the new service will be reachable at Avahi's conflict fallback
such as `inkdaddy-2.local` until the older service is renamed or stopped.

Dry-run the command shape without creating the LXC:

```bash
INKDADDY_DRY_RUN=1 ./installer/install.sh
```

To install an unpublished local checkout from a tar archive already present on
the Proxmox host:

```bash
INKDADDY_LOCAL_ARCHIVE=/tmp/inkdaddy-src.tar.gz ./installer/install.sh
```

From this checkout, the local deploy wrapper can package the worktree, copy it
to the Proxmox node, and run the installer:

```bash
PROXMOX_HOST=10.0.0.118 PROXMOX_USER=root scripts/deploy_proxmox_local.sh
```

Use `INKDADDY_DRY_RUN=1` with that command to exercise the remote installer
without creating or changing an LXC. The wrapper uses non-interactive SSH by
default; set `INKDADDY_SSH_BATCH_MODE=no` when running it manually and you want
SSH to prompt for a password. By default it uses
`~/.ssh/inkdaddy_codex_ed25519` when that key exists; override with
`INKDADDY_SSH_KEY=/path/to/key`.

Manual checks after install:

```bash
pct list
pct exec <CTID> -- systemctl status inkdaddy.service inkdaddy-worker.service
pct exec <CTID> -- curl -fsS http://127.0.0.1:8080/api/health
```
