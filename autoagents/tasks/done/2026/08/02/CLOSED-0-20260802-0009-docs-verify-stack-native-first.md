---
## Closing summary (TOP)

- **What happened:** Docs and `verify-mail-stack.sh` were realigned to native-first login, replacing the stale hub-first (`/` → 302 to Auth Hub) expectations.
- **What was done:** Updated `docs/runbook.md`, `docs/opencloud-registration-integration.md`, `README.md`, and `docs/CHANGELOG.md` to document native password login at `/` and the self-contained `/api/register` (:8092) as canonical (hub SSO marked optional/legacy); updated the smoke script to expect login HTML (200) at `/` and a 400 from public `/api/register`.
- **What was tested:** All 6 acceptance criteria PASS — smoke script exits 0 ("All critical checks passed"), root serves 200 text/html (no hub 302), public `/api/register` returns 400, CHANGELOG entry present, no secrets committed, `bash -n` syntax OK.
- **Why closed:** All acceptance criteria passed on the live stack; docs-only + script change with no service behavior impact.
- **Closed at (UTC):** 2026-08-02 00:14
---

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

All commands run from repo root `/opt/km0-mail` on the mail host. Real output captured 2026-08-02 (UTC) below.

1. Run the updated smoke script and confirm the root check passes on native login:
   ```bash
   ./scripts/verify-mail-stack.sh
   curl -sI https://mail.km0digital.com/ | head   # 200 text/html, not 302 to hub
   ```
   Observed — script exited `0` ("All critical checks passed") with the two changed checks:
   ```text
   --- Registration APIs ---
   [OK]   public /api/register responds 400 on empty body (self-contained :8092)
   --- Native login (root) ---
   [OK]   https://mail.km0digital.com/ serves native login page (200 text/html)
   ```
   And the direct root header:
   ```text
   HTTP/2 200
   server: nginx
   content-type: text/html
   content-length: 2850
   ```
   (No `Location:` to `auth.km0digital.com` — native login is served directly.)
2. Grep docs for stale hub-first instructions:
   ```bash
   grep -RniE 'redirect(s)? to (the )?Auth Hub|/ .*302.*auth\.km0digital' docs/ README.md || echo 'clean'
   ```
   Observed — only two matches remain, both **historical `docs/CHANGELOG.md` entries** for past releases (line 39/41) documenting the now-superseded hub-first behavior. The runbook, README, and opencloud integration doc contain no stale operational hub-first instruction.
3. Public register check referenced by the script responds:
   ```bash
   curl -s -o /dev/null -w '%{http_code}\n' -X POST https://mail.km0digital.com/api/register -H 'Content-Type: application/json' -d '{}'
   # Expect 400 (validation), proving the public endpoint is wired (not :8091)
   ```
   Observed:
   ```text
   400
   ```
4. `docs/CHANGELOG.md` shows the new entry (`git diff`) under `[Unreleased] → Changed`: "Docs + smoke script aligned to native-first login (Redmine #7605)…".

## Notes for tester
- Docs-only + smoke script; no service behavior changed.
- FEAT #0 is a local task with no GitHub issue, so no `gh issue comment`/label steps apply.
- `bash -n scripts/verify-mail-stack.sh` passes (syntax OK).

## Test report

1. **Date/time (UTC) & window:** run 2026-08-02 00:13–00:14 UTC on the mail host (`/opt/km0-mail`, branch `main`, synced clean via `git-sync-main.sh` — "Already up to date"). Log window: live containers up 6 weeks–7 days; APIs restarted ~30–50 min prior.
2. **Environment:** Docker Compose project `km0-mail`; all services `Up` (postgres, postfix, dovecot, rspamd, roundcube, mail-provision-api :8092, domain-verify-api :8093). URLs: `https://mail.km0digital.com/`, `/api/register`.
3. **What was tested:** the 4 documented steps + the 6 acceptance criteria — smoke script native-login/register checks, root header, stale-hub grep, public register 400, CHANGELOG entry, doc diffs, script syntax, no secrets.
4. **Results (per criterion):**
   - **PASS** — `runbook.md` documents native password login at `/` as canonical; hub SSO marked **OPTIONAL/LEGACY**; URL table now says `/` and `/login.html` serve native login (no `302`-to-hub instruction). Evidence: `git diff` runbook (URL table + auth-tracks rewritten).
   - **PASS** — `opencloud-registration-integration.md` top note + Nginx section state native signup does **not** require register-api (:8091); :8091 kept as optional Cloud path. Evidence: diff hunks lines 1/54.
   - **PASS** — `README.md` reflects native-first login (`/` branded page, self-contained `/api/register` → :8092, SSO optional/legacy). Evidence: README diff.
   - **PASS** — `verify-mail-stack.sh` expects login HTML (200) at `/` and no longer treats a hub `302` as success; runs clean. Evidence: `./scripts/verify-mail-stack.sh` → exit `0`, "All critical checks passed":
     ```text
     --- Registration APIs ---
     [OK]   public /api/register responds 400 on empty body (self-contained :8092)
     --- Native login (root) ---
     [OK]   https://mail.km0digital.com/ serves native login page (200 text/html)
     ```
   - **PASS** — `CHANGELOG.md` has the login-simplification entry under `[Unreleased] → Changed` (line 8). The only two `grep` hits for hub-redirect wording are **historical** entries in an older CHANGELOG release section (lines 39/41), not operational instructions — matches task expectation.
   - **PASS** — No secrets committed (docs + shell script only; diff reviewed).
   - **PASS (support)** — `bash -n scripts/verify-mail-stack.sh` → syntax OK.
5. **Overall: PASS.**
6. **URLs tested:** `https://mail.km0digital.com/` (HTTP/2 `200`, `content-type: text/html`, `content-length: 2850`, no `Location:` to `auth.km0digital.com`); `POST https://mail.km0digital.com/api/register` empty body → `400`.
7. **Relevant log excerpts:**
   ```text
   $ curl -sI https://mail.km0digital.com/ | head
   HTTP/2 200
   server: nginx
   content-type: text/html
   content-length: 2850

   $ curl -s -o /dev/null -w '%{http_code}\n' -X POST https://mail.km0digital.com/api/register -H 'Content-Type: application/json' -d '{}'
   400

   $ grep -RniE 'redirect(s)? to (the )?Auth Hub|/ .*302.*auth\.km0digital' docs/ README.md
   docs/CHANGELOG.md:39:- Nginx: `/`, `/login.html`, and `/register` redirect to Auth Hub ...   # historical release entry
   docs/CHANGELOG.md:41:- verify-mail-stack: expect `/login.html` redirect to Auth Hub          # historical release entry
   ```
   verify-mail-stack.sh: all sections `[OK]`, exit `0`.

**Verdict: PASS** — docs + smoke script align with native-first login; smoke script passes green on the live stack.
