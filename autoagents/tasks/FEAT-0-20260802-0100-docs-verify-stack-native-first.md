# FEAT: Docs + stack verification reflect native-first login

## GitHub Issue
- **Issue:** N/A (local FEAT, no GitHub issue — generated directly)
- **Number:** #0
- **Redmine:** #7605 (tracking)
- **Priority:** medium
- **Depends on:** FEAT native-login-canonical, self-contained-registration, verification-first-login, ldap-oauth-optional

## Problem / goal
After the login simplification, the docs and the smoke script still describe/expect the old hub-first behavior (e.g. `/` → `302` to `auth.km0digital.com`). This is misleading and will cause the tester and future operators to "fix" the new behavior back to the maze.

**Goal:** update documentation and `verify-mail-stack.sh` so native-first login is the documented canonical path, and the hub/Dex SSO is clearly marked optional/legacy.

## Current state (files)
- `docs/runbook.md`: "Branded auth → KM0 Auth Hub"; URL table says `/` and `/login.html` redirect to the Auth Hub; describes the activate/sso-continue path (issue #14/#15).
- `docs/opencloud-registration-integration.md`: register-api (:8091) as the signup backend, hub SSO.
- `README.md`: high-level status.
- `scripts/verify-mail-stack.sh`: at the end it checks `https://mail.km0digital.com/` and (per closed tasks) expected a `302` to the Auth Hub; also checks `domain-verify-api` health, DB tables, ports.

## High-level instructions for coder
1. Run `./scripts/git-sync-main.sh` before edits.
2. `docs/runbook.md`:
   - Replace the "Branded auth → KM0 Auth Hub" section and the URL table so `/` and `/login.html` serve the native branded login (no hub redirect). Document native password login as the canonical path.
   - Document the self-contained `/register` → `mail-provision-api` public endpoint (FEAT self-contained-registration) instead of the :8091 register-api for the happy path.
   - Mark hub SSO / `/sso-continue` / activate as OPTIONAL/LEGACY (Cloud users), not the default.
   - Keep the custom-domain (Model B) wizard docs; they are extended by FEAT custom-domain.
3. `docs/opencloud-registration-integration.md`: add a note at the top that the native mail signup path no longer requires km0-opencloud register-api; keep the cross-repo details as the optional Cloud-linked path.
4. `README.md`: update the Status/summary to reflect native-first login.
5. `scripts/verify-mail-stack.sh`: change the root check so it EXPECTS the login page (HTTP 200 branded HTML) at `/`, NOT a `302` to `auth.km0digital.com`. Keep all other critical checks. Add a check that `/api/register` (public) responds (e.g. 400 on empty body) rather than proxying to :8091.
6. `docs/CHANGELOG.md`: add an entry summarizing the login simplification series.
7. Docs-only + script; no behavior change to services. Minimal diff; no secrets committed.

## Acceptance criteria
- [ ] `docs/runbook.md` documents native password login at `/` as canonical; hub SSO marked optional/legacy; no stale "`/` → 302 hub" instruction.
- [ ] `docs/opencloud-registration-integration.md` notes native signup does not require register-api (:8091).
- [ ] `README.md` reflects native-first login.
- [ ] `scripts/verify-mail-stack.sh` expects login HTML (200) at `/` and no longer treats a hub `302` as the success condition; it still passes on the updated stack.
- [ ] `docs/CHANGELOG.md` has a login-simplification entry.
- [ ] No secrets committed.

## Testing instructions
(to be completed by coder before UNTESTED-; include real output)

1. Run the updated smoke script and confirm the root check passes on native login:
   ```bash
   ./scripts/verify-mail-stack.sh
   curl -sI https://mail.km0digital.com/ | head   # 200 text/html, not 302 to hub
   ```
2. Grep docs for stale hub-first instructions:
   ```bash
   grep -RniE 'redirect(s)? to (the )?Auth Hub|/ .*302.*auth\.km0digital' docs/ README.md || echo 'clean'
   ```
3. Public register check referenced by the script responds:
   ```bash
   curl -s -o /dev/null -w '%{http_code}\n' -X POST https://mail.km0digital.com/api/register -H 'Content-Type: application/json' -d '{}'
   # Expect 400 (validation), proving the public endpoint is wired (not :8091)
   ```
4. `docs/CHANGELOG.md` shows the new entry (`git diff`).
