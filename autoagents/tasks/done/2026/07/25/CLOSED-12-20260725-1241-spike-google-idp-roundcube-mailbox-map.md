---
## Closing summary (TOP)

- **What happened:** Spike #12 evaluated Google IdP → Roundcube mailbox mapping and chose Option C (wontfix).
- **What was done:** Documented decision in `docs/spike-google-idp-roundcube-mailbox-map.md` (options A/B/C, Roundcube hook discard); updated pipeline/CHANGELOG/runbook pointers; no auth code or PoC.
- **What was tested:** Tester PASS — design doc Decision C, Roundcube LDAP-only connector, hook discard confirmed, stack healthy, password path up, no auth regression.
- **Why closed:** All acceptance criteria met (design decision + explicit wontfix; no regression on password / LDAP OAuth).
- **Closed at (UTC):** 2026-07-25 15:26
---

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

## Test report

1. **Date/time (UTC) and log window:** 2026-07-25 15:25:37 UTC → 15:25:57 UTC. Stack readiness / Roundcube localhost login 15:25:47–15:25:57Z.
2. **Environment:** compose project `km0-mail` (postfix/dovecot/rspamd/roundcube/postgres/mail-provision-api/domain-verify-api Up); branch `main` @ `311a625`; URLs `https://mail.km0digital.com/`, `http://127.0.0.1:8080/`. **Stack ready:** poll #1 of `https://mail.km0digital.com/` → HTTP/2 302 to Auth Hub; MX `50 mail.km0digital.com.`; A `116.202.10.106`; `nc` open on 25/587/993; Roundcube `:8080` login HTTP 200.
3. **What was tested:** Design doc Option C / wontfix; Roundcube `connector_id=ldap` only; container `rcmail_oauth.php` hook discard (returns pre-hook `$username`); pipeline + CHANGELOG pointers; compose health + HTTPS/DNS/ports; password path via localhost Roundcube; no auth behaviour change (docs-only spike).
4. **Results:**
   - Design doc exists and states Decision C / wontfix — **PASS** (`docs/spike-google-idp-roundcube-mailbox-map.md`; Status **Decision C — wontfix**; **Option C.** prose)
   - Roundcube forces LDAP connector (no Google) — **PASS** (`oauth_auth_parameters` → `connector_id` => `ldap`)
   - Roundcube discards `oauth_login` username rewrite — **PASS** (`exec_hook('oauth_login'…)` then `return ['username' => $username, …]` with pre-hook `$username`)
   - Stack healthy; password path up — **PASS** (all services Up; HTTPS 302 Auth Hub; `:8080/?_task=login` → 200)
   - Pipeline / CHANGELOG pointers — **PASS** (agent-pipeline step 9 **Done — wontfix**; CHANGELOG SPIKE #12 wontfix)
   - No secrets; no Dovecot/Roundcube auth change by spike — **PASS** (spike added design doc only; config still LDAP-only)
5. **Overall:** **PASS**
6. **URLs tested:** https://mail.km0digital.com/ ; http://127.0.0.1:8080/ ; http://127.0.0.1:8080/?_task=login ; infra MX/A/25/587/993
7. **Relevant log excerpts:**
   ```
   Design: Status Decision C — wontfix; Option C. Do not enable Dex connector_id=google
   config.inc.php: oauth_auth_parameters connector_id => ldap
   rcmail_oauth.php: exec_hook('oauth_login'…) then return username => $username (pre-hook)
   HTTPS mail.km0digital.com/ → 302 location: https://auth.km0digital.com/login?service=mail
   localhost:8080/?_task=login → HTTP/1.1 200 OK
   dovecot: OAuth2/XOAUTH2 enabled (Dex LDAP SSO)
   nc mail.km0digital.com 25/587/993 succeeded
   ```
