# FEAT-Task: SPIKE — Optional Google IdP directly into Roundcube mapped to foo@km0digital.com

## GitHub Issue
- **Number:** #12
- **URL:** https://github.com/AMVARA-CONSULTING/km0-mail/issues/12
- **Labels:** enhancement
- **Blocked until:** #10, #11, and #9 have a clear path (LDAP OAuth works). This must not block them.

## Problem / goal
Desire: Google button opens Roundcube as IMAP `foo@km0digital.com`. Hard blockers: Roundcube ignores `oauth_login` username rewrite; Dovecot email attribute must match token email (Gmail ≠ mailbox).

## High-level instructions for coder
1. Do **design first** in `docs/` (sequence diagram + options A patch+map / B token-exchange PLAIN / C wontfix keep LDAP-only).
2. Implement PoC only if A/B chosen and flagged; never break password or LDAP OAuth.
3. If C: close spike with rationale; hub copy already points to activate + LDAP OAuth.

## Acceptance criteria
- [x] Design decision documented
- [x] PoC or explicit wontfix; no regression on password / LDAP OAuth

## Blocker update (20260725-1325)
- Foundations #9 / #13 / #14 and opencloud #24 / #25 were UNTESTED with a clear path — design-first started.

## Implementation notes (2026-07-25)
- **Decision: Option C — wontfix.**
- Design doc: `docs/spike-google-idp-roundcube-mailbox-map.md` (sequence diagram, options A/B/C, Roundcube 1.6.9 hook discard verified in container).
- No code/PoC: Roundcube discards `oauth_login` return; Dovecot `username_attribute=email` requires token email = mailbox; product already excludes Google on Roundcube.
- Docs updated: CHANGELOG, `agent-pipeline-mail-activate.md`, `issue-mail-registration-preplan.md`, `opencloud-registration-integration.md`, `runbook.md`.
- Stack unchanged — password + Dex LDAP OAuth paths untouched.

## Testing instructions

Docs-only / no-regression checks:

1. Design doc exists and states **Option C**:
   ```bash
   test -f /opt/km0-mail/docs/spike-google-idp-roundcube-mailbox-map.md
   grep -E 'Decision C|wontfix|Option C' /opt/km0-mail/docs/spike-google-idp-roundcube-mailbox-map.md
   ```

2. Roundcube still forces LDAP connector (no Google):
   ```bash
   grep "connector_id" /opt/km0-mail/config/roundcube/config.inc.php
   # expect: ldap only
   ```

3. Confirm Roundcube still discards hook rewrite (regression guard for future image bumps):
   ```bash
   docker compose exec -T roundcube sed -n '290,310p' /var/www/html/program/include/rcmail_oauth.php
   # expect: exec_hook('oauth_login'…) then return pre-hook $username
   ```

4. Stack healthy; password path still up:
   ```bash
   docker compose ps
   curl -sI https://mail.km0digital.com/ | head -n 5
   ```

5. Pipeline pointer:
   ```bash
   grep -n 'wontfix\|spike-google' /opt/km0-mail/docs/agent-pipeline-mail-activate.md /opt/km0-mail/docs/CHANGELOG.md
   ```

6. No secrets committed; no Dovecot/Roundcube auth behaviour changed by this spike.
