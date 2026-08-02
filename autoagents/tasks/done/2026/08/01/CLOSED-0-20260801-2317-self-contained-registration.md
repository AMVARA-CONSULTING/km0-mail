---
## Closing summary (TOP)

- **What happened:** Registration became self-contained on the mail host, removing the cross-repo `km0-opencloud` register-api (`:8091`) dependency for the KM0 happy path.
- **What was done:** Added a public, rate-limited, freemail-blocked `POST /register` route to `mail-provision-api` (reusing `provision_mailbox`), repointed nginx `/api/register` to `:8092`, and kept the token-gated `/provision`/`/activate`/`/link` routes intact.
- **What was tested:** Public km0 register creates a mailbox via `:8092` (not `:8091`), freemail/short-password/empty-body rejected, per-IP rate limit returns 429, verification email delivered, custom mode creates a pending domain row, token-gated route still `401`, stack health passes.
- **Why closed:** All acceptance criteria passed; tester reported Overall PASS.
- **Closed at (UTC):** 2026-08-02 00:02
---

# FEAT: Self-contained registration on the mail host (no cross-repo register-api)

## GitHub Issue
- **Issue:** N/A (local FEAT, no GitHub issue — generated directly)
- **Number:** #0
- **Redmine:** #7605 (tracking)
- **Priority:** high
- **Depends on:** FEAT native-login-canonical (`/register` must already serve the local page)

## Problem / goal
Registration currently posts to `/api/register`, proxied to `127.0.0.1:8091` — the `register-api` that lives in the separate `km0-opencloud` repo. That couples the mail signup happy path to a second repo/service (IDM/LDAP user creation) and is a major source of "it gives errors / goes in circles". For a Proton-style single, solid signup we want registration to be **self-contained on the mail host**.

`docker/mail-provision-api/app.py` (:8092) already can create a mailbox end-to-end (`provision_mailbox()`), send the verification email, and store the password hash — but its `/provision` route is Bearer-token-gated (`auth_ok()`), so it cannot be called directly from the public browser.

**Goal:** add a public, rate-limited, freemail-blocked `/register` endpoint to `mail-provision-api`, proxy it in nginx, and point `register.html` at it — removing the `km0-opencloud` `register-api` dependency for the KM0 (`@km0digital.com`) happy path.

## Current state (files)
- `host-www/mail-auth/register.html` posts JSON to `/api/register` (`fetch('/api/register', ...)`), with `mail_mode` `km0`|`custom`, `desired_email`, `password`, `contact_email`.
- `nginx/sites-available/mail`:
  - `location = /api/register` → `proxy_pass http://127.0.0.1:8091/register;` (km0-opencloud register-api).
  - `location /api/mail/` → `proxy_pass http://127.0.0.1:8092/;` (mail-provision-api).
  - `location /api/mail/domain/` → `proxy_pass http://127.0.0.1:8093/domain/;`.
- `docker/mail-provision-api/app.py`:
  - `/provision` (POST) requires `auth_ok()` (Bearer `MAIL_PROVISION_API_TOKEN`).
  - `provision_mailbox(email, password, opencloud_uuid, mail_mode, contact_email, send_verify=True)` does the real work and is reusable.
  - `validate_mailbox_email()` already blocks freemail and enforces `km0`/`custom` domain rules; `is_freemail_domain()` exists.

## High-level instructions for coder
1. Run `./scripts/git-sync-main.sh` before edits.
2. Add a **public** `POST /register` route in `docker/mail-provision-api/app.py`:
   - No Bearer token required (it is called from the browser), but:
     - Enforce `mail_mode in ("km0","custom")`; reject freemail via existing `validate_mailbox_email()`.
     - Never accept `opencloud_uuid` from the public body (ignore it) — public signups are not IDM-linked here.
     - Require `password` length >= 8; validate local part / email format with existing validators.
     - Apply **rate limiting** (per client IP; e.g. an in-process token bucket / simple counter, or document a chosen minimal approach). Keep it dependency-light — check `requirements.txt` before adding anything.
     - Reuse `provision_mailbox(..., send_verify=True)`; return the same shape as `/provision` (created/exists, verification_status, email).
   - For `mail_mode=custom`, still create the `mail_domains` pending row as `provision_mailbox` already does, and return a hint that the caller should continue to the domain DNS wizard (`/domain.html?domain=...`).
