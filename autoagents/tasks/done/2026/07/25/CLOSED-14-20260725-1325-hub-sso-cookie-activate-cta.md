---
## Closing summary (TOP)

- **What happened:** Auth hub never set `sso=all`, so Google-only sessions broke silent LDAP sso-continue and had no activate CTA for mail.
- **What was done:** Cross-repo hub updates (`sso=all` for lobby/mail, chooser without auto prompt=none, activate CTA + i18n), verify-auth-hub smoke, deploy, and km0-mail docs; completes #11 goals.
- **What was tested:** Tester PASS — deploy + 9 smoke checks, live hub-auth/sso-continue/activate-mail, cloud-only #22 intact, docs, no secrets, stack healthy.
- **Why closed:** All acceptance criteria passed under testing.
- **Closed at (UTC):** 2026-07-25 15:35
---

# FEAT-Task: Hub SSO cookie (sso=all) + Google-safe sso-continue + activate CTA

## GitHub Issue
- **Number:** #14
- **URL:** https://github.com/AMVARA-CONSULTING/km0-mail/issues/14
- **Labels:** enhancement
- **Supersedes / completes:** #11 (implement #11 goals here; leave #11 comment pointing to this FEAT)
- **Blocked until:** opencloud #24 (identity) + #25 (cloud wizard) have a clear API/URL; soft-block #9 for silent OAuth
- **Cross-repo:** `/opt/km0-auth/host-www/*` + sibling NEW in km0-auth/tasks

## Problem / goal
Hub never sets `sso=all` → no `km0_sso_continue`; Google-only + #22 sso-continue → LDAP prompt=none fails; no activate CTA.

