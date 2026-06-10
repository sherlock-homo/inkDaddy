#!/usr/bin/env bash
set -euo pipefail

KEEP_DATA="${INKDADDY_KEEP_DATA:-1}"

systemctl disable --now inkdaddy-worker.service inkdaddy.service || true
rm -f /etc/systemd/system/inkdaddy-worker.service /etc/systemd/system/inkdaddy.service
rm -f /etc/nginx/sites-enabled/inkdaddy /etc/nginx/sites-available/inkdaddy
systemctl daemon-reload
systemctl reload nginx || true

if [[ "$KEEP_DATA" != "1" ]]; then
  rm -rf /opt/inkdaddy
else
  printf 'Kept /opt/inkdaddy data. Set INKDADDY_KEEP_DATA=0 to remove it.\n'
fi