3. In `nginx/sites-available/mail`, route the public form to provision-api instead of the cross-repo register-api:
   - Point `location = /api/register` to `http://127.0.0.1:8092/register;` (mail-provision-api), OR add `location = /api/mail/register` and update the front-end. Prefer keeping the existing `/api/register` path to minimize the front-end diff, but ensure it now targets :8092.
   - Keep `Host`/`X-Forwarded-*` headers so the API sees the real client IP for rate limiting (`X-Real-IP` / `X-Forwarded-For`).
4. Update `host-www/mail-auth/register.html` only as needed (endpoint path if changed; keep the `custom` → `/domain.html?domain=...` redirect and `km0` → `/login.html?registered=1`).
5. Confirm `docker-compose.yml` exposes provision-api on `127.0.0.1:8092` (it does) and that no new secret is required for the public route.
6. Do NOT remove the token-gated `/provision`, `/activate`, `/link` routes — km0-opencloud and ops still use them. This FEAT only ADDS a public path.
7. Follow `docs/issue-mail-registration-preplan.md` and `docs/opencloud-registration-integration.md`. Minimal diff; no secrets committed.

## Acceptance criteria
- [ ] `POST https://mail.km0digital.com/api/register` with a valid `@km0digital.com` body creates a mailbox and returns 200/201 WITHOUT any call to `127.0.0.1:8091`.
- [ ] Freemail mailbox (`foo@gmail.com`) is rejected with `freemail_blocked`.
- [ ] Missing/short password and malformed local part are rejected with clear errors.
- [ ] Rate limiting: rapid repeated requests from one IP are throttled (documented threshold) and return 429.
- [ ] After register (km0), the new user can log in with the native password form (FEAT native-login) and a verification email is queued/sent.
- [ ] `custom` mode creates a pending `mail_domains` row and the front-end continues to `/domain.html?domain=...`.
- [ ] Token-gated `/provision`, `/activate`, `/link` are unchanged and still require Bearer.
- [ ] `./scripts/verify-mail-stack.sh` passes; `sudo nginx -t` OK; no secrets committed.

## Implementation notes (coder)
- `docker/mail-provision-api/app.py`: added a **public** `POST /register` route (no Bearer).
  - Reuses `provision_mailbox(..., opencloud_uuid=None, send_verify=True)` — public signups
    are never IDM-linked, so any `opencloud_uuid` in the body is ignored.
  - Validates `mail_mode in (km0,custom)`, email format (`EMAIL_RE`), `validate_local_part`,
    and `password` length >= 8. Freemail / domain rules come back from `validate_mailbox_email`
    inside `provision_mailbox` (`freemail_blocked`, `invalid_domain`).
  - **Rate limiting:** in-process per-IP sliding window (`rate_limited()` / `client_ip()`),
    `REGISTER_RATE_MAX=10` per `REGISTER_RATE_WINDOW_SEC=300` (env-overridable). Dependency-light —
    no new packages (only stdlib `threading`, `time`); `requirements.txt` unchanged. Client IP read
    from `X-Forwarded-For`/`X-Real-IP` (set by nginx). Returns `429 {"error":"rate_limited"}`.
  - `custom` mode returns `domain` + `continue_to=/domain.html?domain=<domain>` and (via
    `provision_mailbox`) creates the pending `mail_domains` row.
  - Token-gated `/provision`, `/activate`, `/link`, `/update-password`, `/lookup/*` are UNCHANGED.
- `nginx/sites-available/mail`: `location = /api/register` now `proxy_pass`es to
  `http://127.0.0.1:8092/register` (was `:8091/register`, km0-opencloud register-api).
  `X-Real-IP`/`X-Forwarded-For` kept for the API rate limit. Header comment updated.