## High-level instructions for coder
1. Sync; read #11 FEAT + km0-auth hub files + cloud wizard URL from #25
2. `startCloudLogin`: pass `sso=all` when product requires mail follow-through (or always for hub global login — document choice)
3. `sso-continue`: if Google-only / silent LDAP fail → activate wizard or password Roundcube (no loop)
4. `service=mail` + no mailbox → deep-link cloud `/activate-mail.html` (or final path from #25)
5. i18n; deploy-auth-hub; sibling NEW; FEAT→UNTESTED; comment #11+#14

## Acceptance criteria
- [x] SSO cookie set when expected
- [x] Google-only mail intent safe (activate/password)
- [x] #22 cloud→/files intact; no secrets

## Implementation notes (2026-07-25)

**`sso=all` choice:** pass on unified lobby login (no `?service=`) and `?service=mail`; **not** on `?service=cloud` alone (keeps session-gate cloud→`/files` without Mail bounce).

**Cross-repo (`/opt/km0-auth`):**
- `host-www/hub-auth.js` — `wantsMailFollowThrough`, `startCloudLogin(..., { ssoAll })`, `ACTIVATE_MAIL_URL` / `goActivateMail` / password helpers
- `host-www/sso-continue.html` — chooser (LDAP OAuth / Activate / password); **no** auto `prompt=none`
- `host-www/login.html` — activate block when `service=mail`
- `host-www/i18n.js` — CA/ES/EN/DE strings
- `scripts/verify-auth-hub.sh` — smoke for chooser + `sso=all` + mail activate CTA
- `README.md` SSO section updated; sibling `tasks/NEW-0-20260725-1325-hub-sso-cookie-and-activate-cta.md`

**km0-mail docs:** CHANGELOG + runbook hub SSO note. Deployed via `deploy-auth-hub.sh`.

Canonical activate deep-link: `https://cloud.km0digital.com/activate-mail.html`

## Testing instructions

1. Deploy + smoke (from km0-auth):
   ```bash
   sudo /opt/km0-auth/scripts/deploy-auth-hub.sh
   /opt/km0-auth/scripts/verify-auth-hub.sh
   ```
   Expect PASS including `/sso-continue chooser`, `/hub-auth.js sso=all + activate URL`, `/login?service=mail activate CTA`.

2. Confirm live assets:
   ```bash
   curl -sS https://auth.km0digital.com/hub-auth.js | grep -E "wantsMailFollowThrough|activate-mail.html|set\\('sso'"
   curl -sS https://auth.km0digital.com/sso-continue | grep -E 'km0-sso-activate|km0-sso-ldap-oauth'
   curl -sS -o /dev/null -w '%{http_code}\n' https://cloud.km0digital.com/activate-mail.html
   ```

3. Manual — unified / mail follow-through (`sso=all`):
   - Open `https://auth.km0digital.com/` → 「Iniciar sesión en KM0」 (LDAP) or `https://auth.km0digital.com/login?service=mail` → Google.
   - After Cloud login, browser should hit `/sso-continue` (cookie path) and show the chooser — **not** an immediate silent OAuth redirect.
   - Activate → `https://cloud.km0digital.com/activate-mail.html`; password link → Roundcube login; LDAP OAuth → Roundcube OAuth start (no `prompt=none`).

4. Manual — cloud-only (#22 intact):
   - `https://auth.km0digital.com/login?service=cloud` → Google/LDAP → land in OpenCloud `/files` **without** forced Mail continue (`sso=all` must not be set for cloud-only).

5. Docs:
   ```bash
   grep -n 'sso=all\|sso-continue' /opt/km0-mail/docs/runbook.md /opt/km0-mail/docs/CHANGELOG.md
   ```

6. No secrets in hub files; mail stack unchanged (`docker compose ps` still healthy).

## Test report

1. **Date/time (UTC) and log window:** 2026-07-25 15:32:57 UTC → 15:33:26 UTC. Mail compose logs sampled ~15:17–15:33 UTC; hub redeployed 15:33:03 UTC.
2. **Environment:** branch `main` @ `da01a42`; compose project `km0-mail` (postfix/dovecot/rspamd/roundcube/postgres/mail-provision-api up). URLs: `https://auth.km0digital.com/`, `https://cloud.km0digital.com/activate-mail.html`, `https://mail.km0digital.com/`. Stack ready via: `docker compose ps` all Up; `curl -sI https://mail.km0digital.com/` → HTTP/2 302 to hub login; MX/A + ports 25/587/993 OK; auth hub smoke EXIT 0 after deploy.
3. **What was tested:** `deploy-auth-hub.sh` + `verify-auth-hub.sh`; live hub-auth.js / sso-continue / activate-mail.html; login?service=mail activate CTA HTML; `wantsMailFollowThrough` cloud-only logic; docs runbook/CHANGELOG; secrets scan; compose health.
4. **Results:**
   - Deploy + smoke (`verify-auth-hub.sh`) — **PASS** (all 9 checks; EXIT 0; chooser + `sso=all` + mail activate CTA)
   - Live `hub-auth.js` (`wantsMailFollowThrough`, `activate-mail.html`, `params.set('sso','all')`) — **PASS**
   - Live `/sso-continue` chooser buttons (`km0-sso-activate`, `km0-sso-ldap-oauth`) — **PASS**; no auto `prompt=none` redirect (comment + click handlers only)
   - `activate-mail.html` HTTP 200 — **PASS**
   - `login?service=mail` activate block (`km0-mail-activate-block` shown when `service === 'mail'`) — **PASS**
   - Cloud-only #22 (`wantsMailFollowThrough`: `!svc || svc === 'mail'` — not for `service=cloud`) — **PASS** (code + live JS; interactive Google→/files not re-run this window)
   - Docs `sso=all` / `sso-continue` in runbook + CHANGELOG — **PASS** (runbook:170, CHANGELOG:9)
   - No secrets in hub files; mail stack healthy — **PASS** (id_token_hint only; compose all Up)
5. **Overall:** **PASS**
6. **URLs tested:** https://auth.km0digital.com/ , `/login?service=mail`, `/sso-continue`, `/hub-auth.js`, `/i18n.js`; https://cloud.km0digital.com/activate-mail.html ; https://mail.km0digital.com/ (302→hub)
7. **Relevant log excerpts:**
   ```
   KM0 Auth Hub deployed to /var/www/km0-auth
   PASS: /sso-continue chooser HTTP 200
   PASS: /hub-auth.js sso=all + activate URL
   PASS: /login?service=mail activate CTA present
   All KM0 Auth Hub smoke checks passed.
   curl activate-mail.html → 200
   mail.km0digital.com → HTTP/2 302 → auth login?service=mail
   nc 25/587/993 → succeeded
   ```
