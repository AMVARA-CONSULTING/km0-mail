#!/usr/bin/env bash
# Smoke checks for km0-mail stack (run from repo root on the VPS).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

MAIL_HOST="${MAIL_HOSTNAME:-mail.km0digital.com}"
MAIL_DOMAIN="${MAIL_DOMAIN:-km0digital.com}"
FAIL=0

ok()   { echo "[OK]   $*"; }
warn() { echo "[WARN] $*"; }
fail() { echo "[FAIL] $*"; FAIL=1; }

echo "=== km0-mail verify-mail-stack.sh ==="
echo "host: ${MAIL_HOST}  domain: ${MAIL_DOMAIN}"
echo

echo "--- Docker Compose ---"
if docker compose ps --status running 2>/dev/null | grep -qE 'postfix|dovecot|rspamd|roundcube|postgres'; then
    docker compose ps
else
    fail "compose services not running — run: docker compose up -d"
fi
echo

echo "--- Service health ---"
for svc in postgres postfix dovecot rspamd roundcube; do
    if docker compose ps --status running "$svc" 2>/dev/null | tail -n +2 | grep -q "$svc"; then
        ok "$svc running"
    else
        fail "$svc not running"
    fi
done
echo

echo "--- Local ports ---"
for port in 25 587 993; do
    if ss -ltn "( sport = :${port} )" 2>/dev/null | grep -q ":${port}"; then
        ok "port ${port} listening"
    else
        fail "port ${port} not listening"
    fi
done

if ss -ltn "( sport = :8080 )" 2>/dev/null | grep -q ":8080"; then
    ok "roundcube bound on 127.0.0.1:8080"
else
    warn "roundcube not listening on 8080 (nginx proxy target)"
fi
echo

echo "--- DNS (optional) ---"
if command -v dig >/dev/null 2>&1; then
    mx="$(dig +short "${MAIL_DOMAIN}" MX 2>/dev/null | head -1 || true)"
    a="$(dig +short "${MAIL_HOST}" A 2>/dev/null | head -1 || true)"
    if [[ -n "$mx" ]]; then ok "MX ${MAIL_DOMAIN}: ${mx}"; else warn "MX not found for ${MAIL_DOMAIN}"; fi
    if [[ -n "$a" ]]; then ok "A ${MAIL_HOST}: ${a}"; else warn "A not found for ${MAIL_HOST}"; fi
else
    warn "dig not installed — skip DNS checks"
fi
echo

echo "--- PostgreSQL schema ---"
if docker compose exec -T postgres psql -U mail -d mail -tAc \
    "SELECT COUNT(*) FROM information_schema.tables WHERE table_name IN ('mail_accounts','mail_aliases','mail_domains');" \
    2>/dev/null | grep -q '^3$'; then
    ok "mail schema tables present"
else
    fail "mail schema tables missing"
fi
echo

echo "--- Webmail (via host Nginx when deployed) ---"
if curl -fsSI --max-time 5 "https://${MAIL_HOST}/" 2>/dev/null | head -1 | grep -qE '200|301|302'; then
    ok "https://${MAIL_HOST}/ responds"
else
    warn "https://${MAIL_HOST}/ not reachable (deploy nginx vhost + cert first)"
fi
echo

if [[ "$FAIL" -eq 0 ]]; then
    echo "All critical checks passed."
    exit 0
fi

echo "One or more checks failed."
exit 1
