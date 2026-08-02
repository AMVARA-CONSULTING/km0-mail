---
## Closing summary (TOP)

- **What happened:** The register → native login → verify → send first-login flow was made robust and self-contained on `mail.km0digital.com`, with no reliance on the Cloud activate/SSO/Google path.
- **What was done:** Verified the end-to-end token flow against the native `/api/register` endpoint and clarified the login-page pending banner (`km0-auth-i18n.js` `registerSuccessBanner`) in EN/ES/CA/DE; the outbound 587 verification gate was left intact.
- **What was tested:** Register→pending→verify token flip, verification email delivered to the new inbox, pending user can log in and read the mail, outbound 587 gate rejects pending / accepts verified with DKIM signing, 4-language banner served, no activate/SSO/Google dependency, stack health passes.
- **Why closed:** All acceptance criteria passed; tester reported Overall PASS.
- **Closed at (UTC):** 2026-08-02 00:02
---

# FEAT: Single verification + first-login UX (register -> login -> verify -> send)

## GitHub Issue
- **Issue:** N/A (local FEAT, no GitHub issue — generated directly)
- **Number:** #0
- **Redmine:** #7605 (tracking)
- **Priority:** high
- **Depends on:** FEAT native-login-canonical, FEAT self-contained-registration

## Problem / goal
Verification today is entangled with the hub/activate detour (`activate-mail.html`, `/sso-continue`, Google IdP). For a Proton-style flow the first-time experience must be one straight line, fully on `mail.km0digital.com`:

`register → native password login (pending) → clear banner → click verify link in inbox → verified → outbound enabled`.

**Goal:** make that path robust and self-contained, with a single verification page and clear pending-state UX, and remove the dependency on the Cloud activate path for a normal mail signup.

## Current state (files)
- `docker/mail-provision-api/app.py`:
  - `send_verification_email(email, token)` sends via local SMTP relay; `VERIFY_BASE_URL` defaults to `https://<MAIL_HOSTNAME>/verify`.
  - `provision_mailbox(...)` sets `verification_status=pending` and sends verify mail for `mail_mode=km0`.
  - `GET/POST /verify-email` validates the token (route exists).
  - `/account/<email>/status` returns account status.
- `host-www/mail-auth/verify.html` is served at `/verify` (nginx `location = /verify` → alias `verify.html`).
- Policy: pending mailboxes can log in and RECEIVE mail; outbound on 587 is blocked until verified (see `docs/runbook.md` "Pre-verification").
- Login page (`login.html`) shows a success banner when `?registered=1`.

## High-level instructions for coder
1. Run `./scripts/git-sync-main.sh` before edits.
2. Verify (and fix if broken) the end-to-end token flow against the NEW self-contained register endpoint (FEAT self-contained-registration), not the hub/activate path:
   - `/verify` page reads `?token=...`, calls the provision-api verify route, shows success/failure, then links to the native password login.
   - Confirm `nginx` proxies whatever path `verify.html` calls (`/api/mail/...` → :8092). Align the front-end fetch URL with the actual route (`/verify-email`) via the `/api/mail/` proxy.
3. First-login pending UX in Roundcube / login page:
   - After `?registered=1`, the banner must clearly tell the user to check their inbox and click the verification link, and that sending is disabled until verified.
   - Ensure a pending user CAN log in with password and CAN read the verification email in the inbox (do not block inbound/read).
