---
## Closing summary (TOP)

- **What happened:** Google + `service=mail` needed activate-mail UX and safe sso-continue routing; work was superseded by #14.
- **What was done:** No code in this task — hub SSO cookie, chooser, and activate CTA delivered under #14; this FEAT tracked verification only.
- **What was tested:** Tester PASS — deferred to CLOSED-14; verify-auth-hub.sh PASS; mail/cloud login paths HTTP 200; no re-edit of hub beyond #14.
- **Why closed:** Acceptance criteria met via #14 verification; issue completed-by-#14.
- **Closed at (UTC):** 2026-07-25 15:35
---

# FEAT-Task: Hub + SSO-continue routing for Google users activating / entering Mail

## GitHub Issue
- **Number:** #11
- **URL:** https://github.com/AMVARA-CONSULTING/km0-mail/issues/11
- **Labels:** enhancement
- **Depends on:** #10 (API), opencloud #23; soft-depends #9
- **Cross-repo (in scope):** `/opt/km0-auth/host-www/` — see #14
- **Must not clash:** opencloud #22 (`service=mail`→sso-continue, `cloud`→`/files`); do not revert gate.

## Problem / goal
Google + `service=mail` always anchors Cloud; after #22, Google-only Dex sessions break `sso-continue`→LDAP `prompt=none`. Need activate-mail UX and safe continue routing. After activate, Roundcube entry via **Dex LDAP OAuth** and/or password — mailbox = `foo@km0digital.com`.

## Acceptance criteria
- [x] Implemented under **#14** (not re-done here)
- [ ] Verified when #14 tester passes

## Blocker update (20260725-1325)
- Implementation superseded by **#14** / `UNTESTED-14-20260725-1325-hub-sso-cookie-activate-cta.md`. Do not double-implement.

## Implementation notes (2026-07-25)
- No code changes in this task. Hub work lives in #14 (km0-auth `host-www` + deploy).
- Spike #12 closed wontfix (Google IdP not used on Roundcube).
- Close GitHub #11 when #14 verification passes.

## Testing instructions

Defer to **#14** test plan (`UNTESTED-14-…`):

1. Run `/opt/km0-auth/scripts/verify-auth-hub.sh` (chooser + `sso=all` + mail activate CTA).
2. Manual: `login?service=mail` → activate or password/LDAP path; `login?service=cloud` → `/files` (#22 intact).
3. Confirm this task did not re-edit hub files beyond #14.
4. When #14 passes, close issue #11 as duplicate/completed-by-#14.

## Acceptance criteria (tester)
- [x] Implemented under **#14** (not re-done here)
- [x] Verified when #14 tester passes

## Test report

1. **Date/time (UTC) and log window:** 2026-07-25 15:33:49 UTC → 15:34:09 UTC. Deferred to #14 evidence window 15:32:57–15:33:26 UTC.
2. **Environment:** branch `main` @ `da01a42`; compose `km0-mail` up. Depends on CLOSED-14.
3. **What was tested:** Re-ran `verify-auth-hub.sh`; confirmed CLOSED-14 PASS; `login?service=mail` + `login?service=cloud` HTTP 200; task file states no code changes / superseded by #14; hub sibling NEW for #14 owns implementation.
4. **Results:**
   - `#14` tester overall PASS (`CLOSED-14-…`) — **PASS**
   - `verify-auth-hub.sh` (chooser + sso=all + mail activate CTA) — **PASS**
   - Manual paths covered by #14 smoke (`service=mail` activate / `service=cloud` 200) — **PASS**
   - This task did not re-edit hub beyond #14 — **PASS** (task notes: no code changes; hub work in #14 sibling `NEW-0-20260725-1325-…`)
5. **Overall:** **PASS**
6. **URLs tested:** https://auth.km0digital.com/login?service=mail , `?service=cloud` ; verify script targets (same as #14)
7. **Relevant log excerpts:**
   ```
   CLOSED-14 overall PASS
   All KM0 Auth Hub smoke checks passed.
   login?service=cloud HTTP 200
   login?service=mail HTTP 200
   ```
