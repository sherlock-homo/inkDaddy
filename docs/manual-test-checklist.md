# Manual Test Checklist

- Proxmox: run installer dry-run, then live install on a test host.
- Hub: open `http://inkdaddy.local`, confirm `/api/health`.
- UI: compare the app to `docs/assets/inkdaddy-ui-concept.png` on desktop and
  mobile.
- Home Assistant: paste token, validate it, fetch entity list.
- Dashboard: import sample YAML, detect overlap errors, render preview.
- Photos: upload batch, confirm previews and raw frames.
- Device simulator: poll manifest, download frame, report displayed.
- Pairing: verify unjoined simulator alternates Matter join screen every other refresh.
- Firmware: build SiSDK project, flash XIAO MG24, capture serial logs for boot,
  provisioning, Thread join, manifest check, frame download, checksum, refresh,
  status report, and sleep.
- OTA: create GitHub release metadata, check hub update screen, verify backup first.
