# GitHub issue draft — KM0 Mail SSO (Dex OIDC + branded login/register)

> **Status: DEFERRED / REVERTED (2026-06-16)**  
> Issue #3 was implemented and rolled back. The external `/login.html` wrapper did not replace Roundcube’s login UI; register returned 403 (register-api CORS). Do **not** re-implement from this draft without a revised plan.  
> **Next step:** [`github-issue-roundcube-login-ui.md`](github-issue-roundcube-login-ui.md) — style Roundcube’s native login first.

Create this issue on **AMVARA-CONSULTING/km0-mail** only when revisiting full SSO.

Cross-repo work also touches **AMVARA-CONSULTING/km0-opencloud** (Dex static clients, register-api). Link both issues when implementing.

---

## Title

```
feat(auth): webmail SSO — branded login/register, Roundcube OAuth, Dovecot XOAUTH2 (shared Dex)
```

## Labels

- `enhancement`

(autoagents will add `agent:planned` when picked up)

---

## Issue body

Copy everything below this line into the GitHub issue description.

---

## Summary

Add **full webmail SSO** for `mail.km0digital.com` by reusing the existing Dex OIDC issuer at `cloud.km0digital.com/dex` (same pattern as OpenCloud). Deliver:

1. **Branded login and register pages** (KM0 Cloud visual style — reuse/adapt `opencloud-auth/`).
2. **Self-registration** that creates an **OpenCloud IDM user** and a **mailbox** `@km0digital.com`.
3. **Silent mailbox auto-provision** on first webmail SSO login (Google or LDAP) when the user has IDM identity but no mailbox yet.
4. **Roundcube OAuth2** against Dex (Google + LDAP connectors).
5. **Dovecot XOAUTH2** so Roundcube can authenticate IMAP/SMTP with OAuth access tokens (no separate mail password for SSO users).

This lays the foundation for **KM0-wide SSO**: future services only need a new Dex static client and optional provisioning hook — same model as Google (one identity, many apps).

**Do not** deploy a second Dex on `mail.km0digital.com`. **Do not** wire Google OAuth directly on the mail hostname.

---

## Product decisions (fixed)

| Decision | Value |
|----------|--------|
| IdP | **Reuse** Dex at `https://cloud.km0digital.com/dex` |
| Mail hostname | `mail.km0digital.com` (webmail only) |
| User email domain | `@km0digital.com` (not `@mail.km0digital.com`) |
| Registration | **Public** — email + password; same uid model as OpenCloud (`email` as username) |
| Registration side effects | Create **IDM user** (register-api) **and** **mailbox** (`mail_accounts` + Maildir) |
| Google login | Via Dex `connector_id=google` (unchanged connector) |
| LDAP login | Via Dex `connector_id=ldap` (OpenCloud IDM) |
| Email verification on register | **None** for now (phase 1b item in mail pre-plan) |
| Legacy auth | Keep **SQL password** passdb for operational mailboxes (`postmaster@`, `noreply@`, CLI-provisioned) |
| Native IMAP clients (Thunderbird, Apple Mail) | **Out of scope** — continue app-password / classic auth until a separate project |
| Pricing notice on register | Same disclaimer as OpenCloud register (testing, free for now, pricing link per locale) |
| **Google SSO, no mailbox yet** | **Silent auto-provision** — on first successful webmail OAuth login, create `mail_accounts` + Maildir + `opencloud_uuid` automatically (no extra confirmation screen) |
| Auto-provision email domain | Only when OIDC `email` claim is `@km0digital.com` (matches mail stack policy); other domains → clear error (do not create mailbox) |

---

## Architecture

```
Register:
  mail.km0digital.com/register
    → POST /api/register (nginx proxy → register-api)
    → Graph API → OpenCloud IDM user
    → mail provision hook → mail_accounts + Maildir + opencloud_uuid

Login (webmail SSO):
  mail.km0digital.com/login.html
    → cloud.km0digital.com/dex/auth?client_id=km0-mail-web&connector_id=google|ldap&…
    → Google OR LDAP (Dex)
    → cloud.km0digital.com/dex/callback        ← Google redirect (unchanged)
    → mail.km0digital.com/index.php/login/oauth
    → if no mailbox for email@km0digital.com: silent auto-provision (mail_accounts + Maildir + opencloud_uuid)
    → Roundcube session
    → Dovecot IMAP/SMTP via XOAUTH2 (token introspection against Dex)

Legacy / admin:
  plain login → Dovecot SQL passdb (unchanged)
```

