---
## Closing summary (TOP)

- **What happened:** Mail auth surfaces still used legacy Inter + purple gradient chrome while marketing already shipped civic dark KM0.
- **What was done:** Replaced mail-auth and Roundcube login CSS/assets with Paper/Snow/Mist/Ink/Signal tokens, IBM Plex/Bricolage, and canonical K0 favicon/logo; deployed to live mail-auth and Roundcube.
- **What was tested:** Hard-gate parity, anti-slop, smoke curls, and login form checks all **PASS** (favicon md5 match, civic tokens, no legacy hexes).
- **Why closed:** All acceptance criteria passed; tester overall **PASS**.
- **Closed at (UTC):** 2026-07-18 06:54
---

# UNTESTED-Task: Sync Mail auth surfaces to civic dark KM0

## Origin
- **Source:** Direct operator request (skip GitHub). Sibling sync with remodelled `km0-web`.
- **Brief:** `/opt/km0-web/docs/design/product-auth-surfaces-sync.md`
- **No GitHub issue** (`NEW-0`).
- **Redmine:** note on close if configured (#7605 tracking pattern).

## Problem / goal
Mail branded auth (`mail-auth`) and Roundcube **login** skin still use legacy Inter + purple gradient chrome and old favicon/logo. Marketing already ships civic dark + K0 lettermark. Sync custom login/register (and shared auth landings) plus favicons. Do **not** restyle the Roundcube mailbox UI after login.

## Scope (only)
1. `host-www/mail-auth/login.html`, `register.html`
2. Shared auth landings that reuse `km0-auth.css`: `domain.html`, `verify.html` (same token pass)
3. `host-www/mail-auth/km0-auth.css`, `favicon.svg`, `logo.svg`
4. Roundcube login skin: `skins/km0/templates/login.html`, `skins/km0/styles/km0-login.css`, `skins/km0/images/favicon.svg`, `skins/km0/images/logo.svg` (and PNG if referenced)

## Out of scope
- Roundcube Elastic UI after authentication (folders, compose, settings)
- Dovecot / Postfix / mail-provision-api behaviour
- Changing SSO redirect targets or i18n keys unless required for contrast/a11y copy

## High-level instructions for coder
1. Read `/opt/km0-web/docs/design/product-auth-surfaces-sync.md` and `/opt/km0-web/docs/brand-tokens.md`.
2. Prefer aligning with Auth hub + Cloud once those land; if this task runs first, still copy assets from `/opt/km0-web/public/` (source of truth), not from stale purple SVGs.
3. Replace Inter-only + purple gradient / glow / clipped rainbow headlines with Paper / Snow / Mist / Ink / Signal + IBM Plex Sans.
4. Keep Roundcube login form objects, plugins, and `data-i18n` hooks working.
5. Deploy per `docs/runbook.md` / skin path. Append Hard gate Testing instructions before `UNTESTED-`.

## Acceptance (hard)
- [x] `mail-auth` login + register match civic dark KM0 (side-by-side with km0digital.com)
- [x] Roundcube `/index.php?_task=login` uses the same tokens + K0 mark
- [x] Favicons are full-bleed K0; no purple gradient assets in scoped paths
- [x] `rg` clean of legacy brand-chain hexes in scoped files
- [x] Password login and register links still work

## What was done
- Replaced Inter + purple gradient chrome in `host-www/mail-auth/km0-auth.css` and `skins/km0/styles/km0-login.css` with Paper/Snow/Mist/Ink/Signal + IBM Plex Sans / Bricolage Grotesque.
- Copied canonical K0 `favicon.svg` + `logo.svg` from `/opt/km0-web/public/` into mail-auth and Roundcube skin images.
- Updated font links in mail-auth HTML + `skins/km0/meta.json`.
- Deployed: `rsync` → `/var/www/mail-auth/`; `docker compose up -d roundcube`.
- Note: nginx still 302s `/login.html` and `/register` to Auth Hub; live mail-native surfaces are Roundcube login + `domain.html`/`verify.html` + shared CSS/logo/favicon.

## Testing instructions

### Hard gate protocol (required)
| Item | Value |
|------|-------|
| Reference | https://km0digital.com/ |
| KM0 Mail URLs | https://mail.km0digital.com/domain.html ; http://127.0.0.1:8080/?_task=login (or https://mail.km0digital.com/index.php?_task=login) ; favicon https://mail.km0digital.com/favicon.svg |
| Decisive viewport | Roundcube login card + domain.html card + tab favicon |

**Parity claims (3)**
1. Favicon `mail.km0digital.com/favicon.svg` md5 matches `km0digital.com/favicon.svg` (full-bleed K0 on `#0F766E`).
2. Roundcube login card uses Snow `#141B28` on Paper `#0B1220` with Signal `#2DD4BF` primary button — same tokens as marketing `docs/brand-tokens.md`.
3. Logo plaque on Roundcube login / domain.html is the rounded K0 lettermark (`#0F766E` + `#EEF0F2`), not the old purple gradient pin.

**Anti-slop claims (3)**
1. No purple radial glow behind the card (`background-image: none` on login body).
2. No `background-clip: text` rainbow headline — titles are solid Ink `#E6E9ED`.
3. No Inter-only UI font; IBM Plex Sans (+ Bricolage for H1/title) loaded via Google Fonts in HTML/`meta.json`.

### Smoke
```bash
# Shared CSS + assets (live)
curl -sI https://mail.km0digital.com/km0-auth.css https://mail.km0digital.com/favicon.svg https://mail.km0digital.com/logo.svg https://mail.km0digital.com/domain.html | grep -E 'HTTP/|content-type'

# Roundcube login skin
curl -sI http://127.0.0.1:8080/skins/km0/styles/km0-login.css http://127.0.0.1:8080/skins/km0/images/logo.svg http://127.0.0.1:8080/skins/km0/images/favicon.svg | grep HTTP
curl -s 'http://127.0.0.1:8080/?_task=login' | grep -E 'km0-login-card|IBM\+Plex|logo\.svg|rcmloginsubmit'

# Legacy brand-chain must be empty
grep -nE '7[Bb]3[Ff][Ee]4|E040A0|FF5F2E|#007[Bb][Ff][Ff]' host-www/mail-auth skins/km0/styles/km0-login.css skins/km0/images || echo CLEAN

# Favicon parity with marketing
md5sum <(curl -s https://mail.km0digital.com/favicon.svg) <(curl -s https://km0digital.com/favicon.svg)

# Auth hub redirects still present (expected until Auth Hub civic sync)
curl -sI https://mail.km0digital.com/login.html | grep -i location
curl -sI https://mail.km0digital.com/register | grep -i location
```

### Manual browser checks
1. Open https://km0digital.com/ and https://mail.km0digital.com/index.php?_task=login side-by-side — tokens + K0 mark match; hard-refresh if CSS cached.
2. Confirm password fields + Login submit present; register / other sign-in links still work.
3. Open https://mail.km0digital.com/domain.html — civic dark card, K0 logo, no purple.
4. Tab favicon shows full-bleed teal K0 (not gradient pin).

## References
- `/opt/km0-web/docs/design/product-auth-surfaces-sync.md`
- `/opt/km0-web/docs/brand-tokens.md`
- `/opt/km0-web/docs/design/logo-brief-it-services.md`
- `docs/runbook.md` (this repo)
- Sibling: `/opt/km0-auth/tasks/NEW-0-20260718-0649-civic-dark-auth-hub-surfaces.md`
- Sibling: `/opt/opencloud/autoagents/tasks/NEW-0-20260718-0649-civic-dark-cloud-auth-surfaces.md`

## Test report

1. **Date/time (UTC) and log window:** 2026-07-18 06:53:57 UTC → 06:54:21 UTC. Roundcube access log window `2026-07-18T06:53:00Z`–`06:54:17Z`.
2. **Environment:** compose project `km0-mail` (all core services Up); branch `main` @ `b3c5284`; URLs `https://mail.km0digital.com/`, `http://127.0.0.1:8080/`, reference `https://km0digital.com/`. Stack ready: poll #1 of `https://mail.km0digital.com/` returned HTTP 302 (Auth Hub redirect); ports 25/587/993 and localhost:8080 open; Roundcube HEAD `/` 200.
3. **What was tested:** Hard-gate parity (favicon md5, civic dark tokens on Roundcube login + domain.html, K0 lettermark), anti-slop (no purple glow / rainbow clip / Inter), smoke curls for CSS/assets/login HTML/legacy hex grep, Auth Hub redirects for `/login.html` + `/register`, login form + register link presence. GitHub labels N/A (no issue; `NEW-0`).
4. **Results:**
   - Favicon md5 parity with `km0digital.com/favicon.svg` — **PASS** (`e1aeac716e15dcc714ace2e20f901da4` both)
   - Roundcube login Snow `#141B28` on Paper `#0B1220`, Signal `#2DD4BF` primary — **PASS** (`km0-login.css` vars + `background: var(--km0-paper)` / card `var(--km0-snow)` / button `var(--km0-signal)`; live CSS md5 matches repo)
   - Logo plaque rounded K0 (`#0F766E` + `#EEF0F2`) — **PASS** (live `/logo.svg` + Roundcube skin)
   - No purple radial glow (`background-image: none`) — **PASS**
   - No `background-clip: text` rainbow; titles solid Ink `#E6E9ED` — **PASS** (`background-clip: unset`; `color: var(--km0-ink)`)
   - IBM Plex Sans + Bricolage via Google Fonts — **PASS** (login HTML + `meta.json` + domain.html)
   - Legacy brand-chain hexes empty in scoped paths — **PASS** (`CLEAN`)
   - Password fields + Login submit + register link — **PASS** (`rcmloginuser`/`rcmloginpwd`/`rcmloginsubmit`; register → `auth.km0digital.com/register`)
   - Live mail-auth assets 200 — **PASS** (`km0-auth.css`, favicon, logo, `domain.html`)
   - Auth Hub redirects for `/login.html` + `/register` — **PASS** (expected 302)
5. **Overall:** **PASS**
6. **URLs tested:** https://mail.km0digital.com/ ; https://mail.km0digital.com/index.php?_task=login ; https://mail.km0digital.com/domain.html ; https://mail.km0digital.com/km0-auth.css ; https://mail.km0digital.com/favicon.svg ; https://mail.km0digital.com/logo.svg ; https://mail.km0digital.com/login.html ; https://mail.km0digital.com/register ; http://127.0.0.1:8080/?_task=login ; http://127.0.0.1:8080/skins/km0/... ; https://km0digital.com/favicon.svg
7. **Relevant log excerpts:**
   ```
   roundcube: GET /?_task=login HTTP/1.1" 200
   roundcube: GET /skins/km0/styles/km0-login.css HTTP/1.1" 200
   roundcube: GET /skins/km0/images/logo.svg HTTP/1.1" 200
   roundcube: GET /skins/km0/images/favicon.svg HTTP/1.1" 200
   HTTPS mail.km0digital.com/ → 302 location: https://auth.km0digital.com/login?service=mail
   ```
