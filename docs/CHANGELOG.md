# Changelog

## [Unreleased]

### Changed

- Autoagents Redmine time tracking: refresh `YYYYMMDD-HHMM` stamp on FEAT/NEW → WIP so duration starts when work begins (not when the task was queued); `redmine_sync.py` parses WIP stamps and Markdown `**Closed at (UTC):**` lines

### Fixed

- Autoagents Redmine time entries: skip logging when `Closed at (UTC)` is missing instead of falling back to `datetime.now()` (avoids inflated hours)

### Added

- SPIKE #12 closed as **wontfix**: Google IdP will not map directly into Roundcube (`docs/spike-google-idp-roundcube-mailbox-map.md`); keep Dex LDAP OAuth + password; Roundcube discards `oauth_login` username rewrite and Dovecot `username_attribute=email` requires token email = mailbox
- Post-activate verify happy path (issue #15): Roundcube login `?activated=1` banner; `entry` next_steps (password → verify → optional LDAP); wizard/hub copy stresses mailbox password + inbox verify (no Google IdP for mail); runbook checklist
- Hub SSO cookie + Google-safe continue (issue #14, supersedes #11): Auth Hub `sso=all` on cloud bridge for unified/`service=mail`; `/sso-continue` chooser (LDAP OAuth / activate-mail.html / password) — no auto `prompt=none`; login `service=mail` activate CTA (cross-repo `/opt/km0-auth/host-www/`)
- Activate Mail API (issue #10): `POST /activate` (local_part + opencloud_uuid + contact_email + password → `foo@km0digital.com`), `POST /link`, lookup `activate_required` soft-fail; freemail never a mailbox; docs clarify Google = Cloud IdP, Roundcube = password + Dex LDAP OAuth
- One mailbox per OpenCloud user (issue #13): unique partial index on `mail_accounts.opencloud_uuid`, index on `contact_email`; `mail-provision-api` returns existing or `409 uuid_already_linked` on duplicate uuid; `GET /lookup/by-uuid/` and `/lookup/by-contact/` helpers
- Docs: agent pipeline order for mail SSO / activate (`docs/agent-pipeline-mail-activate.md`) so FEATs #10–#15 and opencloud #23–#26 do not race (issue #16)
- Agent 001 dedupe (issue #16 follow-up): `issue_checker_agent.py` skips when `WIP|UNTESTED|TESTING|CLOSED-<N>-*` exists or issue has `agent:wip|untested|testing` (stops recreating FEATs after rename)

### Fixed

- Dovecot OAuth/XOAUTH2 for Roundcube Dex LDAP SSO (issue #9): image upgraded to Dovecot CE 2.4 with built-in oauth2; IMAP advertises `AUTH=XOAUTH2` when `DOVECOT_OAUTH_CLIENT_SECRET` is set (ends silent OAuth→login-form loop caused by missing driver on Bookworm 2.3)
- Roundcube KM0 login: `i18n.js` script uses skin-relative `/js/i18n.js` so Roundcube no longer doubles the path to `skins/km0/skins/km0/js/i18n.js` (issue #8)

### Changed

- Dovecot: CE 2.4 config (`mail_driver`/`mail_path`, inline SQL passdb/userdb, `auth-local.conf` rendered at start)

### Changed

- Mail auth + Roundcube login: civic dark KM0 tokens (Paper/Snow/Mist/Ink/Signal), IBM Plex / Bricolage, and canonical K0 favicon/logo (replacing Inter + purple gradient)
- Nginx: `/`, `/login.html`, and `/register` redirect to Auth Hub (`auth.km0digital.com`); Roundcube login links point at the hub
- Roundcube OAuth: Dex auth/token URIs and LDAP `connector_id` for OpenCloud SSO
- verify-mail-stack: expect `/login.html` redirect to Auth Hub

### Added

- Branded login landing: mailbox password primary, OpenCloud / LDAP secondary with redirect hint (en/es/ca/de)
- Registration: password confirmation field, client-side validation, and localized API error messages
- Roundcube login skin: links to self-registration and branded landing (`/login.html`)

### Fixed

- Nginx: `/` redirects to `/login.html`; Roundcube task URLs with query args still route to `/index.php`
- Branded auth pages: register submit button alignment; OpenCloud / LDAP wording (replacing generic “KM0 LDAP”)
- Dovecot auth: OAuth2 passdb enabled only when driver and `DOVECOT_OAUTH_CLIENT_SECRET` are present (fixes *Auth process broken* on Debian Bookworm)
- mail-provision-api: STARTTLS on SMTP submission for verification emails
- verify-mail-stack: Dovecot auth worker and Postfix sender-verification checks
- Postfix submission: `smtpd_tls_security_level=may` on port 587 (fixes hung banner with `encrypt`)

### Added

- Public mail registration (issue #6): Model A (`@km0digital.com`) and Model B (custom domain DNS wizard)
- `mail-provision-api` and `domain-verify-api` services; SQL migration `03-registration-schema.sql`
- Branded auth pages at `host-www/mail-auth/` (`/login.html`, `/register`, `/domain.html`, `/verify`)
- Dex LDAP OAuth (no Google): Roundcube OAuth2, Dovecot XOAUTH2, `km0_sso_provision` plugin
- Pre-verification outbound hold via Postfix sender policy; Roundcube `km0_verification_banner` plugin
- Same-origin nginx proxy for `/api/register` and mail APIs; docs in `opencloud-registration-integration.md`

### Added (prior)

- Roundcube KM0 login branding: custom `km0` skin (extends Elastic) with logo, favicon, and styled login page
- KM0 login page language switch (CA/ES/EN/DE) with client-side i18n (`skins/km0/js/i18n.js`); browser/query/localStorage locale detection

### Fixed

- KM0 login form: hide Elastic `input-group-prepend` icons so username/password fields match OpenCloud-style plain inputs

### Changed

- Roundcube default locale set to `en_US` in `config/roundcube/config.inc.php`
- Runbook: Dovecot image rebuild steps after SSO revert; login skin file list includes `i18n.js`

### Reverted (2026-06-16)

- Rolled back experimental webmail SSO (issue #3): external `/login.html` wrapper, Roundcube OAuth, Dovecot XOAUTH2, `mail-provision-api`, and register proxy. Nginx restored to direct Roundcube proxy. SSO redesign deferred — see `docs/github-issue-mail-sso.md`.

### Changed

- Nginx vhost: polished TLS proxy to Roundcube (`127.0.0.1:8080`) with security headers; no auth-page redirect layer
- Runbook: OpenCloud SMTP example uses `host.docker.internal` (not `127.0.0.1`), current `SMTP_*` env var names, and `extra_hosts: host.docker.internal:host-gateway` for Docker relay to km0-mail on the host

### Deployed (server 2026-06-14)

- Nginx vhost + Let's Encrypt TLS for `https://mail.km0digital.com` (Roundcube via `127.0.0.1:8080`)
- UFW: ports 25, 587, 993 open
- DKIM key generated in Rspamd; DNS checklist: `docs/joker-dns-checklist.md`
- Fail2ban jail `km0-mail.local` installed on host

### Fixed

- Postfix recipient validation: rebuild hash maps from PostgreSQL at startup (`docker/postfix/build-hash-maps.sh`) instead of live `pgsql:` lookups that returned 451 tempfail under smtpd
- Postfix LMTP delivery: IPv4-only transport, chroot DNS (`resolv.conf` in queue dir), LMTP/smtpd chroot disabled
- Dovecot LMTP: SQL config path (`/run/dovecot/dovecot-sql.conf.ext`), absolute `home` in user_query
- Provisioning: create Maildir `cur/new/tmp`, reload Postfix maps after mailbox/alias changes

### Added

- Docker Compose stack: Postfix, Dovecot, Rspamd, Roundcube, PostgreSQL (`docker-compose.yml`)
- PostgreSQL schema: `mail_accounts`, `mail_aliases`, `mail_domains` with nullable `opencloud_uuid`
- Service configs under `config/postfix/`, `config/dovecot/`, `config/rspamd/`, `config/roundcube/`
- Nginx vhost template for `https://mail.km0digital.com` (`nginx/sites-available/mail`)
- Provisioning CLI: `scripts/km0-mail-admin` (mailbox, alias, list, set-password)
- Ops scripts: `scripts/backup-maildir.sh`, `scripts/verify-mail-stack.sh`, `scripts/setup-dkim.sh`
- Operations runbook: `docs/runbook.md`
- DNS operator checklist: `docs/joker-dns-checklist.md`
- Fail2ban jail template: `config/fail2ban/jail.d/km0-mail.local`
- Secrets template: `.env.example`
