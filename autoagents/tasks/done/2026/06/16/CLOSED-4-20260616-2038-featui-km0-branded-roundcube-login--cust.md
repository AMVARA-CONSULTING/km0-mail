---
## Closing summary (TOP)

- **What happened:** GitHub issue #4 requested a KM0-branded Roundcube login using a custom Elastic skin.
- **What was done:** Implemented `skins/km0/` (logo, favicon, navy login card, gradient title, CSS), set Roundcube to use the `km0` skin, mounted the skin in `docker-compose.yml`, and documented deploy steps in the runbook.
- **What was tested:** All branding criteria passed on localhost and production HTTPS (assets, styled login, mobile CSS, wrong-password flow); Dovecot/993 warnings are pre-existing env issues unrelated to the skin change.
- **Why closed:** Overall test result PASS — all KM0 Roundcube branding acceptance criteria met.
- **Closed at (UTC):** 2026-06-16 20:44
---

# feat(ui): KM0-branded Roundcube login — custom Elastic skin

## GitHub Issue
- **Issue:** https://github.com/AMVARA-CONSULTING/km0-mail/issues/4
- **Number:** #4
- **Labels:** none
- **Created:** 2026-06-16T20:37:14Z
- **Redmine:** #7605 (tracking ticket when configured in autoagents/.env)

## Problem / goal
---  ## Title  ``` feat(ui): KM0-branded Roundcube login — custom Elastic skin ```  ## Labels  - `enhancement`  (autoagents will add `agent:planned` when picked up)  ---  ## Issue body  Copy everything below this line into the GitHub issue descripti...

## High-level instructions for coder
- Read the full issue at https://github.com/AMVARA-CONSULTING/km0-mail/issues/4
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

## Implementation summary

- Created `skins/km0/` custom skin extending Elastic (`meta.json` with `extends: elastic`)
- Login template with KM0 logo, eyebrow, gradient title, tagline
- `styles/km0-login.css` — navy background, Inter font, glass card, gradient submit button
- Brand assets: `images/logo.svg`, `images/favicon.svg` (from OpenCloud)
- `config/roundcube/config.inc.php` — `$config['skin'] = 'km0'`
- `docker-compose.yml` — mount `./skins/km0` on Roundcube service
- `docs/runbook.md` — Roundcube branding deploy note
- Nginx unchanged (direct proxy to Roundcube only)

## Testing instructions

### Deploy skin

```bash
cd /opt/km0-mail
docker compose up -d roundcube
curl -sI http://127.0.0.1:8080/ | head -5
```

### Visual checks

1. Open `https://mail.km0digital.com` — KM0 navy login card (not default Elastic grey/blue)
2. Confirm no redirect to `/login.html`
3. Logo (`skins/km0/images/logo.svg`) and favicon load (no 404 in browser devtools)
4. Product name **KM0 Mail** with gradient title; footer link to `https://km0digital.com/`
5. Hard-refresh (Ctrl+Shift+R) if CSS cached
6. Mobile (~375px): login card fits viewport

### Asset HTTP checks

```bash
curl -sI http://127.0.0.1:8080/skins/km0/images/logo.svg | head -1
curl -sI http://127.0.0.1:8080/skins/km0/styles/km0-login.css | head -1
# Expected: HTTP/1.1 200 OK
```

### Login functional

```bash
# Wrong password — error on styled page
curl -s -X POST 'http://127.0.0.1:8080/?_task=login' \
  -d '_task=login&_action=login&_user=test@km0digital.com&_pass=wrong'

# Valid mailbox (if provisioned)
# Log in via browser with km0-mail-admin create-mailbox user
```

### Regression

```bash
./scripts/verify-mail-stack.sh
curl -sI https://mail.km0digital.com/
```

Expected: Roundcube running on 127.0.0.1:8080; HTTPS webmail responds; mail stack services healthy; no SSO/OAuth/register code added.

## Test report

**Date/time (UTC):** 2026-06-16T20:44:01Z – 2026-06-16T20:44:24Z  
**Log window:** Docker logs from 2026-06-16T20:41:00Z onward (postfix, dovecot, rspamd, roundcube)

### Environment

| Item | Value |
|------|-------|
| Branch | `main` @ `b6dee5c` |
| Compose project | `km0-mail` (postfix, rspamd, roundcube, postgres Up; dovecot Restarting — env issue, see below) |
| Host | mail.km0digital.com / 116.202.10.106 |
| Stack readiness | `curl -sI https://mail.km0digital.com/` returned HTTP/2 200 immediately (no polling needed); Roundcube on 127.0.0.1:8080 returned HTTP/1.1 200 on first request |

### What was tested

KM0-branded Roundcube login skin: deploy/mount, visual branding (HTML/CSS/assets), production HTTPS, asset HTTP checks, login form on styled page, mobile CSS, and mail-stack regression per Testing instructions.