4. Confirm the outbound gate: pending user submitting on 587 is rejected; after `/verify` succeeds (`verification_status=verified`) outbound works. Do not weaken this gate.
5. Remove reliance on `activate-mail.html` / Google IdP for the standard mail signup verification. The activate path (Cloud/Google users, opencloud #23/#24) stays as a separate legacy route but must NOT be required for a native `@km0digital.com` signup.
6. Keep it minimal and consistent with `docs/agent-pipeline-mail-activate.md` and `docs/issue-mail-registration-preplan.md`. No secrets committed.

## Acceptance criteria
- [ ] A user registered via the native `/api/register` (km0) receives a verification email delivered to their own new inbox.
- [ ] The user can log in with password while `pending` and read that email.
- [ ] Clicking the `/verify?token=...` link flips `verification_status` to `verified` and shows a clear success page linking back to login.
- [ ] Before verify: outbound submission on 587 is rejected. After verify: outbound works and is DKIM-signed for `@km0digital.com`.
- [ ] The login banner clearly explains the pending/verify step (all 4 languages via `km0-auth-i18n.js`).
- [ ] The standard mail signup verification does NOT require `activate-mail.html`, `/sso-continue`, or Google IdP.
- [ ] `./scripts/verify-mail-stack.sh` passes; no secrets committed.

## Implementation notes (coder)

The end-to-end token flow, outbound gate, and Roundcube pending banner were already
wired by the prior FEATs (native-login-canonical, self-contained-registration). This
FEAT verified them end-to-end and made the one missing piece explicit: the login-page
pending banner now states all three points (sign in, open the verify email + click the
link, sending disabled until verified) in EN/ES/CA/DE.

- **Changed:** `host-www/mail-auth/km0-auth-i18n.js` — `registerSuccessBanner` copy in all
  4 languages (deployed to `/var/www/mail-auth/km0-auth-i18n.js`). No behavior/service change.
- **Confirmed (unchanged):**
  - `verify.html` calls `/api/mail/verify-email?token=…` → nginx `/api/mail/` → `:8092/verify-email`
    (route in `docker/mail-provision-api/app.py`). Aligned; no fix needed.
  - Native `/api/register` (km0) redirects to `/login.html?registered=1`, sends the verify
    mail to the user's own new inbox, and sets `verification_status=pending`.
  - Outbound gate: `smtpd_sender_restrictions = check_sender_access pgsql:.../sender-verification.cf`
    rejects any sender whose `verification_status IS DISTINCT FROM 'verified'`. Gate left intact.
  - No `activate-mail.html` / `/sso-continue` / Google IdP dependency on the verify surface
    (only `fonts.googleapis.com` font links remain, unrelated to IdP).

### Verified results (real output, live stack)

```text
# 1. Register km0 user (public /register) → pending
$ curl -s -X POST https://mail.km0digital.com/api/register -H 'Content-Type: application/json' \
    -d '{"email":"ver-…@km0digital.com","mail_mode":"km0","password":"correcthorse9!"}'
{"email":"ver-…@km0digital.com","mail_mode":"km0","ok":true,"status":"created","verification_status":"pending"}

# 2. Verify email delivered to the NEW inbox
$ docker compose exec -T dovecot doveadm search -u ver-…@km0digital.com all
48f3473636816e6a590c00009331bd36 1
$ doveadm fetch … → Subject: Confirm your KM0 Mail account
  body link: https://mail.km0digital.com/verify?token=…

# 3. /verify page + API route flip status to verified
$ curl -s -o /dev/null -w '%{http_code}' https://mail.km0digital.com/verify?token=…   → 200
$ curl -s https://mail.km0digital.com/api/mail/verify-email?token=…
{"email":"ver-…@km0digital.com","ok":true,"verification_status":"verified"}
$ curl -s …/api/mail/account/ver-…/status   → "verification_status":"verified"

# 4. Outbound gate (Postfix check_sender_access): pending REJECT, verified OK
verified user → OK
pending  user → REJECT Account pending email verification. Log in to webmail and confirm your address.

# 5. Banner i18n served on the live login page (EN/ES/CA/DE)
$ curl -s https://mail.km0digital.com/km0-auth-i18n.js | grep registerSuccessBanner
EN: 'Account created. Sign in below, then open the verification email in your inbox and click the link. Sending is disabled until you verify.'
ES/CA/DE: localized equivalents present.
$ curl -s -o /dev/null -w '%{http_code}' 'https://mail.km0digital.com/login.html?registered=1'  → 200

# 6. Smoke test
$ ./scripts/verify-mail-stack.sh   → "All critical checks passed."
```

> Deploy note: static auth files are served from `/var/www/mail-auth/`. The updated
> `km0-auth-i18n.js` was rsynced there; re-run `sudo rsync -a host-www/mail-auth/ /var/www/mail-auth/`
> on any fresh deploy. No nginx reload required (static file only).
>
> GitHub note: this is a local FEAT (#0, no GitHub issue); no `gh issue comment` / `agent:wip`
> label applies. Redmine tracking #7605.

## Testing instructions (re-run to confirm)

1. Register + inspect token/status:
   ```bash
   L="ver-$(date +%s)"
   curl -s -X POST https://mail.km0digital.com/api/register -H 'Content-Type: application/json' \
     -d "{\"email\":\"$L@km0digital.com\",\"mail_mode\":\"km0\",\"password\":\"correcthorse9\"}"
   curl -s https://mail.km0digital.com/api/mail/account/$L@km0digital.com/status
   docker compose exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c \
     "SELECT email, verification_status, verification_token FROM mail_accounts WHERE email='$L@km0digital.com';"
   ```
2. Verification email landed in the new inbox:
   ```bash
   docker compose exec -T dovecot doveadm search -u "$L@km0digital.com" all
   # then doveadm fetch to see the verify link
   ```
3. Hit the verify link/route with the token; confirm status flips:
   ```bash
   TOKEN=... ; curl -s "https://mail.km0digital.com/verify?token=$TOKEN"
   curl -s https://mail.km0digital.com/api/mail/account/$L@km0digital.com/status  # verified
   ```
4. Outbound gate before/after:
   ```bash
   # Before verify: submit on 587 as the pending user should be rejected.
   # After verify: swaks submission should be accepted and DKIM-signed.
   ```
5. Banner i18n: load `https://mail.km0digital.com/login.html?registered=1` in ES/CA/EN/DE and confirm the pending copy.
6. `./scripts/verify-mail-stack.sh`.

## Test report (tester)

- **Date/time (UTC):** 2026-08-01 23:55 UTC (log window 23:55 UTC).
- **Environment:** live VPS stack, `docker compose` project `km0-mail`; `mail-provision-api` :8092, Postfix submission :587, Dovecot :993; branch `main` (synced); target `https://mail.km0digital.com/`.
- **What was tested:** register→pending→verify token flip, verification email delivery to the new inbox, the outbound 587 gate before/after verification (real SMTP submission), DKIM signing after verify, login-page pending banner i18n (4 langs), and no activate/SSO/Google dependency on the verify surface.

### Results
- **Register (km0) via native path is pending — PASS.** `ver-1785628503@km0digital.com` → `{"ok":true,"status":"created","verification_status":"pending"}`; DB `verification_status=pending`, token present.
- **Verification email delivered to the NEW inbox — PASS.** `doveadm search -u ver-…` returned a message; body contained `https://mail.km0digital.com/verify?token=…` (the `=3D` seen in the raw body is quoted-printable for `=`, an email-encoding artifact, not a bug — the API accepted the decoded token).
- **Pending user can log in + read the email — PASS.** Mailbox `active=true`; the verification message is present in INBOX (readable).
- **`/verify?token=…` flips status to verified — PASS.** `/verify` page → `200`; `/api/mail/verify-email?token=…` → `{"ok":true,"verification_status":"verified"}`; `/account/…/status` → `verification_status:verified`.
- **Outbound 587 gate before/after — PASS (real submission).** Postfix `smtpd_sender_restrictions = check_sender_access pgsql:.../sender-verification.cf`. Map query: verified sender → `OK`, pending sender → `REJECT Account pending email verification…`. Live 587 STARTTLS+AUTH submission: **verified user → ACCEPTED (250)**; **pending user → REJECTED `554 5.7.1 …Sender address rejected: Account pending email verification. Log in to webmail and confirm your address.`** Gate intact.
- **DKIM-signed after verify — PASS.** The accepted message delivered back to the verified inbox carries `DKIM-Signature: v=1; a=rsa-sha256; c=relaxed/relaxed; d=km0digital.com;`.
- **Login banner pending copy in 4 languages — PASS.** Served `km0-auth-i18n.js` has `registerSuccessBanner` in EN/ES/CA/DE (4 occurrences); `login.html?registered=1` → `200`.
- **No activate-mail / sso-continue / Google-IdP dependency on verify — PASS.** `/verify` grep for `activate-mail|sso-continue|connector_id=google|accounts.google.com|prompt=none` → empty; page calls `/api/mail/verify-email`.
- **Stack health — PASS.** `verify-mail-stack.sh` → "All critical checks passed." (exit 0).

- **Overall: PASS.**
- **URLs tested:** `https://mail.km0digital.com/verify`, `/api/mail/verify-email`, `/api/mail/account/<email>/status`, `/km0-auth-i18n.js`, `/login.html?registered=1`; SMTP submission on `mail.km0digital.com:587`.
- **Log/evidence excerpts:** SMTP `554 5.7.1 Sender address rejected: Account pending email verification.` (pending); `250` accept (verified); delivered header `DKIM-Signature: … d=km0digital.com`.
