---
## Closing summary (TOP)

- **What happened:** Roundcube login rendered a doubled `skins/km0/skins/km0/js/i18n.js` path (404 HTML MIME), so language switching could not load.
- **What was done:** Changed `login.html` script to skin-relative `/js/i18n.js` (same pattern as the logo); documented skin-relative assets in the runbook and CHANGELOG.
- **What was tested:** Smoke curls PASS — asset 200 `text/javascript`, rendered `src` is non-doubled `skins/km0/js/i18n.js`, doubled path absent (count 0) on HTTPS and localhost:8080.
- **Why closed:** All acceptance criteria passed; overall tester result PASS.
- **Closed at (UTC):** 2026-07-25 14:44
---

# FEAT-Task: BUG: Roundcube login i18n.js 404 — doubled skins/km0 path

## GitHub Issue
- **Number:** #8
- **URL:** https://github.com/AMVARA-CONSULTING/km0-mail/issues/8
- **Labels:** bug
- **Redmine tracking:** #7605 (when configured)
- **Priority:** production-urgent

## Problem / goal
Roundcube rewrites the KM0 login skin script include so the browser requests `skins/km0/skins/km0/js/i18n.js` (404 HTML). Console: MIME type `text/html` is not executable. Correct file is at `/skins/km0/js/i18n.js` (200).

Root cause: `skins/km0/templates/login.html` uses `<script src="/skins/km0/js/i18n.js">`. Roundcube skin path resolution treats that like other skin assets and prefixes `skins/km0/` again. Logo correctly uses skin-relative `/images/logo.svg`.

## High-level instructions for coder
1. Run `./scripts/git-sync-main.sh` before edits.
2. Fix `skins/km0/templates/login.html`: change script to skin-relative `/js/i18n.js` (same pattern as `/images/logo.svg`), **or** another Roundcube-safe include that renders a single `skins/km0/js/i18n.js` (or absolute origin URL). Do not leave a doubled path in rendered HTML.
3. Grep `skins/km0` for other `/skins/km0/` hardcoded asset URLs that would double the same way; fix only if broken.
4. Verify inside container / via curl that login HTML contains a working i18n src (not `skins/km0/skins/km0`).
5. Append Testing instructions; rename FEAT → WIP → UNTESTED per `autoagents/TASKS-README.md`.
6. Update `docs/CHANGELOG.md` (and runbook skin file note if needed). No secrets.

## Acceptance criteria
- [x] Rendered login HTML references `skins/km0/js/i18n.js` (or absolute equivalent) — never `skins/km0/skins/km0/...`
- [x] `curl -sI https://mail.km0digital.com/skins/km0/js/i18n.js` → 200 `text/javascript`
- [x] `curl -sL 'https://mail.km0digital.com/?_task=login' | grep i18n.js` shows non-doubled path
- [x] No secrets committed; CHANGELOG updated

## Implementation notes

- Changed `skins/km0/templates/login.html` script from `/skins/km0/js/i18n.js` to skin-relative `/js/i18n.js` (same pattern as logo `/images/logo.svg`).
- No other `/skins/km0/` hardcoded asset URLs in `skins/km0/` templates.
- Runbook note: skin template assets must be skin-relative.
- Roundcube bind-mounts `skins/km0`; restart roundcube after template edit if Apache/PHP caches aggressively.

## Testing instructions

### Smoke (required)

```bash
cd /opt/km0-mail
docker compose ps roundcube
# Optional after pull: docker compose restart roundcube

# Asset exists
curl -sI https://mail.km0digital.com/skins/km0/js/i18n.js | head -5
# Expect: HTTP/2 200, content-type: text/javascript

# Rendered login — single skins/km0 segment only
curl -sL 'https://mail.km0digital.com/?_task=login' | grep -oE 'src="[^"]*i18n\.js[^"]*"'
# Expect: src="skins/km0/js/i18n.js?s=..."
# Must NOT contain: skins/km0/skins/km0

curl -sL 'https://mail.km0digital.com/?_task=login' | grep -c 'skins/km0/skins/km0'
# Expect: 0

# Local (bypass nginx)
curl -sL 'http://127.0.0.1:8080/?_task=login' | grep -oE 'src="[^"]*i18n\.js[^"]*"'
```

