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

echo "--- Registration APIs ---"
if curl -fsS --max-time 3 http://127.0.0.1:8092/health 2>/dev/null | grep -q '"ok":true'; then
    ok "mail-provision-api health"
else
    warn "mail-provision-api not healthy on :8092"
fi
if curl -fsS --max-time 3 http://127.0.0.1:8093/health 2>/dev/null | grep -q '"ok":true'; then
    ok "domain-verify-api health"
else
    warn "domain-verify-api not healthy on :8093"
fi
if curl -fsSI --max-time 5 "https://${MAIL_HOST}/login.html" 2>/dev/null | grep -qi 'auth.km0digital.com'; then
    ok "https://${MAIL_HOST}/login.html redirects to auth hub"
else
    warn "mail login.html not redirecting to auth hub"
fi
echo
if curl -fsSI --max-time 5 "https://${MAIL_HOST}/" 2>/dev/null | head -1 | grep -qE '200|301|302'; then
    ok "https://${MAIL_HOST}/ responds"
else
    warn "https://${MAIL_HOST}/ not reachable (deploy nginx vhost + cert first)"
fi
echo

echo "--- Dovecot auth ---"
if docker compose exec -T dovecot test -f /run/dovecot/auth.conf 2>/dev/null; then
    ok "dovecot auth.conf rendered"
else
    fail "dovecot auth.conf missing — rebuild dovecot image"
fi
auth_out=""
auth_rc=0
auth_out="$(timeout 8 docker compose exec -T dovecot doveadm auth test "postmaster@${MAIL_DOMAIN}" '__verify_stack_wrong__' 2>&1)" || auth_rc=$?
if [[ "$auth_rc" -eq 77 ]] || echo "$auth_out" | grep -qiE 'auth failed|invalid credentials|password mismatch'; then
    ok "dovecot auth worker responding (expected failure for probe password)"
elif [[ "$auth_rc" -eq 75 ]] || echo "$auth_out" | grep -qiE "Couldn't connect to auth|Auth process broken|Timeout waiting"; then
    fail "dovecot auth worker broken — check docker compose logs dovecot"
else
    warn "dovecot auth probe inconclusive (rc=${auth_rc})"
fi
echo

echo "--- Postfix SMTP ---"
for port in 25 587; do
    banner=""
    banner="$(timeout 5 docker compose exec -T postfix python3 -c "
import socket
s=socket.create_connection(('127.0.0.1',${port}),5)
s.settimeout(5)
print(s.recv(256).decode('ascii','replace').strip())
s.close()
" 2>/dev/null | tr -d '\r' || true)"
    if [[ "$banner" == 220* ]]; then
        ok "postfix port ${port} SMTP banner"
    else
        fail "postfix port ${port} no SMTP banner (got: ${banner:-timeout})"
    fi
done
echo

echo "--- Postfix sender verification ---"
sender_restrictions="$(docker compose exec -T postfix postconf -h smtpd_sender_restrictions 2>/dev/null | tr -d '\r' || true)"
if [[ -n "$sender_restrictions" ]] && [[ "$sender_restrictions" != " " ]]; then
    ok "postfix smtpd_sender_restrictions active"
else
    fail "postfix smtpd_sender_restrictions empty — rebuild postfix: docker compose build postfix --no-cache && docker compose up -d postfix"
fi
if docker compose exec -T postfix test -f /etc/postfix/sql/sender-verification.cf 2>/dev/null; then
    ok "postfix sender-verification.cf present"
else
    fail "postfix sender-verification.cf missing"
fi
echo

if [[ "$FAIL" -eq 0 ]]; then
    echo "All critical checks passed."
    exit 0
fi

echo "One or more checks failed."
exit 1
