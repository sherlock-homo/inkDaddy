# Update, Backup, Restore, And Uninstall

Inside the LXC:

```bash
/opt/inkdaddy/bin/inkdaddy-backup
/opt/inkdaddy/bin/inkdaddy-update
```

Pin an update:

```bash
INKDADDY_UPDATE_VERSION=v0.1.0 /opt/inkdaddy/bin/inkdaddy-update
```

## Automatic Hub Updates

The hub worker checks GitHub Releases when these service environment values are
set in `/opt/inkdaddy/config/inkdaddy.env`:

```bash
INKDADDY_GITHUB_REPO=owner/inkDaddy
INKDADDY_AUTO_UPDATE=1
INKDADDY_UPDATE_ALLOW_APPLY=1
INKDADDY_UPDATE_CHECK_INTERVAL_SECONDS=3600
INKDADDY_UPDATE_COMMAND=/opt/inkdaddy/bin/inkdaddy-update
```

The installer writes this file with `0600` permissions. For private
repositories, add a read-only GitHub token there as `INKDADDY_GITHUB_TOKEN=...`
and restart both services:

```bash
systemctl restart inkdaddy.service inkdaddy-worker.service
```

The update API exposes the same state:

```bash
curl http://127.0.0.1:8080/api/updates/hub/check
curl http://127.0.0.1:8080/api/updates/hub/auto
```

`inkdaddy-update` prefers a release source asset such as
`inkdaddy-v0.2.0.tar.gz` with a GitHub `sha256:` digest. It refuses unsigned
source updates by default. `INKDADDY_ALLOW_UNSIGNED_UPDATE=1` exists only for
manual recovery and should not be used for unattended updates.

Update flow:

1. Fetch selected/latest GitHub Release metadata.
2. Download the source archive asset, or the GitHub tarball if explicitly
   allowed.
3. Verify SHA-256 when present.
4. Create a metadata backup.
5. Stop services.
6. Install into a new source tree and rebuild frontend assets.
7. Restart services and health-check `/api/health`.
8. Roll back the previous source tree where practical if health check fails.

Restore:

```bash
/opt/inkdaddy/bin/inkdaddy-restore /opt/inkdaddy/data/backups/inkdaddy-backup-YYYYMMDDTHHMMSSZ.tar.gz
```

Uninstall service files while keeping data:

```bash
/opt/inkdaddy/bin/inkdaddy-uninstall
```

Remove data too:

```bash
INKDADDY_KEEP_DATA=0 /opt/inkdaddy/bin/inkdaddy-uninstall
```
