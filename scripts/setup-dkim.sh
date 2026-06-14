#!/usr/bin/env bash
# Generate Rspamd DKIM key for km0digital.com and print DNS TXT record.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

DOMAIN="${MAIL_DOMAIN:-km0digital.com}"
SELECTOR="${DKIM_SELECTOR:-mail}"

echo "Generating DKIM key for ${DOMAIN} (selector: ${SELECTOR})..."
docker compose exec -T rspamd rspamadm dkim_keygen \
    -d "$DOMAIN" -s "$SELECTOR" -k "/var/lib/rspamd/dkim/${DOMAIN}.${SELECTOR}.key" \
    > /tmp/dkim-dns.txt

echo
echo "Add this DNS TXT record at Joker.com:"
echo "  Host: ${SELECTOR}._domainkey"
cat /tmp/dkim-dns.txt
rm -f /tmp/dkim-dns.txt
