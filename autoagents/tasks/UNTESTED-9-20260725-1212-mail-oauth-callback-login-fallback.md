# FEAT-Task: BUG: Mail OAuth callback returns login page — IMAP auth fails without Dovecot oauth2

## GitHub Issue
- **Number:** #9
- **URL:** https://github.com/AMVARA-CONSULTING/km0-mail/issues/9
- **Labels:** bug
- **Redmine tracking:** #7605 (when configured)
- **Priority:** production-urgent

## Problem / goal
Hub mail SSO (`auth.km0digital.com/login?service=mail` → Roundcube `/index.php/login/oauth` → Dex `km0-mail-web`) returns HTTP 200 login HTML on the OAuth callback instead of opening the mailbox. Dovecot logs: `DOVECOT_OAUTH_CLIENT_SECRET set but oauth2 driver missing — password login only`. Roundcube cannot complete IMAP via XOAUTH2; users bounce to the password form (also hit by i18n #8).

## High-level instructions for coder
1. Run `./scripts/git-sync-main.sh` before edits.
2. Confirm failure path: OAuth callback 200 + Dovecot oauth2 driver absence; inspect Roundcube OAuth + `km0_sso_provision` plugin + Dovecot entrypoint oauth guard.
3. Implement the **minimal** fix that lets a mailbox user finish SSO into webmail after Dex OIDC, without breaking SQL password login:
   - Prefer enabling a real Dovecot oauth2 passdb if an installable module fits the image strategy; **or**
   - An interim bridge that does not require `libdriver_oauth2.so` if documented and safe; **or**
   - If blocked: explicit OAuth error UX + reliable password path (coordinate with #8 asset fix).
4. Do not commit secrets (`.env`, client secrets). Document operator steps in runbook.
5. Append Testing instructions; FEAT → WIP → UNTESTED. Comment/label on GitHub (#9).

## Acceptance criteria
- [x] After Dex OIDC for `km0-mail-web`, user reaches mailbox **or** clear recoverable error (no silent login-form loop) — Dovecot now advertises XOAUTH2 + Dex introspection (browser SSO still needs operator smoke)
- [x] Password IMAP login still works for non-OAuth users
- [x] Dovecot does not enter "Auth process broken" state
- [x] Runbook + CHANGELOG updated; no secrets committed

## What was done
- Upgraded `docker/dovecot` to **Dovecot CE 2.4.4** from `repo.dovecot.org` (built-in oauth2; Debian Bookworm 2.3 has none).
- Migrated `config/dovecot/dovecot.conf` to 2.4 syntax; entrypoint renders `/run/dovecot/auth-local.conf` (SQL plain/login + optional oauth2/XOAUTH2).
- Removed obsolete 2.3 SQL `.ext` template; oauth2 template updated for CE 2.4 `oauth2 { }` block.
- Live rebuild: logs show `OAuth2/XOAUTH2 enabled`; IMAP CAPABILITY includes `AUTH=XOAUTH2`; `doveadm auth test` succeeds for PLAIN; `./scripts/verify-mail-stack.sh` passes.

## Testing instructions

1. Confirm Dovecot is CE 2.4 with OAuth enabled:
   ```bash
   cd /opt/km0-mail
   docker compose logs --tail=5 dovecot   # "OAuth2/XOAUTH2 enabled (Dex LDAP SSO)"
   docker compose exec dovecot dovecot --version   # 2.4.x
   ```
2. IMAP advertises XOAUTH2 (not password-only):
   ```bash
   python3 - <<'PY'
   import ssl,socket
   ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
   s=ctx.wrap_socket(socket.create_connection(('127.0.0.1',993)),server_hostname='mail.km0digital.com')
   print(s.recv(1024).decode())
   s.close()
   PY
   # Expect: AUTH=PLAIN AUTH=LOGIN AUTH=XOAUTH2 AUTH=OAUTHBEARER
   ```
3. Password login still works (SQL passdb):
   ```bash
   docker compose exec dovecot doveadm auth test postmaster@km0digital.com '<real-password>'
   # Or set a disposable password via mail-provision-api /update-password on a test mailbox, then doveadm auth test, then rotate.
   ```
4. No auth-process breakage:
   ```bash
   ./scripts/verify-mail-stack.sh
   docker compose logs --tail=50 dovecot | grep -iE 'broken|Fatal|Error' || true
   ```
5. **Browser SSO (required for full #9 sign-off):** From hub `https://auth.km0digital.com/login?service=mail` → LDAP/OpenCloud connector → Roundcube OAuth callback should open the inbox for a user whose Dex `email` claim matches an existing `@km0digital.com` mailbox (not freemail). Must not land on the password form with HTTP 200 alone.
6. Regression: Roundcube password form login still works for a non-OAuth mailbox.
