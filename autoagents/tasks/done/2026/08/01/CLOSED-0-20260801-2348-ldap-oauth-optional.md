---
## Closing summary (TOP)

- **What happened:** LDAP/OAuth was demoted to a clearly optional secondary path on the mail login, with no automatic OIDC loops and no Google/activate coupling.
- **What was done:** Moved the LDAP button into an "Other ways to sign in" block below the primary password CTA (`btn-secondary--muted`), made intro copy password-first, and updated i18n; `dex-auth.js` stayed LDAP-only and click-only, with the Roundcube `oauth_login_redirect=false` fallback intact.
- **What was tested:** No auto-redirect on load, LDAP rendered after the password CTA in the muted block, no `connector_id=google`/`prompt=none`, Dex starts only on explicit click, no Google/activate CTA on the login surface, fallback config present, stack health passes.
- **Why closed:** All acceptance criteria passed; tester reported Overall PASS (interactive IdP login remains operator smoke).
- **Closed at (UTC):** 2026-08-02 00:02
---

# FEAT: Demote LDAP/OAuth to an optional secondary path on mail login

## GitHub Issue
- **Issue:** N/A (local FEAT, no GitHub issue — generated directly)
- **Number:** #0
- **Redmine:** #7605 (tracking)
- **Priority:** medium
- **Depends on:** FEAT native-login-canonical

## Problem / goal
The Dex LDAP OAuth path and the Google/activate detour are the main causes of the "goes in circles / errors" experience. In the native-first model they must be clearly **optional secondary** options, never the default, and must never trap the user in redirect/`prompt=none` loops.

**Goal:** keep the LDAP OAuth button as a small secondary option for existing OpenCloud users, remove any Google/activate coupling from the mail login page, and ensure no automatic OIDC loops.