- `host-www/mail-auth/register.html`: unchanged — it already POSTs `/api/register` with
  `{email, desired_email, password, mail_mode, contact_email}` and redirects `custom` →
  `/domain.html?domain=...`, `km0` → `/login.html?registered=1`.
- Deploy: `docker compose build mail-provision-api && docker compose up -d mail-provision-api`;
  `cp nginx/sites-available/mail /etc/nginx/sites-available/mail && nginx -t && systemctl reload nginx`.

## Testing instructions
Run from repo root on the VPS. Real output captured 2026-08-01 23:2x UTC after deploy + reload.

1. Public register (km0), disposable local part — created, pending, no IDM link:
   ```bash
   L="reg-$(date +%s)"
   curl -s -X POST https://mail.km0digital.com/api/register -H 'Content-Type: application/json' \
     -d "{\"email\":\"$L@km0digital.com\",\"mail_mode\":\"km0\",\"password\":\"correcthorse9!\"}"
   curl -s https://mail.km0digital.com/api/mail/account/$L@km0digital.com/status
   ```
   Observed:
   ```
   {"email":"reg-1785626562@km0digital.com","mail_mode":"km0","ok":true,"status":"created","verification_status":"pending"}
   {"active":true,"contact_email":null,"email":"reg-1785626562@km0digital.com","mail_mode":"km0","opencloud_uuid":null,"verification_status":"pending"}
   ```
2. Confirm mail-provision-api (:8092) served it — proves not the cross-repo register-api (:8091):
   ```bash
   docker compose logs --tail=40 mail-provision-api | grep -iE 'POST /register'
   ```
   Observed: `... "POST /register HTTP/1.1" 201 -` (and 400s for the invalid-input probes below).
3. Verification email landed in the NEW inbox (send_verify path):
   ```bash
   docker compose exec -T dovecot doveadm search -u "reg-1785626562@km0digital.com" all
   ```
   Observed: one message id returned; no SMTP warning in provision-api logs (send OK).
4. Invalid input rejected:
   ```bash
   curl -s -X POST https://mail.km0digital.com/api/register -H 'Content-Type: application/json' \
     -d '{"email":"foo@gmail.com","mail_mode":"km0","password":"correcthorse9!"}'   # freemail
   curl -s -X POST https://mail.km0digital.com/api/register -H 'Content-Type: application/json' \
     -d '{"email":"shorty@km0digital.com","mail_mode":"km0","password":"abc"}'      # short pw
   curl -s -o /dev/null -w '%{http_code}\n' -X POST https://mail.km0digital.com/api/register \
     -H 'Content-Type: application/json' -d '{}'                                     # empty body
   ```
   Observed: `{"error":"freemail_blocked"}`, `{"error":"password_too_short"}` (HTTP 400), empty body `400`.
5. Rate limit (per-IP sliding window, MAX=10/300s) — expect 429 after threshold:
   ```bash
   for i in $(seq 1 20); do curl -s -o /dev/null -w '%{http_code} ' -X POST \
     https://mail.km0digital.com/api/register -H 'Content-Type: application/json' \
     -d '{"email":"rl@km0digital.com","mail_mode":"km0","password":"correcthorse9!"}'; done; echo
   ```
   Observed: `201 200 200 200 429 429 429 429 429 429 429 429 429 429 429 429 429 429 429 429`
   (first hits create/exist, then 429 once the window is full; prior probes counted toward the 10).
6. `custom` mode → pending domain row + wizard continuation:
   ```bash
   CD="cust-$(date +%s).example"
   curl -s -X POST https://mail.km0digital.com/api/register -H 'Content-Type: application/json' \
     -d "{\"email\":\"admin@$CD\",\"mail_mode\":\"custom\",\"password\":\"correcthorse9!\"}"
   docker compose exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c \
     "SELECT name, active, verification_status FROM mail_domains WHERE name='$CD';"
   ```
   Observed: `{"continue_to":"/domain.html?domain=cust-....example","domain":"cust-....example","email":"admin@cust-....example","mail_mode":"custom","ok":true,"status":"created","verification_status":"pending"}`
   and the `mail_domains` row `active=f, verification_status=pending`.
