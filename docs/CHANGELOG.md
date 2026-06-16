# Changelog

## [Unreleased]

### Added

- Roundcube KM0 login branding: custom `km0` skin (extends Elastic) with logo, favicon, and styled login page; mounted via Docker Compose; inbox UI unchanged
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
