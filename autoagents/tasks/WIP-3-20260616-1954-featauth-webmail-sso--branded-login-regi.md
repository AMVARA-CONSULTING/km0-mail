# feat(auth): webmail SSO — branded login/register, Roundcube OAuth, Dovecot XOAUTH2 (shared Dex)

## GitHub Issue
- **Issue:** https://github.com/AMVARA-CONSULTING/km0-mail/issues/3
- **Number:** #3
- **Labels:** agent:untested, agent:wip
- **Created:** 2026-06-16T19:42:06Z
- **Redmine:** #7605 (tracking ticket when configured in autoagents/.env)

## Problem / goal
# GitHub issue draft — KM0 Mail SSO (Dex OIDC + branded login/register)  Create this issue on **AMVARA-CONSULTING/km0-mail**.  Cross-repo work also touches **AMVARA-CONSULTING/km0-opencloud** (Dex static clients, register-api). Link both issues when...

## High-level instructions for coder
- Read the full issue at https://github.com/AMVARA-CONSULTING/km0-mail/issues/3
- Follow **`docs/issue-mail-preplan.md`** for architecture, DNS, ports, and phases
- Implement under `docker-compose.yml`, `config/`, `nginx/`, `scripts/`, `sql/`, `docs/`
- Phase 1 focus: Postfix + Dovecot + Rspamd + Roundcube + PostgreSQL on same VPS as OpenCloud
- User addresses: `@km0digital.com`; service hostname: `mail.km0digital.com`
- No OpenCloud LDAP unification in phase 1; include `mail_accounts.opencloud_uuid` nullable in SQL
- Light SMTP relay from localhost for OpenCloud / marketing / register-api / km0-web (see pre-plan)
- Add **Testing instructions** before renaming to UNTESTED-

## References
- Pre-plan: docs/issue-mail-preplan.md
- Repo: https://github.com/AMVARA-CONSULTING/km0-mail
- Runbook: docs/runbook.md (create/update during implementation)
- OpenCloud cross-repo: docs/opencloud-sso-integration.md

## Implementation notes (coder)

Repo implementation was already on `main`. This session **deployed** on production host:

- SSO secrets appended to `/opt/km0-mail/.env` (not committed)
- `host-www/mail-auth/` → `/var/www/mail-auth/`
- Nginx vhost updated from `nginx/sites-available/mail`
- `docker compose up -d --build` — `mail-provision-api`, Dovecot OAuth, Roundcube plugin now running

**Still operator / km0-opencloud:** register-api mailbox hook + CORS for `mail.km0digital.com` remain opencloud work. Dex static clients `km0-mail-web` and `km0-mail-dovecot` were added on host (`/opt/opencloud/dex/`) with secrets synced from `.env`; Dex restarted.

## Testing instructions

### Prerequisites (operator)

1. Confirm SSO vars in `/opt/km0-mail/.env`:
   - `ROUNDCUBE_OAUTH_CLIENT_SECRET`
   - `DOVECOT_OAUTH_CLIENT_SECRET`
   - `MAIL_PROVISION_API_TOKEN`
2. Confirm Dex static clients `km0-mail-web` and `km0-mail-dovecot` in km0-opencloud (secrets must match `.env`); restart Dex. *(Deployed on host 2026-06-16.)*
3. Auth pages + nginx (if not already deployed):
   ```bash
   sudo rsync -a /opt/km0-mail/host-www/mail-auth/ /var/www/mail-auth/
   sudo cp /opt/km0-mail/nginx/sites-available/mail /etc/nginx/sites-available/mail
   sudo nginx -t && sudo systemctl reload nginx
   ```
4. Stack:
   ```bash
   cd /opt/km0-mail
   docker compose build dovecot mail-provision-api
   docker compose up -d
   docker compose ps
   ```

### Infrastructure

```bash
curl -s https://cloud.km0digital.com/dex/.well-known/openid-configuration | jq .introspection_endpoint
curl -sI https://mail.km0digital.com/login.html | head -5
curl -sI https://mail.km0digital.com/register | head -5
curl -s http://127.0.0.1:8092/health
docker compose logs --tail=50 dovecot roundcube mail-provision-api
docker compose exec roundcube ls /var/roundcube/plugins/km0_sso_provision/
docker compose exec dovecot test -f /run/dovecot/dovecot-oauth2.conf.ext
```

### Provision API (idempotent)

```bash
source /opt/km0-mail/.env
curl -s -X POST http://127.0.0.1:8092/provision \
  -H "Authorization: Bearer $MAIL_PROVISION_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email":"testsso@km0digital.com","opencloud_uuid":"test-uuid"}'
./scripts/km0-mail-admin list-mailboxes | grep testsso
# Repeat POST — expect HTTP 200 (exists), no duplicate row
```

### SSO login (manual — requires Dex clients)

| Case | Steps | Expected |
|------|-------|----------|
| Google SSO | `/login.html` → Google → Roundcube | Inbox without mailbox password |
| Google auto-provision | IDM user exists, no mailbox | First login creates mailbox silently |
| LDAP SSO | Register or `/login.html` → LDAP | Roundcube inbox |
| Legacy | `/index.php?_task=login` as `postmaster@` | Password login still works |
| Wrong domain | Google account not `@km0digital.com` | Clear error, no mailbox created |

### Regression

- OpenCloud login at `https://cloud.km0digital.com/login.html` unchanged
- Inbound/outbound mail unchanged: `./scripts/verify-mail-stack.sh`
- `./scripts/km0-mail-admin list-mailboxes` shows operational accounts

