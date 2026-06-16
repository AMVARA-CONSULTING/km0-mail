# feat(auth): webmail SSO — branded login/register, Roundcube OAuth, Dovecot XOAUTH2 (shared Dex)

## GitHub Issue
- **Issue:** https://github.com/AMVARA-CONSULTING/km0-mail/issues/3
- **Number:** #3
- **Labels:** agent:untested
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

Repo implementation on `main`. This session **fixed blocking defects** from prior test run:

1. **Roundcube plugin mount** — `docker-compose.yml` now mounts `km0_sso_provision` to `/var/www/html/plugins/km0_sso_provision` (Roundcube loads plugins from `/var/www/html/plugins/`, not `/var/roundcube/plugins/`).
2. **Postfix map reload** — `mail-provision-api` uses `docker exec km0-mail-postfix-1 build-hash-maps.sh` instead of `docker compose exec` (compose CLI unavailable inside API container).

Prior deployment (operator): SSO secrets in `.env`, Dex static clients, nginx auth pages, stack running.

**Still operator / km0-opencloud:** register-api mailbox hook + CORS for `mail.km0digital.com` remain opencloud work.

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
docker compose exec roundcube ls /var/www/html/plugins/km0_sso_provision/
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
- Verify Roundcube logs show **no** `Failed to load plugin file ... km0_sso_provision` after `docker compose up -d roundcube`