7. Token-gated routes unchanged (Bearer still required):
   ```bash
   curl -s -o /dev/null -w '%{http_code}\n' -X POST https://mail.km0digital.com/api/mail/provision \
     -H 'Content-Type: application/json' -d '{"email":"x@km0digital.com","mail_mode":"km0","password":"correcthorse9!"}'
   ```
   Observed: `401`.
8. Native password login with the freshly registered mailbox (FEAT native-login path):
   open `https://mail.km0digital.com/`, use the primary CTA (`/index.php?_task=login`) with the
   registered address + password. Operator smoke — account exists/active per step 1 status.
9. Stack health:
   ```bash
   ./scripts/verify-mail-stack.sh   # -> "All critical checks passed." (exit 0)
   nginx -t                          # syntax ok
   ```
   Observed: all critical checks passed (only the pre-existing WARN "mail login.html not
   redirecting to auth hub"); `nginx -t` successful.

## Test report (tester)

- **Date/time (UTC):** 2026-08-01 23:53–23:54 UTC (provision-api log window 23:53–23:54 UTC).
- **Environment:** live VPS stack, `docker compose` project `km0-mail`; `mail-provision-api` on `127.0.0.1:8092`; branch `main` (synced); target `https://mail.km0digital.com/api/register`.
- **What was tested:** the FEAT's Testing instructions — public km0 register, provision-api served it (not the cross-repo :8091), verification email delivery, invalid-input rejection, per-IP rate limiting, custom-mode pending row, token-gated route untouched, stack health.

### Results
- **Public km0 register creates mailbox, no :8091 — PASS.** `POST /api/register` (`reg-1785628405@km0digital.com`) → `{"ok":true,"status":"created","verification_status":"pending"}`; status route shows `active:true, mail_mode:km0, opencloud_uuid:null`. `mail-provision-api` (:8092) logged `POST /register HTTP/1.1 201` — proves the mail host served it, not the km0-opencloud register-api (:8091).
- **Freemail rejected — PASS.** `foo@gmail.com` → `{"error":"freemail_blocked"}`.
- **Short password / empty body rejected — PASS.** `abc` → `{"error":"password_too_short"}` (400); empty body `{}` → `400`.
- **Rate limiting (per-IP) — PASS.** 20 rapid requests → `200×6` then `429×14` (window `MAX=10/300s`; earlier probes counted toward the window). A follow-up custom request over HTTPS was also `{"error":"rate_limited"}`, confirming the throttle holds.
- **Verification email delivered to new inbox — PASS.** `doveadm search -u reg-1785628405@km0digital.com all` → one message id returned.
- **Custom mode pending domain row + wizard continuation — PASS.** (tested direct on :8092 to use a separate rate-limit bucket): `{"ok":true,"continue_to":"/domain.html?domain=cust-….example","mail_mode":"custom","verification_status":"pending"}`; `mail_domains` row `active=f, verification_status=pending`; `mail_accounts admin@cust-….example active=t, mail_mode=custom, opencloud_uuid=NULL`.
- **Token-gated /provision unchanged — PASS.** `POST /api/mail/provision` without Bearer → `401`.
- **Stack health — PASS.** `verify-mail-stack.sh` → "All critical checks passed." (exit 0); `nginx -t` successful.
- **Native password login with the registered mailbox — operator smoke** (account created/active/pending per status above; native form served per FEAT native-login).

- **Overall: PASS.**
- **URLs tested:** `https://mail.km0digital.com/api/register`, `/api/mail/account/<email>/status`, `/api/mail/provision`, `http://127.0.0.1:8092/register`.
- **Log excerpt (mail-provision-api, UTC):** `... "POST /register HTTP/1.1" 201 -` (public register served by :8092) and `... "POST /register HTTP/1.1" 429 -` (rate limit enforced).
