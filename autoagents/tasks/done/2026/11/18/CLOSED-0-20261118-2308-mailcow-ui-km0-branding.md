---
## Closing summary (TOP)

- **What happened:** Mailcow/SOGo at mail.km0digital.com still showed stock branding after the Roundcube cutover.
- **What was done:** Added `config/mailcow-branding/` (KM0 theme + SOGo custom JS), `scripts/apply-mailcow-branding.sh`, and docs; applied live (`UI_THEME=km0`, title KM0 Mail, logos, teal/IBM Plex) without changing SSO or proxy/ports.
- **What was tested:** Login chrome, Redis theme, SOGo/SSO hooks, idempotent re-apply, and mail ports/proxy — all PASS.
- **Why closed:** All acceptance criteria passed; no contract breakage.
- **Closed at (UTC):** 2026-11-18 23:12
---

# Mailcow UI + SOGo: apply KM0 brand design

## GitHub Issue
- **Issue:** (create if needed; track under mail hub) — `gh issue create` denied for this token; track Redmine #8480
- **Number:** #0
- **Redmine:** #8480 / hub #7605

## Problem / goal
Mail.km0digital.com now runs **Mailcow + SOGo** (legacy Roundcube stopped). The UI still looks stock Mailcow. Align login, Mailcow UI chrome, and SOGo shell with **KM0 Digital** brand (logo, colours, typography) without breaking SSO or upgrades.

## High-level instructions for coder
- Source of brand truth: km0-web / existing Roundcube plugin @config/roundcube/plugins/km0_theme@ (colours, logo assets) and public site brand tokens where helpful.
- Prefer Mailcow-supported customize paths (Admin → Configuration → Customize / custom CSS & logos under Mailcow data dirs). Do **not** fork SOGo/Mailcow core if a customize hook exists.
- Keep @mail.km0digital.com@ hostname; do not change ports or reverse-proxy contract (host nginx → :8880).
- Preserve SOGo SSO via @/sogo-auth@.
- Document how to re-apply after @./update.sh@ / image pull.
- Reference @docs/mailcow-cutover-status.md@ and @docs/runbook.md@.
- English for commits/docs; no secrets in git.

## Out of scope
- Keycloak IdP attach (Phase 4 — paused)
- Deleting km0-mail volumes
- Functional mail routing changes

## Implementation notes (coder)
- Pack: `config/mailcow-branding/` (theme `km0`, assets, SOGo `custom-theme.js` + SSO-safe `custom-sogo.js`)
- Apply: `scripts/apply-mailcow-branding.sh` → `/opt/mailcow-dockerized` (theme files, Redis UI texts/logos, SOGo mounts; restarts nginx+sogo)
- Docs: `docs/mailcow-branding.md`, runbook + cutover status + CHANGELOG updated
- Applied live: Redis `UI_THEME=km0`, title **KM0 Mail**, logos set; `/sogo-auth` still 200

## Testing instructions

1. **Login chrome**
   ```bash
   curl -sI https://mail.km0digital.com/ | head
   curl -s https://mail.km0digital.com/ | grep -E '<title>|KM0 Mail|main-logo'
   ```
   Expect HTTP 200 and `<title>KM0 Mail</title>`; browser should show K0 mark (not stock cow) and IBM Plex / teal accents in dark mode.

2. **Theme selected**
   ```bash
   REDISPASS=$(grep '^REDISPASS=' /opt/mailcow-dockerized/mailcow.conf | cut -d= -f2-)
   docker exec mailcowdockerized-redis-mailcow-1 redis-cli -a "$REDISPASS" --no-auth-warning GET UI_THEME
   ```
   Expect `km0`. Admin → Configuration → Customize should list **KM0 Digital**.

