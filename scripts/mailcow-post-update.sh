#!/usr/bin/env bash
# Run AFTER /opt/mailcow-dockerized/update.sh
# Re-applies KM0 branding (Mailcow may reset tracked SOGo custom-* via git checkout)
# and refreshes host nginx vhost from this repo.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MAILCOW_ROOT="${MAILCOW_ROOT:-/opt/mailcow-dockerized}"

echo "==> KM0 mailcow post-update"
"$REPO_ROOT/scripts/apply-mailcow-branding.sh"

NGINX_SRC="$REPO_ROOT/nginx/sites-available/mail"
if [[ -f "$NGINX_SRC" ]]; then
  echo "==> Installing host nginx vhost from repo → /etc/nginx/sites-available/mail"
  install -m 0644 "$NGINX_SRC" /etc/nginx/sites-available/mail
  ln -sfn /etc/nginx/sites-available/mail /etc/nginx/sites-enabled/mail
  nginx -t
  systemctl reload nginx
else
  echo "warn: missing $NGINX_SRC (host nginx not updated)" >&2
fi

echo "==> Post-update checks"
test -f "$MAILCOW_ROOT/data/conf/sogo/custom-sogo.js"
grep -q 'km0-sogo-contrast' "$MAILCOW_ROOT/data/conf/sogo/custom-sogo.js"
grep -q 'material-icons' "$MAILCOW_ROOT/data/conf/sogo/custom-sogo.js"
test -f "$MAILCOW_ROOT/data/web/css/build/0081-custom-mailcow.css"
test -f "$MAILCOW_ROOT/data/web/css/themes/km0/theme.json"
echo "OK — branding + nginx re-applied. Hard-refresh browser (Ctrl+Shift+R)."
