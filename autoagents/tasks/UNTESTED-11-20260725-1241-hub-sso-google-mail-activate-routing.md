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