### Browser

1. Open `https://mail.km0digital.com/?_task=login` (hard-refresh).
2. DevTools Network: `i18n.js` → **200**, type javascript (not HTML).
3. Language switch (CA/ES/EN/DE) still updates tagline / register link strings.
4. No console MIME error for `i18n.js`.

## Test report

1. **Date/time (UTC) and log window:** 2026-07-25 14:43:15 UTC → 14:43:40 UTC. Roundcube access for login/i18n in `2026-07-25T14:43:31Z`–`14:43:40Z`.
2. **Environment:** compose project `km0-mail` (postfix/dovecot/rspamd/roundcube/postgres Up); branch `main` @ `3ce82e3`; URLs `https://mail.km0digital.com/`, `http://127.0.0.1:8080/`. Stack ready: poll #1 of `https://mail.km0digital.com/` returned HTTP 302 (Auth Hub redirect); MX `50 mail.km0digital.com.`; A `116.202.10.106`; ports 25/587/993 open.
3. **What was tested:** Smoke curls for `i18n.js` asset (200 `text/javascript`), rendered login HTML script `src` (non-doubled `skins/km0/js/i18n.js`), doubled-path absence (count 0) on HTTPS and localhost:8080, doubled URL 404, template uses skin-relative `/js/i18n.js`, i18n.js contains EN/ES/CA/DE + `loginTagline`/`registerLink` keys, CHANGELOG entry for #8, no secrets in path fix. Browser DevTools Network/MIME not exercised interactively; equivalent verified via HTTP headers + JS payload.
4. **Results:**
   - Rendered login HTML references `skins/km0/js/i18n.js` (never `skins/km0/skins/km0/...`) — **PASS** (`src="skins/km0/js/i18n.js?s=1784990257"`; `grep -c skins/km0/skins/km0` → 0 on HTTPS and :8080)
   - `curl -sI https://mail.km0digital.com/skins/km0/js/i18n.js` → 200 `text/javascript` — **PASS** (HTTP/2 200, `content-type: text/javascript`, length 8078; body starts with IIFE + LOCALES)
   - Login HTML grep for `i18n.js` non-doubled — **PASS** (HTTPS + `http://127.0.0.1:8080/?_task=login`)
   - Doubled path URL returns 404 — **PASS** (`/skins/km0/skins/km0/js/i18n.js` → 404 HTML)
   - Template fix skin-relative `/js/i18n.js` — **PASS** (`login.html` line 42)
   - i18n locales CA/ES/EN/DE usable (tagline/register keys present) — **PASS** (`loginTagline` ×4 in JS; keys present)
   - No secrets; CHANGELOG updated — **PASS** (CHANGELOG line notes issue #8; path-only template change)
5. **Overall:** **PASS**
6. **URLs tested:** https://mail.km0digital.com/ ; https://mail.km0digital.com/?_task=login ; https://mail.km0digital.com/skins/km0/js/i18n.js ; https://mail.km0digital.com/skins/km0/skins/km0/js/i18n.js ; http://127.0.0.1:8080/?_task=login
7. **Relevant log excerpts:**
   ```
   roundcube: HEAD /skins/km0/js/i18n.js HTTP/1.1" 200
   roundcube: GET /index.php?_task=login HTTP/1.1" 200
   roundcube: GET /?_task=login HTTP/1.1" 200
   roundcube: GET /skins/km0/js/i18n.js HTTP/1.1" 200
   roundcube: HEAD /skins/km0/skins/km0/js/i18n.js HTTP/1.1" 404
   HTTPS mail.km0digital.com/ → 302 location: https://auth.km0digital.com/login?service=mail
   ```