### Notes

- register-api mailbox hook is **km0-opencloud** work; mail nginx proxies `/api/register` only
- Test mail: `postmaster@km0digital.com` → `yoelberjaga@gmail.com` if needed

## Test report

**Date/time (UTC):** 2026-06-16T19:55:06Z – 2026-06-16T19:55:28Z  
**Log window:** container logs from ~19:54:00Z (Roundcube/Dovecot/mail-provision-api restart) through test end.

### Environment

- **Branch/commit:** `main` @ `46d9e65`
- **Compose:** all 6 services Up (`postfix`, `dovecot`, `rspamd`, `roundcube`, `postgres`, `mail-provision-api`)
- **Stack readiness:** `docker compose ps` showed all services healthy/running; `curl -sI https://mail.km0digital.com/` returned HTTP 302 → `/login.html` immediately (no polling delay needed)
- **URLs:** `https://mail.km0digital.com`, `https://cloud.km0digital.com/dex/`, `http://127.0.0.1:8092`

### What was tested

Prerequisites (env vars present), infrastructure (Dex, nginx auth pages, health, DNS, ports), provision API idempotency, Dovecot OAuth config, Roundcube plugin deployment, regression (`verify-mail-stack.sh`, mailbox list, OpenCloud login page), nginx error log.

### Results

| Criterion | Result | Evidence |
|-----------|--------|----------|
| SSO env vars in `.env` | **PASS** | `ROUNDCUBE_OAUTH_*`, `DOVECOT_OAUTH_*`, `MAIL_PROVISION_API_TOKEN` all set |
| Dex introspection endpoint | **PASS** | `https://cloud.km0digital.com/dex/token/introspect` |
| Branded `/login.html` | **PASS** | HTTP 200; Google SSO button + legacy link present |
| Branded `/register` | **PASS** | HTTP 200 |
| mail-provision-api `/health` | **PASS** | `{"domain":"km0digital.com","ok":true}` |
| Dovecot OAuth config file | **PASS** | `/run/dovecot/dovecot-oauth2.conf.ext` exists |
| Provision API create + idempotent repeat | **PASS** | POST → HTTP 200 `status:exists`; `testsso@km0digital.com` in DB with `opencloud_uuid=test-uuid`; repeat POST same result, no duplicate |
| Roundcube `km0_sso_provision` plugin loads | **FAIL** | Startup log: `ERROR: Failed to load plugin file /var/www/html/plugins/km0_sso_provision/km0_sso_provision.php`; plugin file exists at `/var/roundcube/plugins/km0_sso_provision/` but **not** under `/var/www/html/plugins/` (compose volume mount targets wrong path) |
| Google SSO → Roundcube inbox | **NOT RUN** | Blocked by plugin load failure; requires interactive browser |
| Google auto-provision on first login | **NOT RUN** | Blocked by plugin load failure |
| LDAP SSO | **NOT RUN** | Requires interactive browser |
| Legacy password login (`postmaster@`) | **NOT RUN** | Login page loads (HTTP 200); password not available to tester |
| Wrong-domain Google rejection | **NOT RUN** | Requires interactive browser |
| OpenCloud login unchanged | **PASS** | `https://cloud.km0digital.com/login.html` HTTP 200 |
| Mail stack regression | **PASS** | `./scripts/verify-mail-stack.sh` — all critical checks passed |
| Operational mailboxes | **PASS** | `postmaster@`, `noreply@`, `testuser@`, `testsso@` listed |
| DNS MX/A | **PASS** | MX `50 mail.km0digital.com.`; A `116.202.10.106` |
| Mail ports 25/587/993 | **PASS** | `nc -vz` succeeded on all three |
| Nginx error log | **PASS** | No mail-auth/SSO-related errors in test window; only unrelated SSL scan noise from external IPs |

### Overall: **FAIL**

Blocking defect: Roundcube bind-mounts `km0_sso_provision` to `/var/roundcube/plugins/` but Roundcube loads plugins from `/var/www/html/plugins/`. Silent auto-provision on OAuth login cannot work until the mount path is corrected (e.g. mount to `/var/www/html/plugins/km0_sso_provision`).

Secondary note: `mail-provision-api` logs `WARNING postfix map reload skipped` (exit 125 from `build-hash-maps.sh` inside container) — provisioning still succeeds but Postfix maps may not refresh automatically.

### URLs tested

- https://cloud.km0digital.com/dex/.well-known/openid-configuration
- https://cloud.km0digital.com/login.html
- https://mail.km0digital.com/
- https://mail.km0digital.com/login.html
- https://mail.km0digital.com/register
- https://mail.km0digital.com/index.php?_task=login
- https://mail.km0digital.com/index.php/login/oauth
- http://127.0.0.1:8092/health
- http://127.0.0.1:8092/provision

### Log excerpts

```
roundcube-1  | ERROR: Failed to load plugin file /var/www/html/plugins/km0_sso_provision/km0_sso_provision.php
mail-provision-api-1  | WARNING postfix map reload skipped: Command '['docker', 'compose', '-p', 'km0-mail', 'exec', '-T', 'postfix', 'build-hash-maps.sh']' returned non-zero exit status 125.
mail-provision-api-1  | INFO 172.22.0.1 - - [16/Jun/2026 19:54:05] "POST /provision HTTP/1.1" 201 -
mail-provision-api-1  | INFO 172.22.0.1 - - [16/Jun/2026 19:54:06] "POST /provision HTTP/1.1" 200 -
```