3. **SOGo shell + SSO**
   ```bash
   curl -sI https://mail.km0digital.com/SOGo/ | head
   curl -sI https://mail.km0digital.com/sogo-auth | head
   grep -n "loginForm\|/user" /opt/mailcow-dockerized/data/conf/sogo/custom-sogo.js
   ```
   Expect SOGo redirect to `/SOGo/index`, `/sogo-auth` 200, and custom-sogo still redirecting login form to `/user`. In browser after mailbox login, SOGo chrome should use teal primary (not stock green cow palette).

4. **Re-apply script (idempotent)**
   ```bash
   cd /opt/km0-mail && ./scripts/apply-mailcow-branding.sh
   ```
   Should complete without error; login title still KM0 Mail.

5. **No contract breakage**
   Host nginx → Mailcow `:8880` unchanged; ports 25/465/587/993 unchanged (`docker compose -f /opt/mailcow-dockerized/docker-compose.yml ps`).

## Test report

1. **Date/time (UTC) and log window:** 2026-11-18T23:11:48Z → 2026-11-18T23:12:21Z (tester start → post re-apply verify).
2. **Environment:** branch `main` (@ `origin/main`); Mailcow compose `/opt/mailcow-dockerized/docker-compose.yml` (project `mailcowdockerized`); public URL `https://mail.km0digital.com/`; host nginx → `127.0.0.1:8880`. Stack readiness: polled `curl -sI https://mail.km0digital.com/` → HTTP/2 200 before and after branding re-apply (nginx/sogo restart completed; no fixed sleep).
3. **What was tested:** Login chrome title/logo; Redis `UI_THEME`; SOGo redirect + `/sogo-auth` SSO hook + `custom-sogo.js`; idempotent `./scripts/apply-mailcow-branding.sh`; mail ports + host proxy contract; theme CSS/SOGo teal tokens (IBM Plex / `#0F766E`).
4. **Results:**
   - **Login chrome — PASS.** `curl -sI` → HTTP/2 200; body `<title>KM0 Mail</title>`, legend `KM0 Mail`, `main-logo` / `main-logo-dark` SVG data-URIs with K0 plaque `#0F766E` (not stock cow). Live theme CSS has `IBM Plex Sans` + `#0F766E`.
   - **Theme selected — PASS.** `redis-cli GET UI_THEME` → `km0`; theme dir `/opt/mailcow-dockerized/data/web/css/themes/km0/{theme.json,theme.css,dark.css}` present (Customize label **KM0 Digital** per apply script / theme pack).
   - **SOGo shell + SSO — PASS.** `/SOGo/` → HTTP/2 302 `Location: /SOGo/index`; `/sogo-auth` → HTTP/2 200; `custom-sogo.js` lines 6–8 redirect `loginForm` → `/user`; `custom-theme.js` primary palette `km0-signal` / teal `#0F766E` (not stock green).
   - **Re-apply script — PASS.** `./scripts/apply-mailcow-branding.sh` exit 0; post-run title still `KM0 Mail`, `UI_THEME=km0`.
   - **No contract breakage — PASS.** Host nginx `proxy_pass http://127.0.0.1:8880/`; compose publishes 25/465/587/993; `nc -vz` succeeded on 25/465/587/993; MX `50 mail.km0digital.com.`, A `116.202.10.106`.
5. **Overall: PASS**
6. **URLs tested:** `https://mail.km0digital.com/`, `https://mail.km0digital.com/SOGo/`, `https://mail.km0digital.com/sogo-auth`. GitHub issue #0 N/A (no issue; Redmine #8480) — `agent:testing` label skipped.
7. **Relevant log / evidence excerpts:**
   ```
   HTTP/2 200 … https://mail.km0digital.com/
   <title>KM0 Mail</title>
   UI_THEME=km0
   /SOGo/ → 302 Location: /SOGo/index
   /sogo-auth → 200
   custom-sogo.js: window.location.href = '/user';
   apply-mailcow-branding.sh → EXIT=0; title still KM0 Mail
   nc … 25/465/587/993 succeeded
   ```
