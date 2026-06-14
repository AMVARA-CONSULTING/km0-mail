# Changelog

## [Unreleased]

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
- Fail2ban jail template: `config/fail2ban/jail.d/km0-mail.local`
- Secrets template: `.env.example`