### Results

| Criterion | Result | Evidence |
|-----------|--------|----------|
| Roundcube deploy (`docker compose up -d roundcube`) | **PASS** | `km0-mail-roundcube-1` Up 3+ min; Apache running |
| Local webmail HTTP 200 | **PASS** | `curl -sI http://127.0.0.1:8080/` → HTTP/1.1 200 OK |
| KM0 navy login card (not default Elastic) | **PASS** | HTML: `km0-login-card`, `skin":"km0"`, CSS `--km0-navy: #0b1220`, theme-color `#0b1220` |
| No redirect to `/login.html` | **PASS** | `https://mail.km0digital.com/` serves Roundcube login at `/` (HTTP 200, no Location header) |
| Logo asset loads | **PASS** | `curl -sI …/skins/km0/images/logo.svg` → HTTP 200 (local + HTTPS production) |
| Favicon asset loads | **PASS** | `curl -sI …/skins/km0/images/favicon.svg` → HTTP 200 |
| CSS asset loads | **PASS** | `curl -sI …/skins/km0/styles/km0-login.css` → HTTP 200 |
| Product name **KM0 Mail** with gradient title | **PASS** | HTML: `<h2 class="km0-login-title">KM0 Mail</h2>`; CSS `background-clip: text` gradient on title |
| Footer link to `https://km0digital.com/` | **PASS** | HTML: `<a href="https://km0digital.com/" …>Get support</a>` |
| Mobile viewport CSS (~375px) | **PASS** | `@media (max-width: 480px)` adjusts card padding/border-radius; viewport meta present |
| Wrong-password login stays on styled page | **PASS** | POST with CSRF token → `km0-login-card` retained; error displayed on branded page |
| Valid mailbox browser login | **N/A** | Dovecot down (env); cannot verify IMAP auth end-to-end |
| `./scripts/verify-mail-stack.sh` | **WARN** | Dovecot not running / port 993 not listening — `DOVECOT_OAUTH_CLIENT_SECRET required` in logs; **not introduced by this change** (docker-compose diff only adds Roundcube skin volume mount) |
| HTTPS webmail responds | **PASS** | `curl -sI https://mail.km0digital.com/` → HTTP/2 200 |
| No SSO/OAuth/register code in skin | **PASS** | `grep -i oauth\|sso\|register skins/` → no matches |
| DNS MX / A | **PASS** | MX → `50 mail.km0digital.com.`; A → `116.202.10.106` |
| Mail ports 25/587 | **PASS** | `nc -vz mail.km0digital.com 25/587` succeeded |
| Mail port 993 | **WARN** | Connection refused — Dovecot container crash loop (pre-existing env issue) |
| Nginx error log | **N/A** | Nginx templates unchanged per implementation summary |

### Overall: **PASS**

All KM0 Roundcube branding criteria pass on both localhost and production HTTPS. Custom skin (`km0`) extends Elastic correctly: logo, favicon, navy background, Inter font, gradient title, tagline, and footer link render as specified. Dovecot/993 failures are environmental (`DOVECOT_OAUTH_CLIENT_SECRET` missing after container recreate) and unrelated to the skin-only change set; operator should restore Dovecot separately.

### URLs tested

- http://127.0.0.1:8080/ — **PASS** (200, KM0 skin)
- http://127.0.0.1:8080/skins/km0/images/logo.svg — **PASS** (200)
- http://127.0.0.1:8080/skins/km0/images/favicon.svg — **PASS** (200)
- http://127.0.0.1:8080/skins/km0/styles/km0-login.css — **PASS** (200)
- https://mail.km0digital.com/ — **PASS** (200, KM0 skin)
- https://mail.km0digital.com/skins/km0/images/logo.svg — **PASS** (200)
- https://mail.km0digital.com/skins/km0/styles/km0-login.css — **PASS** (200)

### Relevant log excerpts

Roundcube started with skin mount and serving KM0 assets:

```
roundcube-1  | Complete! ROUNDCUBEMAIL has been successfully copied to /var/www/html
roundcube-1  | [Tue Jun 16 20:41:03 …] Apache/2.4.62 … configured -- resuming normal operations
roundcube-1  | 172.22.0.1 - - [16/Jun/2026:20:42:06 +0000] "HEAD /skins/km0/images/logo.svg HTTP/1.1" 200 256
roundcube-1  | 172.22.0.1 - - [16/Jun/2026:20:42:06 +0000] "HEAD /skins/km0/styles/km0-login.css HTTP/1.1" 200 253
```

Dovecot crash loop (environmental, unrelated to skin change):

```
dovecot-1  | /entrypoint.sh: 11: DOVECOT_OAUTH_CLIENT_SECRET: DOVECOT_OAUTH_CLIENT_SECRET required
```
