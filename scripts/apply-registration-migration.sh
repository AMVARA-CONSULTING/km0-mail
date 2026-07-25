#!/usr/bin/env bash
# Apply registration schema migration on an existing PostgreSQL volume (non-destructive).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
    echo "error: .env missing" >&2
    exit 1
fi

# shellcheck disable=SC1091
source .env

echo "Applying registration schema migration (existing data preserved)..."
docker compose exec -T postgres psql -v ON_ERROR_STOP=1 -U "${POSTGRES_USER:-mail}" -d "${POSTGRES_DB:-mail}" \
    < "${ROOT}/sql/init/03-registration-schema.sql"

echo "Applying one-mailbox-per-uuid indexes (issue #13)..."
docker compose exec -T postgres psql -v ON_ERROR_STOP=1 -U "${POSTGRES_USER:-mail}" -d "${POSTGRES_DB:-mail}" \
    < "${ROOT}/sql/init/04-one-mailbox-per-uuid.sql"

echo "Migration complete. Reload Postfix maps:"
echo "  docker compose exec postfix build-hash-maps.sh"
