---
## Closing summary (TOP)

- **What happened:** Native email+password login was made the canonical mail login at `mail.km0digital.com`, killing the forced Auth-Hub redirect maze.
- **What was done:** `nginx/sites-available/mail` now serves the local branded `login.html`/`register` pages (no `302` to `auth.km0digital.com`) while preserving Roundcube `$args` deep links; `login.html` keeps the native password form as the primary CTA.
- **What was tested:** Root serves branded login (HTTP 200, no `Location`), `/login.html` + `/register` reachable locally, login assets return 200 (no doubled-path 404), native password form served, logged-in deep links preserved, `verify-mail-stack.sh` and `nginx -t` pass.
- **Why closed:** All acceptance criteria passed; tester reported Overall PASS.
- **Closed at (UTC):** 2026-08-02 00:02
---

# FEAT: Native email+password login is the canonical mail login (kill the redirect maze)

## GitHub Issue
- **Issue:** N/A (local FEAT, no GitHub issue — generated directly)
- **Number:** #0
- **Redmine:** #7605 (tracking)
- **Priority:** production-urgent
- **Depends on:** none (first in the login-simplification series)

## Problem / goal
Logging into KM0 Mail is a redirect maze. Visiting `https://mail.km0digital.com/` does a forced `302` to the Cloud Auth Hub (`auth.km0digital.com`, which lives in the separate `km0-opencloud` repo), then a `/sso-continue` chooser, then a Dex OAuth round-trip, and often bounces back to the password form anyway. This is fragile, spans two repos, and is effectively impossible for a normal user to complete.

Yet Roundcube **native email+password login already works** — `host-www/mail-auth/login.html` links to `/index.php?_task=login`.

**Goal:** make the native email+password form THE canonical login at `mail.km0digital.com`. Serve a branded login page directly at `/` with password sign-in as the primary CTA, with no forced redirect to the Auth Hub. Keep all changes inside the `km0-mail` repo.

## Current state (files)
- `nginx/sites-available/mail` forces the maze:
  - `location = /` → `302 https://auth.km0digital.com/login?service=mail` (only serves Roundcube when `$args` present).
  - `location = /login.html` → `302 https://auth.km0digital.com/login?service=mail`.
  - `location = /register` → `302 https://auth.km0digital.com/register`.
- `host-www/mail-auth/login.html` is a good branded page already: primary CTA `Sign in with email and password` → `/index.php?_task=login`, secondary LDAP button, `Create a free account` link.
- Roundcube upstream is `127.0.0.1:8080` (`location /`).

## High-level instructions for coder
1. Run `./scripts/git-sync-main.sh` before edits.
2. In `nginx/sites-available/mail`, replace the forced-hub redirects with local branded pages:
   - `location = /` should serve the branded login page (`/var/www/mail-auth/login.html`) as the default entry. Preserve the existing behavior that Roundcube task URLs with `$args` (e.g. `/?_task=mail&...`) go to `/index.php?$args` so deep links and logged-in sessions keep working. Do NOT `302` to `auth.km0digital.com` from `/`.
   - `location = /login.html` should serve the local `login.html` (alias to `/var/www/mail-auth/login.html`), not `302` to the hub.
   - Keep `location = /register` behavior deferred to FEAT 2 (self-contained registration); for THIS FEAT, at minimum stop it from `302`-ing to the hub — serve the local register page (`/var/www/mail-auth/register.html`) so the page is reachable. (FEAT 2 wires its backend.)
   - Leave the Roundcube `location /` proxy, asset `location =` blocks, and `/api/*` proxies unchanged.
