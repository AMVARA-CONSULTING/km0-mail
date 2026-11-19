#!/usr/bin/env bash
# Apply KM0 branding to the live Mailcow install (UI theme, logos, SOGo shell).
# REQUIRED after /opt/mailcow-dockerized/update.sh — Mailcow's update runs
# `git checkout .` which resets tracked files under data/conf/sogo/custom-*.
#
# Usage:
#   ./scripts/apply-mailcow-branding.sh
#   MAILCOW_ROOT=/opt/mailcow-dockerized ./scripts/apply-mailcow-branding.sh
# Full post-update (branding + host nginx): ./scripts/mailcow-post-update.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BRAND_SRC="${REPO_ROOT}/config/mailcow-branding"
MAILCOW_ROOT="${MAILCOW_ROOT:-/opt/mailcow-dockerized}"

die() { echo "error: $*" >&2; exit 1; }

[[ -d "$BRAND_SRC" ]] || die "missing branding pack: $BRAND_SRC"
[[ -d "$MAILCOW_ROOT" ]] || die "MAILCOW_ROOT not found: $MAILCOW_ROOT"
[[ -f "$MAILCOW_ROOT/mailcow.conf" ]] || die "not a mailcow install: $MAILCOW_ROOT"

REDIS_CTR="$(cd "$MAILCOW_ROOT" && docker compose ps -q redis-mailcow 2>/dev/null | head -1 || true)"
[[ -n "$REDIS_CTR" ]] || die "redis-mailcow container not running in $MAILCOW_ROOT"

# shellcheck disable=SC1091
REDISPASS="$(grep -E '^REDISPASS=' "$MAILCOW_ROOT/mailcow.conf" | cut -d= -f2-)"
[[ -n "$REDISPASS" ]] || die "REDISPASS empty in mailcow.conf"

redis() {
  docker exec "$REDIS_CTR" redis-cli -a "$REDISPASS" --no-auth-warning "$@"
}

data_uri() {
  local file="$1" mime="$2"
  printf 'data:%s;base64,%s' "$mime" "$(base64 -w0 "$file")"
}

echo "==> Installing KM0 Mailcow theme → ${MAILCOW_ROOT}/data/web/css/themes/km0/"
mkdir -p "$MAILCOW_ROOT/data/web/css/themes/km0"
install -m 0644 "$BRAND_SRC/theme/theme.json" "$MAILCOW_ROOT/data/web/css/themes/km0/theme.json"
install -m 0644 "$BRAND_SRC/theme/theme.css"  "$MAILCOW_ROOT/data/web/css/themes/km0/theme.css"
install -m 0644 "$BRAND_SRC/theme/dark.css"   "$MAILCOW_ROOT/data/web/css/themes/km0/dark.css"

echo "==> Installing always-on custom CSS (gitignored by Mailcow — survives update)"
install -m 0644 "$BRAND_SRC/0081-custom-mailcow.css" \
  "$MAILCOW_ROOT/data/web/css/build/0081-custom-mailcow.css"

echo "==> Installing favicon"
install -m 0644 "$BRAND_SRC/assets/favicon.png" "$MAILCOW_ROOT/data/web/favicon.png"

echo "==> Installing SOGo logos + theme/SSO JS from km0-mail pack"
echo "    NOTE: data/conf/sogo/custom-* are TRACKED by Mailcow git; update.sh"
echo "    may reset them — this step restores the KM0 pack every time."
install -m 0644 "$BRAND_SRC/assets/logo-full.svg"  "$MAILCOW_ROOT/data/conf/sogo/custom-fulllogo.svg"
install -m 0644 "$BRAND_SRC/assets/logo-short.svg" "$MAILCOW_ROOT/data/conf/sogo/custom-shortlogo.svg"
install -m 0644 "$BRAND_SRC/assets/logo-full.png"  "$MAILCOW_ROOT/data/conf/sogo/custom-fulllogo.png"
install -m 0644 "$BRAND_SRC/assets/favicon.ico"    "$MAILCOW_ROOT/data/conf/sogo/custom-favicon.ico"
install -m 0644 "$BRAND_SRC/sogo/custom-theme.js"  "$MAILCOW_ROOT/data/conf/sogo/custom-theme.js"
install -m 0644 "$BRAND_SRC/sogo/custom-sogo.js"   "$MAILCOW_ROOT/data/conf/sogo/custom-sogo.js"

# Sanity: never ship a pack without contrast + SSO redirect
grep -q 'km0-sogo-contrast' "$MAILCOW_ROOT/data/conf/sogo/custom-sogo.js" \
  || die "custom-sogo.js missing km0-sogo-contrast block"
grep -q 'material-icons' "$MAILCOW_ROOT/data/conf/sogo/custom-sogo.js" \
  || die "custom-sogo.js missing material-icons contrast rules"
grep -q "location.href = '/user'" "$MAILCOW_ROOT/data/conf/sogo/custom-sogo.js" \
  || die "custom-sogo.js missing SSO login redirect"

echo "==> Setting Mailcow UI texts + theme in Redis (volume — survives update)"
redis SET TITLE_NAME "KM0 Mail"
redis SET MAIN_NAME "KM0 Mail"
redis SET APPS_NAME "Apps"
redis SET UI_FOOTER "KM0 Digital · mail.km0digital.com"
redis SET UI_THEME "km0"

echo "==> Setting Mailcow logos in Redis (light + dark)"
redis SET MAIN_LOGO      "$(data_uri "$BRAND_SRC/assets/logo.svg" "image/svg+xml")"
redis SET MAIN_LOGO_DARK "$(data_uri "$BRAND_SRC/assets/logo-dark.svg" "image/svg+xml")"

echo "==> Restarting nginx-mailcow + sogo-mailcow to pick up bind mounts / CSS cache"
(
  cd "$MAILCOW_ROOT"
  docker compose restart nginx-mailcow sogo-mailcow
)

echo "==> Done."
echo "    Login:  https://mail.km0digital.com/"
echo "    Theme:  System → Configuration → Customize → KM0 Digital (km0)"
echo "    After Mailcow ./update.sh always run:"
echo "      $REPO_ROOT/scripts/mailcow-post-update.sh"
