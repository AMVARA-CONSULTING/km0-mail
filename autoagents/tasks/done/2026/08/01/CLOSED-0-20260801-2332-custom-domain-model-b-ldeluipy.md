---
## Closing summary (TOP)

- **What happened:** Custom-domain (Model B) support was made fully functional — inbound delivery, native login, and per-domain DKIM-signed outbound — so a verified customer domain can be onboarded end-to-end.
- **What was done:** Added an idempotent `dkim_private_key` migration, made `domain-verify-api` persist both keys and materialize the private key into Rspamd on activation (with reload), opened a public rate-limited `/check`, and documented the operator onboarding runbook; nothing domain-specific hardcoded.
- **What was tested:** Migration present, custom register creates pending domain+mailbox, wizard `/status` generates+persists both keys, public `/check` (200/401/404), DKIM materialization + Rspamd reload (0600 `_rspamd`), Postfix accepts active domains, custom-domain login (`doveadm auth` succeeds), docs updated, no secrets, stack health passes.
- **Why closed:** All automatable acceptance criteria passed; tester reported Overall PASS (final `ldeluipy.es` live DNS flip remains an operator step, as scoped).
- **Closed at (UTC):** 2026-08-02 00:02
---

# FEAT: Custom-domain (Model B) readiness — unblock ldeluipy.es

## GitHub Issue
- **Issue:** N/A (local FEAT, no GitHub issue — generated directly)
- **Number:** #0
- **Redmine:** #7605 (tracking)
- **Priority:** high (end goal that unblocks ldeluipy.es)
- **Depends on:** FEAT native-login-canonical, self-contained-registration, verification-first-login

## Problem / goal
The concrete objective behind the whole login-simplification effort is to run a customer-owned domain, `ldeluipy.es`, on this stack (Model B). Today the pieces are half-wired:
- Per-domain DKIM signing is NOT real: `config/rspamd/local.d/dkim_signing.conf` hardcodes ONLY `km0digital.com`.
- Postfix accepted domains are not driven end-to-end from the `mail_domains` table for custom domains (verification flips `active=true` but signing/postfix maps may not follow).
- The DNS wizard (`domain.html` + `domain-verify-api`) verifies TXT/MX/SPF/DKIM but the DKIM private key for a custom domain is not provisioned into Rspamd for actual outbound signing.

**Goal:** make a verified custom domain fully functional — inbound delivery, native login for `user@customdomain`, and DKIM-signed outbound — so `ldeluipy.es` can be integrated by the operator right after.

## Current state (files)
- `config/rspamd/local.d/dkim_signing.conf`: single `domain { km0digital.com { path=...; selector="mail"; } }`; generic `path = "/var/lib/rspamd/dkim/$domain.$selector.key"` is present but no per-domain key material for customs.
- `docker/domain-verify-api/app.py`:
  - Generates a DKIM keypair (`generate_dkim_keypair()`), stores only the PUBLIC key (`dkim_public_key`) in `mail_domains`, checks DNS (TXT/MX/SPF/DKIM), flips `active=true` + `verification_status=verified` when all pass, and calls `reload_postfix_maps()`.
  - Does NOT persist the DKIM PRIVATE key into Rspamd's key store, so outbound signing for the custom domain cannot happen.
- `docker/mail-provision-api/app.py`: `provision_mailbox` inserts the `mail_domains` pending row for `mail_mode=custom`.
- Postfix maps: `docker/postfix/build-hash-maps.sh` + `config/postfix/sql-templates/virtual-mailbox-domains.cf` (DB-driven virtual domains).
- `sql/init/03-registration-schema.sql`: `mail_domains` has `dkim_selector`, `dkim_public_key`, verification flags.
- SQL schema note: `mail_domains` currently has no `dkim_private_key` column.

## High-level instructions for coder
1. Run `./scripts/git-sync-main.sh` before edits.
2. **Persist the DKIM private key** so custom domains can actually sign outbound:
   - Add a `dkim_private_key TEXT` column to `mail_domains` via an idempotent migration in `sql/init/` (follow the `IF NOT EXISTS` pattern of `03-registration-schema.sql`). Store the private PEM there (it is already in a trusted DB).
   - In `domain-verify-api` `generate_dkim_keypair()` usage, store BOTH private and public keys when a custom domain first generates its key.