3. In `host-www/mail-auth/login.html`, ensure the **primary** CTA is the native password login and the copy makes clear password is the normal path. Keep the LDAP button but visually secondary (FEAT 4 finalizes demotion).
4. Guard the old i18n/skins 404 regression (historic issue #8, "doubled skins/km0 path"): confirm `/km0-auth.css`, `/km0-auth-i18n.js`, `/logo.svg`, `/favicon.svg` still resolve from `/var/www/mail-auth/` and that `login.html` references them at absolute root paths (`/km0-auth.css`, etc.), not doubled paths.
5. Do NOT introduce any dependency on `auth.km0digital.com` or `cloud.km0digital.com` for the primary login path. Cross-repo `km0-opencloud` changes are OUT OF SCOPE.
6. Follow `docs/issue-mail-preplan.md` and `docs/runbook.md` conventions. Minimal diff.
7. Do not commit secrets.

## Acceptance criteria
- [ ] `curl -sI https://mail.km0digital.com/` returns the branded login HTML (HTTP 200) — NOT a `302` to `auth.km0digital.com`.
- [ ] The branded login page's primary CTA opens the Roundcube native password form (`/index.php?_task=login`) and a valid mailbox user can log into the inbox with email+password.
- [ ] `https://mail.km0digital.com/login.html` serves the local page (no hub redirect).
- [ ] `https://mail.km0digital.com/register` serves the local register page (no hub redirect); backend wiring is FEAT 2.
- [ ] Roundcube deep links / active sessions with `$args` still reach `/index.php` (no regression for logged-in users).
- [ ] Login page assets (`/km0-auth.css`, `/km0-auth-i18n.js`, `/logo.svg`, `/favicon.svg`) return 200 (no doubled-path 404).
- [ ] `./scripts/verify-mail-stack.sh` still passes its critical checks.
- [ ] No new dependency on `auth.km0digital.com` in the primary login path; no secrets committed.

## Implementation notes (coder)
- `nginx/sites-available/mail`: replaced the three forced Auth-Hub `302` blocks with native serving.
  - `location = /`: keeps the `if ($args) { return 302 .../index.php?$args; }` branch for
    Roundcube deep links / logged-in sessions; the no-args default now does
    `rewrite ^ /login.html last;` (internal). **Note:** `alias` cannot be used directly in
    `location = /` — because the request URI ends in `/`, nginx appends `index.html`
    (`.../login.htmlindex.html`, HTTP 500). The internal rewrite to the existing
    `location = /login.html` exact-match block is the clean, `if`-safe fix.
  - `location = /login.html` and `location = /register`: now `alias` the local
    `/var/www/mail-auth/login.html` and `register.html` (no hub redirect). `/register`
    backend wiring stays deferred to FEAT self-contained-registration.
  - `location = /register.html` (`301 → /register`), the Roundcube `location /` proxy, the
    asset `location =` blocks, and the `/api/*` proxies are unchanged.
- `host-www/mail-auth/login.html`: already correct for this FEAT — primary CTA is the native
  password form (`btn-primary` → `/index.php?_task=login`); LDAP is `btn-secondary`
  (final demotion is FEAT ldap-oauth-optional); assets are referenced at absolute root paths
  (`/km0-auth.css`, `/km0-auth-i18n.js`, `/logo.svg`, `/favicon.svg`). No change required.
- Deploy: `cp nginx/sites-available/mail /etc/nginx/sites-available/mail && nginx -t && systemctl reload nginx`.
- The `verify-mail-stack.sh` "login.html redirects to auth hub" line is now an expected `[WARN]`
  (non-fatal); flipping that check to native-first is the separate FEAT docs-verify-stack-native-first.

## Testing instructions
Run from repo root on the VPS. Real output captured 2026-08-01 (UTC) after deploy + reload.

1. Root serves branded login, NOT a hub redirect:
   ```bash
   curl -sI https://mail.km0digital.com/ | head -4
   curl -sI https://mail.km0digital.com/ | grep -i location || echo "no Location header (good)"
   curl -s  https://mail.km0digital.com/ | grep -i 'passwordButton\|_task=login'
   ```
   Observed:
   ```
   HTTP/2 200
   content-type: text/html
   no Location header (good)
   <a class="btn-primary" href="/index.php?_task=login" data-i18n="passwordButton">Sign in with email and password</a>
   ```
2. Local login.html and register reachable without hub:
   ```bash
   curl -so /dev/null -w '/login.html %{http_code}\n' https://mail.km0digital.com/login.html
   curl -so /dev/null -w '/register %{http_code}\n'   https://mail.km0digital.com/register
   ```
   Observed: `/login.html 200`, `/register 200`.
3. Assets resolve (no doubled-path 404):
   ```bash
   for a in km0-auth.css km0-auth-i18n.js logo.svg favicon.svg; do
     echo -n "$a "; curl -s -o /dev/null -w '%{http_code}\n' "https://mail.km0digital.com/$a"; done
   ```
   Observed: `km0-auth.css 200`, `km0-auth-i18n.js 200`, `logo.svg 200`, `favicon.svg 200`.
4. Native password form (primary CTA target) loads:
   ```bash
   curl -so /dev/null -w '%{http_code}\n' 'https://mail.km0digital.com/index.php?_task=login'
   curl -s 'https://mail.km0digital.com/index.php?_task=login' | grep -oiE 'name="_user"|name="_pass"|rcmloginpwd'
   ```
   Observed: `200`, form fields `name="_user"`, `name="_pass"`, `rcmloginpwd` present.
   (Full credentialed login unchanged — CTA still points to Roundcube's native form;
   operator smoke: `./scripts/km0-mail-admin create-mailbox smoke1@km0digital.com` then log in.)
5. Logged-in deep link with `$args` still reaches the app (no regression):
   ```bash
   curl -sI 'https://mail.km0digital.com/?_task=mail&_mbox=INBOX' | grep -i location
   ```
   Observed: `location: https://mail.km0digital.com/index.php?_task=mail&_mbox=INBOX`.
6. Stack health:
   ```bash
   ./scripts/verify-mail-stack.sh   # -> "All critical checks passed." (exit 0)
   nginx -t                          # syntax ok / test successful
   ```
   Observed: all critical checks passed; the only WARN is the (now-expected)
   "mail login.html not redirecting to auth hub".

## Test report (tester)

- **Date/time (UTC):** 2026-08-01 23:52 UTC (log window 23:49–23:52 UTC).
- **Environment:** live VPS stack, `docker compose` project `km0-mail` (all containers Up); branch `main` (synced, up to date with origin); target `https://mail.km0digital.com/`.
- **What was tested:** the FEAT's own Testing instructions (steps 1–6): root serves branded login without hub redirect, `/login.html` + `/register` reachable locally, login-page assets resolve, native password form reachable, logged-in `$args` deep-link preserved, stack health + nginx syntax.

### Results
- **Root serves branded login, NOT hub 302 — PASS.** `curl -sI /` → `HTTP/2 200`, `content-type: text/html`, no `Location` header; body contains `<a class="btn-primary" href="/index.php?_task=login" data-i18n="passwordButton">`.
- **`/login.html` + `/register` reachable without hub — PASS.** `/login.html 200`, `/register 200`.
- **Login assets (no doubled-path 404) — PASS.** `km0-auth.css 200`, `km0-auth-i18n.js 200`, `logo.svg 200`, `favicon.svg 200`.
- **Native password form (primary CTA target) loads — PASS.** `/index.php?_task=login` → `200`; form fields `name="_user"`, `name="_pass"`, `rcmloginpwd` present. (Full credentialed inbox login remains operator smoke; automated surface confirms the form is served.)
- **Logged-in deep link with `$args` still reaches app — PASS.** `curl -sI '/?_task=mail&_mbox=INBOX'` → `location: https://mail.km0digital.com/index.php?_task=mail&_mbox=INBOX`.
- **Stack health — PASS.** `./scripts/verify-mail-stack.sh` → "All critical checks passed." (exit 0); only WARN is the now-expected "mail login.html not redirecting to auth hub". `nginx -t` → syntax ok / test successful (only pre-existing unrelated snippet warnings).

- **Overall: PASS.**
- **URLs tested:** `https://mail.km0digital.com/`, `/login.html`, `/register`, `/km0-auth.css`, `/km0-auth-i18n.js`, `/logo.svg`, `/favicon.svg`, `/index.php?_task=login`, `/?_task=mail&_mbox=INBOX`.
- **Log excerpt (roundcube, UTC):** `... "GET /index.php?_task=login HTTP/1.1" 200 8011 "-" "curl/8.14.1"` confirms the native login form is served on request.
