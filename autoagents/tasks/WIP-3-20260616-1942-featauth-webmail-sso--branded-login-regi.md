# feat(auth): webmail SSO — branded login/register, Roundcube OAuth, Dovecot XOAUTH2 (shared Dex)

## GitHub Issue
- **Issue:** https://github.com/AMVARA-CONSULTING/km0-mail/issues/3
- **Number:** #3
- **Labels:** none
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

## Testing instructions

### Prerequisites (operator)

1. Add to `/opt/km0-mail/.env` (generate secrets with `openssl rand -hex 32`):
   - `ROUNDCUBE_OAUTH_CLIENT_SECRET`
   - `DOVECOT_OAUTH_CLIENT_SECRET`
   - `MAIL_PROVISION_API_TOKEN`
2. Add Dex static clients `km0-mail-web` and `km0-mail-dovecot` in km0-opencloud (see `docs/opencloud-sso-integration.md`); restart Dex.
3. Deploy auth pages and nginx:
   ```bash
   sudo rsync -a /opt/km0-mail/host-www/mail-auth/ /var/www/mail-auth/
   sudo cp /opt/km0-mail/nginx/sites-available/mail /etc/nginx/sites-available/mail
   sudo nginx -t && sudo systemctl reload nginx
   ```
4. Rebuild stack:
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

**Date/time (UTC):** 2026-06-16T19:45:51Z – 2026-06-16T19:46:23Z  
**Log window:** container logs `--tail=100` postfix/dovecot/rspamd/roundcube; nginx error.log last 50 lines  
**Environment:** `main` branch (synced), compose project `km0-mail`, host `mail.km0digital.com` (116.202.10.106)  
**Stack readiness:** Polled `https://mail.km0digital.com/` → HTTP 200; ports 25/587/993 open; core containers Up 2 days. SSO-specific services/config **not** deployed.

### What was tested

- Prerequisites checklist (`.env` SSO vars, nginx deploy, auth pages, `mail-provision-api`)
- Infrastructure (Dex OIDC, branded auth URLs, provision API health)
- Container SSO artifacts (Roundcube plugin, Dovecot OAuth)
- Regression (`verify-mail-stack.sh`, mailbox list, OpenCloud login)

### Results

| Criterion | Result | Evidence |
|-----------|--------|----------|
| `.env` SSO secrets (`ROUNDCUBE_OAUTH_*`, `DOVECOT_OAUTH_*`, `MAIL_PROVISION_API_TOKEN`) | **FAIL** | Vars absent from `/opt/km0-mail/.env` |
| Auth pages deployed (`/var/www/mail-auth/`) | **FAIL** | `ls: cannot access '/var/www/mail-auth/': No such file or directory` |
| Nginx SSO routes deployed | **FAIL** | `/etc/nginx/sites-available/mail` dated 2026-06-14; no `login.html`/`mail-auth` blocks (repo template has them) |
| `mail-provision-api` container running | **FAIL** | Absent from `docker compose ps`; `curl http://127.0.0.1:8092/health` → connection refused |
| Dex introspection endpoint | **PASS** | `https://cloud.km0digital.com/dex/token/introspect` |
| `https://mail.km0digital.com/login.html` | **FAIL** | HTTP 404 |
| `https://mail.km0digital.com/register` | **FAIL** | HTTP 403 (proxied to Roundcube; no static register page) |
| `https://mail.km0digital.com/dex-auth.js` | **FAIL** | HTTP 404 |
| Roundcube `km0_sso_provision` plugin mounted | **FAIL** | `ls: cannot access '/var/roundcube/plugins/km0_sso_provision/'` in running container |
| Dovecot OAuth config | **FAIL** | `/etc/dovecot/dovecot-oauth2.conf.ext` missing in running container |
| Provision API idempotent POST | **FAIL** | Blocked — service not listening on 8092 |
| SSO login flows (Google/LDAP/auto-provision/wrong-domain) | **FAIL** | Blocked — prerequisites undeployed |
| Legacy Roundcube password login page | **PASS** | `https://mail.km0digital.com/index.php?_task=login` → HTTP 200 |
| OpenCloud login regression | **PASS** | `https://cloud.km0digital.com/login.html` → HTTP 200 |
| Mail stack regression (`verify-mail-stack.sh`) | **PASS** | All critical checks passed (postgres/postfix/dovecot/rspamd/roundcube, ports, DNS, schema) |
| Operational mailboxes | **PASS** | `postmaster@`, `noreply@`, `testuser@` active |
| DNS MX/A | **PASS** | MX `50 mail.km0digital.com.`; A `116.202.10.106` |
| SMTP/IMAP ports | **PASS** | `nc -vz` succeeded on 25, 587, 993 |

**Overall: FAIL**

SSO implementation exists in repo (`host-www/mail-auth/`, updated `nginx/sites-available/mail`, `docker/mail-provision-api/`, Roundcube plugin, Dovecot OAuth template) but **operator prerequisites were not applied** on the production host. Running stack is the pre-SSO deployment from 2026-06-14.

### URLs tested

- https://mail.km0digital.com/
- https://mail.km0digital.com/login.html
- https://mail.km0digital.com/register
- https://mail.km0digital.com/dex-auth.js
- https://mail.km0digital.com/index.php?_task=login
- https://cloud.km0digital.com/login.html
- https://cloud.km0digital.com/dex/.well-known/openid-configuration
- http://127.0.0.1:8092/health

### Relevant log excerpts

```
# docker compose ps — mail-provision-api absent
NAME                   STATUS
km0-mail-dovecot-1     Up 2 days
km0-mail-postfix-1     Up 2 days
km0-mail-postgres-1    Up 2 days (healthy)
km0-mail-roundcube-1   Up 2 days
km0-mail-rspamd-1      Up 2 days

# provision API health
curl http://127.0.0.1:8092/health → connect failed: Connection refused

# verify-mail-stack.sh
All critical checks passed.

# Roundcube container
ls: cannot access '/var/roundcube/plugins/km0_sso_provision/': No such file or directory

# Dovecot container
dovecot oauth config missing
```

### Remediation required before retest

1. Set SSO secrets in `/opt/km0-mail/.env`.
2. Configure Dex static clients in km0-opencloud (`km0-mail-web`, `km0-mail-dovecot`).
3. Deploy auth pages and nginx per Testing instructions §Prerequisites steps 3–4.
4. Rebuild and start `dovecot` + `mail-provision-api`; confirm `docker compose ps` shows `mail-provision-api` and port 8092 healthy.