3. **Wire per-domain DKIM into Rspamd** on activation:
   - When a domain becomes `active`, materialize its private key to `/var/lib/rspamd/dkim/<domain>.<selector>.key` (path already referenced by `dkim_signing.conf`'s `$domain.$selector.key`) and ensure `dkim_signing.conf` signs for active custom domains (either via the generic path map keyed by header domain, or by rendering per-domain blocks). Prefer the generic `$domain.$selector.key` map so no per-domain config block is needed. Reload Rspamd.
   - Confirm `use_domain = "header"` + `check_pubkey` behavior is compatible; document the reload step.
4. **Postfix accepted domains** for customs:
   - Ensure `virtual-mailbox-domains.cf` / `build-hash-maps.sh` accept `active=true` custom domains from `mail_domains` so inbound for `@customdomain` is delivered (not rejected). Verify `reload_postfix_maps()` picks them up on activation.
5. **Native custom-domain signup + login** (glue to earlier FEATs):
   - Confirm the native `/api/register` `custom` flow (FEAT self-contained-registration) creates the pending domain + mailbox, redirects to `/domain.html?domain=...`, and that after DNS verification the user logs in with password at the native login for `user@customdomain`.
6. Update `docs/runbook.md` with an operator runbook for onboarding a custom domain end-to-end (register → DNS wizard → verify → outbound signs), and a short `ldeluipy.es` example. Update `docs/CHANGELOG.md`.
7. Do NOT hardcode `ldeluipy.es` anywhere — keep it generic/DB-driven. No secrets committed (private keys live in DB/volume, never in git).

## Implementation summary
- `sql/init/05-custom-domain-dkim.sql`: idempotent `ALTER TABLE mail_domains ADD COLUMN IF NOT EXISTS dkim_private_key TEXT`; wired into `scripts/apply-registration-migration.sh`.
- `docker/domain-verify-api/app.py`:
  - `ensure_domain_keys()` generates + persists **both** public (DNS value) and private (PEM) keys when missing; called from `GET /status` (so the wizard shows a real DKIM record on first load) and `POST /check`.
  - `materialize_dkim_key()` writes the private key into Rspamd via `docker exec -i <rspamd> sh -c 'umask 077; ... cat > /var/lib/rspamd/dkim/<domain>.<selector>.key'` (runs as `_rspamd` → `0600`, correct owner), then `reload_rspamd()` (SIGHUP to PID 1). Called on verification alongside `reload_postfix_maps()`.
  - `POST /check` is now usable by the public DNS wizard: auth optional (a supplied Bearer token must still be valid) + per-IP rate limit (`CHECK_RATE_MAX`/`CHECK_RATE_WINDOW_SEC`). This unblocks the wizard's "Check again" button (was `401`).
  - Selector sanitized (`SELECTOR_RE`) before shell interpolation; domain already validated by `DOMAIN_RE`.
- No `dkim_signing.conf` change needed: the existing generic `$domain.$selector.key` map signs any domain that has a key file. No domain hardcoded.

## Acceptance criteria
- [x] `mail_domains` has `dkim_private_key` (idempotent migration) and `domain-verify-api` stores both keys on first generation.
- [x] Registering `user@<customdomain>` (custom mode) creates a pending `mail_domains` row and a mailbox; front-end continues to `/domain.html?domain=<customdomain>`.
- [x] The DNS wizard verifies TXT/MX/SPF/DKIM and flips the domain to `active=true` / `verified` (mechanism verified: public `/check` returns per-record checks and, on `all_verified`, sets `active`/`verified`; final flip needs real DNS the operator controls — see `ldeluipy.es` step below).
- [x] After activation: inbound mail to `@<customdomain>` is accepted/delivered — Postfix `virtual_mailbox_domains` hash is rebuilt from `active=TRUE` rows by `build-hash-maps.sh` on `reload_postfix_maps()`.
- [x] After activation: outbound from `user@<customdomain>` is DKIM-signed with the domain's own key — private key materialized to `/var/lib/rspamd/dkim/<domain>.mail.key` and Rspamd reloaded (verified below); actual header `d=<domain>` requires sending from the verified domain (operator smoke).
- [x] `user@<customdomain>` can log in at the native login with email+password (Dovecot SQL passdb; mailbox created active with bcrypt hash).
- [x] Runbook has an end-to-end custom-domain onboarding section incl. an `ldeluipy.es` example; CHANGELOG updated.
- [x] No domain hardcoding; no secrets committed; `./scripts/verify-mail-stack.sh` passes.

## Testing instructions

Coder ran the following on the live stack with a **disposable** test domain
(`km0e2etest.org`, cleaned up afterwards). Real output inline. For the true end goal,
repeat steps 2–6 with `ldeluipy.es` once the operator can set its DNS.

1. **Migration applied** — `dkim_private_key` column present:
   ```bash
   ./scripts/apply-registration-migration.sh   # ... "Applying custom-domain DKIM private key column..." -> ALTER TABLE
   docker compose exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c \
     "SELECT column_name FROM information_schema.columns WHERE table_name='mail_domains' AND column_name IN ('dkim_private_key','dkim_public_key','dkim_selector');"
   ```
   → returns `dkim_private_key`, `dkim_public_key`, `dkim_selector` (3 rows).

2. **Custom register** creates pending domain + mailbox:
   ```bash
   curl -s -X POST http://127.0.0.1:8092/register -H 'Content-Type: application/json' \
     -d '{"email":"admin@km0e2etest.org","mail_mode":"custom","password":"<redacted>"}'
   ```
   → `{"continue_to":"/domain.html?domain=km0e2etest.org","domain":"km0e2etest.org","mail_mode":"custom","ok":true,"status":"created","verification_status":"pending"}`
   DB: `mail_domains` row `active=f verification_status=pending` (pub=f priv=f before wizard); `mail_accounts admin@km0e2etest.org active=t mail_mode=custom`.

3. **Wizard first load** (`GET /status`) generates + persists BOTH keys and shows the DKIM record:
   ```bash
   curl -s http://127.0.0.1:8093/domain/km0e2etest.org/status | python3 -m json.tool
   ```
   → `dns.dkim.value = "v=DKIM1; k=rsa; p=MIIBIjANBgkq..."` (real key, not "(generating...)").
   DB after: `pub=t priv=t`, `dkim_private_key` starts `-----BEGIN PRIVATE KEY-----`.

4. **Wizard "Check again"** (`POST /check`) — public, rate-limited; Bearer optional but validated:
   ```bash
   curl -s -o /dev/null -w '%{http_code}\n' -X POST http://127.0.0.1:8093/domain/km0e2etest.org/check          # 200 (was 401)
   curl -s -o /dev/null -w '%{http_code}\n' -X POST -H 'Authorization: Bearer wrong' .../check                  # 401
   curl -s -o /dev/null -w '%{http_code}\n' -X POST http://127.0.0.1:8093/domain/doesnotexist-km0.org/check     # 404
   ```
   → `200` unauth (checks all false — test box does not control the domain's DNS), `401` bad token, `404` unknown domain.

5. **Materialization + Rspamd reload** (verified from inside the real `domain-verify-api` container):
   ```bash
   docker compose exec -T domain-verify-api python3 -c "import app,psycopg2;c=psycopg2.connect(**app.DB).cursor();c.execute(\"SELECT dkim_selector,dkim_private_key FROM mail_domains WHERE name='km0e2etest.org'\");s,p=c.fetchone();print(app.materialize_dkim_key('km0e2etest.org',s,p))"
   docker compose exec -T rspamd ls -l /var/lib/rspamd/dkim/
   ```
   → `materialize_dkim_key -> True`; file `km0e2etest.org.mail.key` present, `-rw------- _rspamd _rspamd`; Rspamd logged a config reload (SIGHUP) and stayed `Up` (in-process reload, not a restart).

6. **Postfix accepts the active domain** (mechanism): `build-hash-maps.sh` selects `WHERE active=TRUE` into `hash:/etc/postfix/virtual-mailbox-domains`; `reload_postfix_maps()` runs it on activation. After a real `ldeluipy.es` activation:
   ```bash
   docker compose exec postfix postmap -q ldeluipy.es hash:/etc/postfix/virtual-mailbox-domains   # -> OK
   ```

7. **Stack smoke test**: `./scripts/verify-mail-stack.sh` → "All critical checks passed." (exit 0).

8. **Operator end goal (`ldeluipy.es`)** — repeat 2–4 with `ldeluipy.es`, publish the 4 DNS records from the wizard, click **Check again** until all four are OK (domain flips `active`/`verified`, key materialized). Then sign in as `admin@ldeluipy.es` (password) and send a test mail; confirm `DKIM-Signature: ... d=ldeluipy.es` in the received headers.

## Test report (tester)

- **Date/time (UTC):** 2026-08-01 23:56–23:58 UTC.
- **Environment:** live VPS stack, `docker compose` project `km0-mail`; `mail-provision-api` :8092, `domain-verify-api` :8093, Postfix, Rspamd, Postgres; branch `main` (synced). Disposable test domain `km0e2e-1785628646.org` (created + fully cleaned up afterwards).
- **What was tested:** DKIM private-key migration, custom register → pending domain+mailbox, wizard key generation (`/status`), public rate-limited `/check`, DKIM materialization + Rspamd reload, Postfix accepted-domain mechanism (reversible), custom-domain login, and docs.

### Results
- **Migration (`dkim_private_key`) — PASS.** `apply-registration-migration.sh` ran (idempotent `ALTER TABLE`); `information_schema` shows `dkim_private_key`, `dkim_public_key`, `dkim_selector` (3 columns).
- **Custom register creates pending domain + mailbox — PASS.** `admin@km0e2e-…org` → `{"ok":true,"continue_to":"/domain.html?domain=…","verification_status":"pending"}`; `mail_domains` `active=f, pending, pub=f, priv=f` (pre-wizard); `mail_accounts` `active=t, mail_mode=custom`.
- **Wizard `/status` generates + persists BOTH keys — PASS.** DKIM value = `v=DKIM1; k=rsa; p=MIIBIjANBgkq…` (real key, not placeholder); DB after: `pub=t, priv=t`, `dkim_private_key` begins `-----BEGIN PRIVATE KEY-----`.
- **Public `/check` (rate-limited, Bearer optional-but-validated) — PASS.** no-auth → `200`, bad Bearer → `401`, unknown domain → `404`.
- **DKIM materialization + Rspamd reload — PASS.** `materialize_dkim_key(...) -> True`; file `/var/lib/rspamd/dkim/km0e2e-….org.mail.key` present `-rw------- _rspamd _rspamd` (0600, correct owner); Rspamd stayed `Up` (SIGHUP in-process reload, not a restart).
- **Postfix accepts `active=true` custom domain — PASS (reversible).** Before: domain not in `virtual-mailbox-domains`. After `UPDATE active=TRUE` + `build-hash-maps.sh`: `postmap -q <domain>` → `OK`. Reverted to `active=FALSE` + rebuild → not present again (clean). Confirms `reload_postfix_maps()` path (`SELECT name … WHERE active=TRUE`).
- **Custom-domain native login — PASS.** `doveadm auth test admin@km0e2e-….org` → `auth succeeded`; DB `password_hash` scheme `{BLF-CR}` (bcrypt), created active.
- **Docs — PASS.** `docs/runbook.md` has "## Custom domain onboarding (Model B, end-to-end)" with an `ldeluipy.es` walkthrough (register → wizard → verify → inbound/outbound DKIM → login); `docs/CHANGELOG.md` documents the `dkim_private_key` migration + per-domain signing.
- **No domain hardcoding / no secrets — PASS.** `grep -RniE 'ldeluipy'` across `docker/ config/ sql/ scripts/ host-www/ nginx/` → no matches (only docs reference it). Private keys live in DB/volume, not git.
- **Stack health — PASS.** `verify-mail-stack.sh` → "All critical checks passed." (exit 0).

- **Overall: PASS.** (Automated/mechanism-level verification complete on a disposable domain. The true end goal — `ldeluipy.es` DNS flip to `active`/`verified` and a live `d=ldeluipy.es` DKIM header — remains an operator step requiring the customer's real DNS, as the FEAT itself scopes.)
- **URLs/endpoints tested:** `http://127.0.0.1:8092/register`, `http://127.0.0.1:8093/domain/<d>/status`, `.../check`; Postfix/Rspamd/Postgres via `docker compose exec`.
- **Evidence:** rspamd key `-rw------- 1 _rspamd _rspamd … km0e2e-….org.mail.key`; `postmap -q` → `OK` when active; `doveadm auth … auth succeeded`.

### Cleanup
Disposable test domain fully removed: `DELETE FROM mail_accounts/mail_domains`, rspamd key file removed, Postfix maps rebuilt clean (`postmap -q` no longer resolves the test domain).
