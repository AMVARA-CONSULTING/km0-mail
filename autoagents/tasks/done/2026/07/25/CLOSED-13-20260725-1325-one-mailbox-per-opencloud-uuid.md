---
## Closing summary (TOP)

- **What happened:** Issue #13 required one mailbox per `opencloud_uuid` plus a `contact_email` index to stop duplicate mailboxes and ambiguous SSO lookup.
- **What was done:** Added SQL migration (unique partial index + contact index), made provision-api idempotent/409 on uuid conflict with lookup helpers, and updated CHANGELOG/runbook/docs.
- **What was tested:** Tester PASS — indexes present, no duplicate uuids, provision 201/200/409, lookups OK, no secrets.
- **Why closed:** All acceptance criteria passed under testing.
- **Closed at (UTC):** 2026-07-25 15:11
---

# FEAT-Task: Enforce 1 mailbox per opencloud_uuid + contact_email indexes

## GitHub Issue
- **Number:** #13
- **URL:** https://github.com/AMVARA-CONSULTING/km0-mail/issues/13
- **Labels:** enhancement
- **Coordinates:** opencloud #23 activate-mail; mail #10
- **Priority:** before prod activate CTA

## Problem / goal
No UNIQUE on `mail_accounts.opencloud_uuid` / index on `contact_email` → duplicate mailboxes or ambiguous SSO lookup.

## High-level instructions for coder
1. `./scripts/git-sync-main.sh`
2. SQL migration (IF NOT EXISTS): unique on `opencloud_uuid` WHERE NOT NULL; index `contact_email`
3. provision-api: second mailbox same uuid → return existing or `409`; add lookup helpers
4. CHANGELOG/runbook; FEAT→WIP→UNTESTED

## Acceptance criteria
- [x] Unique uuid enforced; contact indexed
- [x] Duplicate uuid provision safe/idempotent
- [x] No secrets

## Implementation notes (2026-07-25)
- `sql/init/03-registration-schema.sql` + `sql/init/04-one-mailbox-per-uuid.sql`: dedupe legacy duplicate uuids (keep lowest id), then unique partial index + `lower(contact_email)` index
- `scripts/apply-registration-migration.sh` applies `04-…`
- `mail-provision-api`: same uuid+email → `200 exists`; same uuid+other email → `409 uuid_already_linked`; `GET /lookup/by-uuid/…`, `GET /lookup/by-contact/…`
- Docs: CHANGELOG, runbook, opencloud-registration-integration, registration preplan schema section

## Testing instructions

1. Sync and ensure stack is up:
   ```bash
   cd /opt/km0-mail && ./scripts/git-sync-main.sh
   docker compose ps postgres mail-provision-api
   ```

2. Confirm indexes (after migration already applied on this host; re-run is idempotent):
   ```bash
   ./scripts/apply-registration-migration.sh
   docker compose exec -T postgres psql -U mail -d mail -c "\di idx_mail_accounts_opencloud_uuid_unique"
   docker compose exec -T postgres psql -U mail -d mail -c "\di idx_mail_accounts_contact_email"
   docker compose exec -T postgres psql -U mail -d mail -c \
     "SELECT opencloud_uuid, count(*) FROM mail_accounts WHERE opencloud_uuid IS NOT NULL GROUP BY 1 HAVING count(*) > 1;"
   ```
   Expect: both indexes present; no duplicate uuid rows.

