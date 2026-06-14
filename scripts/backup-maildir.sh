#!/usr/bin/env bash
# Backup maildir volume and PostgreSQL mail DB (aligned with OpenCloud backup cadence).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

BACKUP_ROOT="${BACKUP_ROOT:-/var/backups/km0-mail}"
STAMP="$(date +%Y%m%d-%H%M%S)"
DEST="${BACKUP_ROOT}/${STAMP}"

if [[ ! -f .env ]]; then
    echo "error: .env missing" >&2
    exit 1
fi

# shellcheck disable=SC1091
source .env

mkdir -p "$DEST"

echo "==> PostgreSQL dump"
docker compose exec -T postgres pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
    | gzip -9 > "${DEST}/mail-db-${STAMP}.sql.gz"

echo "==> Maildir archive"
VOL="$(docker volume ls --format '{{.Name}}' | grep '_mail-data$' | head -1)"
if [[ -z "$VOL" ]]; then
    echo "error: mail-data volume not found (is the stack running?)" >&2
    exit 1
fi

docker run --rm \
    -v "${VOL}:/data:ro" \
    -v "${DEST}:/backup" \
    alpine:3.20 \
    sh -c "tar czf /backup/maildir-${STAMP}.tar.gz -C /data ."

echo "==> Rspamd DKIM keys (if present)"
RSPAMD_VOL="$(docker volume ls --format '{{.Name}}' | grep '_rspamd-data$' | head -1)"
if [[ -n "$RSPAMD_VOL" ]]; then
    docker run --rm \
        -v "${RSPAMD_VOL}:/data:ro" \
        -v "${DEST}:/backup" \
        alpine:3.20 \
        sh -c "tar czf /backup/rspamd-${STAMP}.tar.gz -C /data . 2>/dev/null || true"
fi

echo "backup complete: ${DEST}"
ls -lh "$DEST"