### OAuth redirect chains (important)

| Step | URL | Validated by |
|------|-----|--------------|
| Google → Dex | `https://cloud.km0digital.com/dex/callback` | **Google Cloud Console** |
| Dex → Roundcube | `https://mail.km0digital.com/index.php/login/oauth` | **Dex static client** (`km0-mail-web`) |
| Dovecot token check | `https://cloud.km0digital.com/dex/token/introspect` | **Dex confidential client** (`km0-mail-dovecot`) |

The mail hostname **does not** appear in Google Cloud Console redirect URIs when Dex is shared.

---

## Operator actions (human prerequisites)

### Google Cloud Console — **no change expected**

If Dex remains on `cloud.km0digital.com` with the existing Google connector, **do not add** `mail.km0digital.com` redirect URIs.

**Verify only** that the OAuth client already has:

| Setting | Value |
|---------|--------|
| Authorized redirect URI | `https://cloud.km0digital.com/dex/callback` |
| Authorized JavaScript origins (if listed) | `https://cloud.km0digital.com` |

Docs: [Dex — Google connector](https://dexidp.io/docs/connectors/google/) · [Google OAuth 2.0 setup](https://developers.google.com/identity/protocols/oauth2/web-server#creatingcred)

If you see `redirect_uri_mismatch` from **Google**, the Console list does not match Dex’s connector `redirectURI` — not a mail-specific problem.

### Operator **must** do (during/after implementation)

| # | Action | Owner |
|---|--------|-------|
| 1 | **Generate and store secrets** for Dex clients `km0-mail-web` (Roundcube) and `km0-mail-dovecot` (introspection) in host secrets / `.env` — never commit | Operator |
| 2 | **Deploy nginx** mail vhost changes on VPS (`/etc/nginx/sites-available/mail`) and reload nginx | Operator |
| 3 | **Deploy static auth pages** to `/var/www/mail-auth/` on the host | Operator |
| 4 | **Restart Dex** after `config.yaml` / static client changes (`km0-opencloud/dex`) | Operator |
| 5 | **Recreate/restart** Roundcube + Dovecot containers after config changes | Operator |
| 6 | **Confirm** `register-api` `ALLOWED_ORIGIN` includes `https://mail.km0digital.com` (or proxy `/api/register` from mail nginx to avoid CORS) | Operator |
| 7 | **Smoke-test** login with Google, LDAP, and legacy admin mailbox | Operator |
| 8 | **Optional:** add DNS record only if introducing a dedicated auth host later (e.g. `auth.km0digital.com`) — **not required** for this issue | Operator |

### Operator **does not** need to do

- Add `mail.km0digital.com` to Google OAuth redirect URIs (unless a separate Dex is deployed on mail — explicitly out of scope).
- Create a new Google OAuth client for mail.
- Change MX, SPF, DKIM, or PTR records for this feature.

---

## Implementation scope

### km0-opencloud (sibling repo)

| Item | Details |
|------|---------|
| Dex `staticClients` | Add `km0-mail-web` (public or confidential per Roundcube needs) with redirect `https://mail.km0digital.com/index.php/login/oauth` |
| Dex `staticClients` | Add `km0-mail-dovecot` (confidential) for RFC 7662 introspection used by Dovecot |
| `register-api` | Extend or add hook to provision mailbox after IDM user creation; set `opencloud_uuid` |
| `register-api` `.env` | Allow `https://mail.km0digital.com` origin (or document nginx proxy pattern) |
| Docs | Update `dex/README.md` and `docs/runbook.md` |

Shared **mailbox provisioning** logic (register hook + OAuth auto-provision) should live in one place (script or localhost API) to avoid duplication.

Reference implementation:

- `host-www/opencloud-auth/login.html`, `register.html`, `dex-auth.js`
- `dex/config.yaml`, `nginx/snippets/opencloud-locations.conf`
- `docs/github-issue-self-registration.md`

### km0-mail (this repo)

| Item | Details |
|------|---------|
| `host-www/mail-auth/` | Branded login + register (adapt OpenCloud HTML/CSS/JS; point `authority` to `https://cloud.km0digital.com/dex`) |
| `nginx/sites-available/mail` | Serve `/login.html`, `/register`, `/dex-auth.js`; proxy `/api/register`; optional unauthenticated redirect to login |
| Roundcube `config.inc.php` | Enable OAuth2 generic provider; `oauth_config_uri` → Dex discovery; `oauth_login_redirect` |
| Dovecot | Dual passdb: `oauth2` (XOAUTH2/OAUTHBEARER) + `sql` (plain/login legacy); introspection against Dex |
| Postfix | SASL via Dovecot — should inherit OAuth-capable auth once Dovecot is updated |
| Scripts / API | Mailbox provisioning callable from register hook **and** post-OAuth auto-provision (`km0-mail-admin` wrapper or HTTP API on localhost) |
| Post-OAuth hook | After Roundcube OAuth success: if `@km0digital.com` email has IDM session but no mailbox → silent auto-provision, then continue IMAP login |
| Docs | Update `docs/runbook.md`; link from README |

Reference: [`docs/issue-mail-preplan.md`](docs/issue-mail-preplan.md) phase 2 identity link via `opencloud_uuid`.

---

## Key configuration snippets (reference)

### Roundcube OAuth (indicative)

See [Roundcube OAuth2 configuration](https://github.com/roundcube/roundcubemail/wiki/Configuration:-OAuth2).

```php
$config['oauth_provider'] = 'generic';
$config['oauth_provider_name'] = 'KM0 Mail';
$config['oauth_client_id'] = 'km0-mail-web';
$config['oauth_client_secret'] = '…'; // from operator secrets
$config['oauth_config_uri'] = 'https://cloud.km0digital.com/dex/.well-known/openid-configuration';
$config['oauth_scope'] = 'openid profile email';
$config['oauth_identity_fields'] = ['email'];
$config['oauth_cache'] = 'db';
$config['oauth_login_redirect'] = true;
```

Roundcube redirect URI registered in Dex: `https://mail.km0digital.com/index.php/login/oauth`

### Dovecot OAuth2 (indicative)

See [Dovecot OAuth2 passdb](https://doc.dovecot.org/main/core/config/auth/databases/oauth2.html) (CE) and [Dovecot 2.3 OAuth2 manual](https://doc.dovecot.org/2.3/configuration_manual/authentication/oauth2/).

- Enable `auth_mechanisms` including `xoauth2` and `oauthbearer`.
- Add `passdb oauth2` with `introspection_url` → `https://cloud.km0digital.com/dex/token/introspect`, `introspection_mode = post`, confidential client credentials.
- Keep existing `passdb sql` for `plain` / `login`.
- Map `username_attribute = email` to `@km0digital.com` mailboxes in PostgreSQL.

Dex v2.42.0 already advertises `introspection_endpoint` in OIDC discovery ([Dex source](https://github.com/dexidp/dex/blob/v2.42.0/server/handlers.go)).

---

## External documentation

| Topic | Link |
|-------|------|
| Dex OpenID Connect | https://dexidp.io/docs/openid-connect/ |
| Dex static clients / custom claims | https://dexidp.io/docs/custom-scopes-claims-clients/ |
| Dex Google connector | https://dexidp.io/docs/connectors/google/ |
| OAuth 2.0 token introspection (RFC 7662) | https://datatracker.ietf.org/doc/html/rfc7662 |
| OpenID Connect Core | https://openid.net/specs/openid-connect-core-1_0.html |
| OpenID Connect Discovery | https://openid.net/specs/openid-connect-discovery-1_0.html |
| Roundcube OAuth2 | https://github.com/roundcube/roundcubemail/wiki/Configuration:-OAuth2 |
| Dovecot OAuth2 (current CE docs) | https://doc.dovecot.org/main/core/config/auth/databases/oauth2.html |
| Dovecot OAuth2 (2.3 reference) | https://doc.dovecot.org/2.3/configuration_manual/authentication/oauth2/ |
| Google OAuth 2.0 for web server apps | https://developers.google.com/identity/protocols/oauth2/web-server |
| PKCE (RFC 7636) | https://datatracker.ietf.org/doc/html/rfc7636 |

---

## Out of scope

- Second Dex instance on `mail.km0digital.com`
- Google OAuth client or redirect URIs on the mail hostname
- Native mail client SSO (Thunderbird / Apple Mail OAuth)
- Email verification on registration (follow-up: mail pre-plan phase 1b)
- Unified single login portal at `auth.km0digital.com` (future UX consolidation — compatible with this architecture)
- Deprecating SQL password auth for all mailboxes (operational accounts stay on password)
- “Activate mail” confirmation screen (explicitly rejected — use silent auto-provision instead)
- Keycloak or external user directory

---

## Future: KM0-wide SSO (why this issue is the right foundation)

This design matches multi-app OIDC:

- **One issuer:** `https://cloud.km0digital.com/dex`
- **One identity store:** OpenCloud IDM
- **One client per service:** `opencloud-web`, `km0-mail-web`, future apps
- **One registration pipeline:** register-api + per-product provisioning hooks

Later improvements (no rewrite required): consolidate login HTML to a single portal, silent OIDC refresh across apps, global logout via Dex end-session.

---

## Test plan

### Infrastructure

- [ ] `curl -s https://cloud.km0digital.com/dex/.well-known/openid-configuration | jq .introspection_endpoint` returns `/dex/token/introspect`
- [ ] `https://mail.km0digital.com/login.html` loads KM0-branded UI (CA/ES/EN/DE if i18n ported)
- [ ] `https://mail.km0digital.com/register` loads register form

### Registration

- [ ] Register `newuser@km0digital.com` → IDM user exists (OpenCloud Settings or Graph)
- [ ] Mailbox exists: `./scripts/km0-mail-admin list-mailboxes` shows user
- [ ] `mail_accounts.opencloud_uuid` populated

### SSO login

- [ ] **Google:** login.html → Google → Roundcube inbox without manual password
- [ ] **Google auto-provision:** user with OpenCloud IDM account (Google) but **no mailbox** → first mail login silently creates mailbox and opens inbox (no “Activate mail” step)
- [ ] **LDAP:** register then login with email/password via Dex LDAP connector → Roundcube inbox
- [ ] **Legacy:** `postmaster@` / CLI mailbox still logs in with password (no OAuth)

### Regression

- [ ] OpenCloud login at `https://cloud.km0digital.com/login.html` unchanged
- [ ] OpenCloud file sync / Dex clients (`opencloud-web`, desktop) unchanged
- [ ] Inbound/outbound mail delivery unchanged (MX, Postfix, Rspamd)

### Failure cases

- [ ] Google user with IDM account, **no mailbox**, email `@km0digital.com` → auto-provision succeeds; second login is idempotent (no duplicate mailbox)
- [ ] OAuth login with email **not** `@km0digital.com` (e.g. `@gmail.com`) → no auto-provision; user-friendly error (register with `@km0digital.com` or use correct Google account)
- [ ] Invalid/expired OAuth token → Dovecot rejects IMAP; Roundcube shows auth error
- [ ] Rate limit on `/api/register` (mirror OpenCloud nginx limit if proxied)

---

## Acceptance criteria

- [ ] Public register + branded login live on `mail.km0digital.com`
- [ ] Webmail SSO works for Google and LDAP via shared Dex
- [ ] **Silent auto-provision** on first Google/LDAP webmail login when `@km0digital.com` and no mailbox exists
- [ ] Dovecot accepts XOAUTH2 tokens issued for `km0-mail-web`
- [ ] Operational mailboxes retain password login
- [ ] Operator checklist above documented in `docs/runbook.md`
- [ ] No new Google Cloud Console redirect URIs required (verified)

---

## Related

- km0-mail pre-plan: `docs/issue-mail-preplan.md` (phase 2 identity / SSO)
- km0-opencloud self-registration: `docs/github-issue-self-registration.md`
- km0-opencloud Dex README: `dex/README.md`
- Redmine / tracking: _(add ticket if applicable)_