3. Rebuild API if needed, then with `MAIL_PROVISION_API_TOKEN` from `.env`:
   ```bash
   docker compose up -d --build mail-provision-api
   set -a; source .env; set +a
   UUID="tester-13-$(date +%s)"
   EMAIL="tester13-${UUID##*-}@km0digital.com"
   # create
   curl -sS -w "\n%{http_code}\n" -X POST http://127.0.0.1:8092/provision \
     -H "Authorization: Bearer $MAIL_PROVISION_API_TOKEN" -H "Content-Type: application/json" \
     -d "{\"email\":\"$EMAIL\",\"password\":\"TmpPass13!\",\"opencloud_uuid\":\"$UUID\",\"mail_mode\":\"km0\",\"contact_email\":\"c+$UUID@gmail.com\",\"send_verification\":false}"
   # expect HTTP 201 status created
   # idempotent
   curl -sS -w "\n%{http_code}\n" -X POST http://127.0.0.1:8092/provision \
     -H "Authorization: Bearer $MAIL_PROVISION_API_TOKEN" -H "Content-Type: application/json" \
     -d "{\"email\":\"$EMAIL\",\"opencloud_uuid\":\"$UUID\",\"mail_mode\":\"km0\",\"send_verification\":false}"
   # expect HTTP 200 status exists
   # conflict
   curl -sS -w "\n%{http_code}\n" -X POST http://127.0.0.1:8092/provision \
     -H "Authorization: Bearer $MAIL_PROVISION_API_TOKEN" -H "Content-Type: application/json" \
     -d "{\"email\":\"other-$EMAIL\",\"opencloud_uuid\":\"$UUID\",\"mail_mode\":\"km0\",\"send_verification\":false}"
   # expect HTTP 409 uuid_already_linked
   curl -sS -H "Authorization: Bearer $MAIL_PROVISION_API_TOKEN" \
     "http://127.0.0.1:8092/lookup/by-uuid/$UUID"
   curl -sS -H "Authorization: Bearer $MAIL_PROVISION_API_TOKEN" \
     "http://127.0.0.1:8092/lookup/by-contact/c+$UUID@gmail.com"
   # cleanup
   docker compose exec -T postgres psql -U mail -d mail -c "DELETE FROM mail_accounts WHERE opencloud_uuid='$UUID';"
   ```

4. Pass when: unique + contact indexes exist, idempotent 200, conflict 409, lookups return the mailbox; no secrets committed.

## Test report

1. **Date/time (UTC) and log window:** 2026-07-25 15:09:59 UTC → 15:10:15 UTC (provision-api exercised 15:10:00–15:10:06Z).
2. **Environment:** compose project `km0-mail` (postgres healthy; mail-provision-api Up; postfix/dovecot/rspamd/roundcube Up); branch `main` @ `abc3c98`; API `http://127.0.0.1:8092`. **Stack ready:** `GET /health` → `{"ok":true}`; polled `https://mail.km0digital.com/` → HTTP/2 302 to Auth Hub; MX `50 mail.km0digital.com.`; A `116.202.10.106`; `nc` open on 25/587/993.
3. **What was tested:** Idempotent registration migration (`04-one-mailbox-per-uuid`); presence of unique uuid + contact_email indexes; no duplicate uuid rows; `/provision` create / exists / conflict; lookup by uuid and by contact; docs mentions; cleanup of disposable row; no secrets in git.
4. **Results:**
   - Unique + contact indexes present — **PASS** (`idx_mail_accounts_opencloud_uuid_unique`, `idx_mail_accounts_contact_email`; migration re-run idempotent)
   - No duplicate `opencloud_uuid` rows — **PASS** (HAVING count(*) > 1 → 0 rows)
   - Provision create → HTTP 201 `status=created` — **PASS** (`tester13-1784992205@km0digital.com`)
   - Idempotent same uuid+email → HTTP 200 `status=exists` — **PASS**
   - Same uuid + other email → HTTP 409 `uuid_already_linked` — **PASS**
   - `GET /lookup/by-uuid/…` and `/lookup/by-contact/…` — **PASS** (mailbox + contact returned)
   - Docs (CHANGELOG/runbook/integration/preplan) — **PASS** (issue #13 / indexes / `uuid_already_linked` documented)
   - No secrets committed — **PASS** (`.env` not staged; only autoagents/task noise in working tree)
5. **Overall:** **PASS**
6. **URLs tested:** `http://127.0.0.1:8092/health`, `/provision`, `/lookup/by-uuid/…`, `/lookup/by-contact/…`; `https://mail.km0digital.com/` (readiness)
7. **Relevant log excerpts:**
   ```
   Migration: NOTICE relation "idx_mail_accounts_opencloud_uuid_unique" already exists, skipping
   Migration: NOTICE relation "idx_mail_accounts_contact_email" already exists, skipping
   POST /provision → 201 created
   POST /provision → 200 exists
   POST /provision → 409 uuid_already_linked (existing_email=tester13-1784992205@km0digital.com)
   GET /lookup/by-uuid/tester-13-1784992205 → 200
   GET /lookup/by-contact/c+tester-13-1784992205@gmail.com → 200
   DELETE FROM mail_accounts … → DELETE 1
   HTTPS mail.km0digital.com/ → 302 location: https://auth.km0digital.com/login?service=mail
   ```