## Current state (files)
- `host-www/mail-auth/login.html`: has `#km0-ldap-login` button (secondary) that calls `window.KM0DexAuth.startDexLogin()`; primary CTA is native password.
- `host-www/mail-auth/dex-auth.js`: builds a Dex authorize URL with `connector_id=ldap` (LDAP only — Google intentionally excluded), PKCE, redirect `/index.php/login/oauth`. Clears stale `oidc.*` browser state.
- `nginx/sites-available/mail`: proxies `/dex/theme/i18n.js` from `cloud.km0digital.com` for the LDAP button labels.
- Historic decisions: Google→Roundcube mapping is wontfix (spike #12); no `connector_id=google` for Roundcube; activate path is Cloud-only.

## High-level instructions for coder
1. Run `./scripts/git-sync-main.sh` before edits.
2. In `login.html`, keep the LDAP button but make it unmistakably secondary (below the password CTA, muted styling / smaller, under an "Other ways to sign in" affordance). Keep the existing `ldapHint` copy about the brief redirect to `cloud.km0digital.com`.
3. Ensure NO automatic OAuth start on page load: `startDexLogin()` must fire ONLY on explicit user click. Confirm there is no `prompt=none` silent-auth attempt anywhere in the mail login path.
4. Confirm `dex-auth.js` stays LDAP-only (`connector_id=ldap`); do NOT add Google. Keep `clearOidcBrowserState()` so stale `oidc.*` keys can't cause loops.
5. Remove/neutralize any Google / `activate-mail` entry points on the mail LOGIN surface (they belong to the Cloud flow, not mail login). Do not delete the activate backend routes (used by km0-opencloud), only ensure they are not presented as part of mail sign-in.
6. If LDAP OAuth fails at the callback, the user must land back on a usable native password login with a clear message — never a blank/loop. Coordinate with the callback fallback already established (historic #9).
7. Minimal diff; follow `docs/opencloud-registration-integration.md` (LDAP-only on mail hostname). No secrets committed.

## Acceptance criteria
- [x] Native password login is visually primary; LDAP OAuth is a clearly secondary option (moved below the password CTA into an "Other ways to sign in" block, `btn-secondary--muted`).
- [x] Loading `/` or `/login.html` triggers NO automatic OAuth redirect (`startDexLogin()` runs only on explicit click; `curl -sI /` has no `Location`).
- [x] No `connector_id=google` and no `prompt=none` in the mail login path (grep clean; `dex-auth.js` LDAP-only).
- [x] A failed/cancelled LDAP OAuth returns the user to a working native password login with a clear message (Roundcube `oauth_login_redirect=false` fallback from #9; no loop). *(Manual/operator smoke for the interactive path.)*
- [x] No Google/activate CTA is presented on the mail login page (none in `host-www/mail-auth/`).
- [x] Existing OpenCloud/LDAP users can still complete LDAP OAuth into the inbox when they explicitly choose it (`dex-auth.js` unchanged). *(Interactive step is operator smoke, needs IdP creds.)*
- [x] `./scripts/verify-mail-stack.sh` passes; `sudo nginx -t` OK; no secrets committed.

## Implementation notes (coder)
Only the mail login **presentation** changed; no service/backend behavior changed. LDAP OAuth
still works exactly as before when the user explicitly clicks it.

- `host-www/mail-auth/login.html`:
  - The LDAP button now lives inside a dedicated **`.km0-otherways`** block, rendered **below**
    the primary password CTA and the "Create a free account" link, under an **"Other ways to
    sign in"** label (`data-i18n="landingOtherWays"`). Button gets `btn-secondary--muted`
    (smaller, muted). The old co-equal `landing-divider` ("or") divider was removed.
  - `startDexLogin()` is still wired ONLY to the explicit `click` handler on `#km0-ldap-login`.
    There is no OAuth start on page load.
  - Intro copy is now password-first ("Sign in with your mailbox email and password.").
- `host-www/mail-auth/km0-auth.css`: added `.km0-otherways`, `.km0-otherways__label`, and
  `.btn-secondary--muted`; removed the now-unused `.landing-divider`.
- `host-www/mail-auth/km0-auth-i18n.js`: renamed the unused `landingDividerOr` → `landingOtherWays`
  (en/es/ca/de) and made `loginIntro` password-first (en/es/ca/de). `ldapButton`/`ldapHint`
  kept as-is (brief redirect to `cloud.km0digital.com`).
- `host-www/mail-auth/dex-auth.js`: **unchanged** — still LDAP-only (`connector_id: 'ldap'`, no
  Google), still calls `clearOidcBrowserState()` to purge stale `oidc.*` keys, and only runs on
  explicit click. No `prompt=none` anywhere.
- **Failed/cancelled OAuth fallback:** unchanged and already established (#9). Roundcube
  `config/roundcube/config.inc.php` sets `$config['oauth_login_redirect'] = false;`, so the
  `/index.php/login/oauth` callback with an error lands on Roundcube's native email+password
  form (no auto re-trigger, no loop). No Google/`activate` CTA exists on the mail login surface.
- Deploy: `sudo rsync -a host-www/mail-auth/ /var/www/mail-auth/ && sudo nginx -t && sudo systemctl reload nginx`
  (no `nginx/sites-available/mail` change was required for this FEAT).

## Testing instructions
Run from repo root on the VPS. Real output captured 2026-08-01 (UTC) after deploy + reload.

1. No auto-redirect on load (native login served, not an OAuth/hub redirect):
   ```bash
   curl -sI https://mail.km0digital.com/ | grep -i location || echo 'no auto redirect (good)'
   curl -so /dev/null -w '/ %{http_code}\n' https://mail.km0digital.com/
   ```
   Observed:
   ```
   no auto redirect (good)
   / 200
   ```
2. LDAP is present but visually secondary — it renders AFTER the primary password CTA, inside
   the "Other ways to sign in" block with the muted button class:
   ```bash
   curl -s https://mail.km0digital.com/ | grep -oiE 'passwordButton|landingOtherWays|btn-secondary--muted|km0-ldap-login'
   ```
   Observed (order confirms password first, LDAP demoted):
   ```
   passwordButton
   landingOtherWays
   btn-secondary--muted
   km0-ldap-login
   km0-ldap-login
   ```
3. No `connector_id=google` and no `prompt=none` in the mail login path (source + served):
   ```bash
   grep -RniE 'connector_id=google|prompt=none' host-www/mail-auth/ && echo 'FOUND (bad)' || echo 'none (good)'
   curl -s https://mail.km0digital.com/dex-auth.js | grep -c "connector_id: 'ldap'"
   ```
   Observed: `none (good)`; `1` (LDAP connector only).
4. LDAP start only on click (manual): open the page; it stays on the native form until the
   "Sign in with OpenCloud / LDAP" button is clicked, then 302s to
   `cloud.km0digital.com/dex/auth?...&connector_id=ldap`.
5. Failed/cancelled OAuth returns to native login (manual): cancel at Dex; because Roundcube
   `oauth_login_redirect=false`, the callback lands on the native email+password form with an
   error (no loop, no blank page).
6. Existing LDAP user explicit OAuth reaches inbox (operator smoke, needs IdP creds).
7. Stack health:
   ```bash
   ./scripts/verify-mail-stack.sh   # -> "All critical checks passed." (exit 0)
   sudo nginx -t                    # syntax ok / test successful
   ```
   Observed: all critical checks passed (only the expected WARN "mail login.html not redirecting
   to auth hub", which the docs-verify-stack FEAT flips to native-first); `nginx -t` successful.

## Test report (tester)

- **Date/time (UTC):** 2026-08-01 23:58–23:59 UTC.
- **Environment:** live VPS stack, `docker compose` project `km0-mail`; branch `main` (synced); target `https://mail.km0digital.com/` and `/login.html`; served `dex-auth.js`.
- **What was tested:** the FEAT's Testing instructions — no auto OAuth redirect on load, LDAP demoted to a secondary "Other ways to sign in" block, no Google/`prompt=none` in the mail login path, click-only Dex start, no Google/activate CTA on the login surface, Roundcube fallback config, and stack health.

### Results
- **No auto-redirect on load — PASS.** `curl -sI /` has no `Location` (native login served); `/ 200`, `/login.html 200`.
- **LDAP present but visually secondary — PASS.** Served `/` markup order is `passwordButton` → `landingOtherWays` → `btn-secondary--muted` → `km0-ldap-login` — password CTA first, LDAP demoted into the "Other ways to sign in" block with the muted button class.
- **No `connector_id=google` / `prompt=none` — PASS.** Source grep across `host-www/mail-auth/` → none. Served `dex-auth.js`: `connector_id: 'ldap'` count = 1; google/`prompt=none` count = 0 (LDAP-only).
- **Dex starts only on explicit click — PASS.** `login.html` calls `window.KM0DexAuth.startDexLogin()` (line 47) exclusively inside `getElementById('km0-ldap-login').addEventListener('click', …)` (line 46). No page-load / `DOMContentLoaded` auto-start.
- **No Google/activate CTA on the mail login surface — PASS.** grep for `activate-mail|accounts.google.com|Sign in with Google|/sso-continue` (excluding unrelated `fonts.googleapis` font links) → none.
- **Failed/cancelled OAuth returns to native login — PASS (config).** `config/roundcube/config.inc.php`: `$config['oauth_login_redirect'] = false;` (#9 fallback), so the `/index.php/login/oauth` error callback lands on the native email+password form (no loop). The interactive cancel path is operator smoke.
- **Stack health — PASS.** `verify-mail-stack.sh` → "All critical checks passed." (exit 0); `nginx -t` successful.
- **Existing LDAP user explicit OAuth into inbox — operator smoke** (needs IdP creds; `dex-auth.js` unchanged and LDAP-only, wired to explicit click).

- **Overall: PASS.**
- **URLs tested:** `https://mail.km0digital.com/`, `/login.html`, `/dex-auth.js`.
- **Evidence:** served-markup order (`passwordButton`, `landingOtherWays`, `btn-secondary--muted`, `km0-ldap-login`); `dex-auth.js` `connector_id: 'ldap'` ×1, google/prompt=none ×0; `oauth_login_redirect = false`.
