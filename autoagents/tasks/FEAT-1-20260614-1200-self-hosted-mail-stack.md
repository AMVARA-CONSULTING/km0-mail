# Self-hosted mail stack (Postfix + Dovecot + Rspamd + Roundcube)

## GitHub Issue
- **Issue:** https://github.com/AMVARA-CONSULTING/km0-mail/issues/1
- **Number:** #1
- **Labels:** agent:planned
- **Created:** 2026-06-14
- **Redmine tracking:** #7605

## Problem / goal

Implement production self-hosted mail for KM0 Digital on the existing VPS: send, receive, webmail, anti-spam, and light SMTP integration for OpenCloud and km0-web — without OpenCloud LDAP unification in phase 1.

Full architecture, DNS, ports, phases, and acceptance criteria are in **`docs/issue-mail-preplan.md`**.

## High-level instructions for coder

### Phase 1 — Core stack (this task scope)

- [ ] Create `docker-compose.yml` with modular services: **Postfix**, **Dovecot**, **Rspamd**, **Roundcube**, **PostgreSQL**
- [ ] PostgreSQL schema: `mail_accounts` (+ `opencloud_uuid` nullable), `mail_aliases`, Roundcube tables
- [ ] Maildir volume; expose ports **25**, **587**, **993** on host (UFW documented)
- [ ] Nginx template `nginx/sites-available/mail` → Roundcube at `https://mail.km0digital.com`
- [ ] Scripts: `km0-mail-admin` (create mailbox/alias), `verify-mail-stack.sh`, `backup-maildir.sh`
- [ ] Operational mailboxes: `postmaster@km0digital.com`, `noreply@km0digital.com`
- [ ] Localhost SMTP relay (`mynetworks`) for internal apps
- [ ] `docs/runbook.md` with operator steps (DNS at Joker.com, PTR, certbot, UFW)
- [ ] Document OpenCloud `NOTIFICATIONS_SMTP_*` → `127.0.0.1:587` (operator applies on opencloud side)

### Explicit non-goals (phase 1)

- OpenCloud LDAP / shared passwords
- ClamAV
- POP3
- Customer self-service mail activation UI

### Key decisions (already agreed)

| Item | Value |
|------|--------|
| Server | Same VPS as OpenCloud |
| User addresses | `@km0digital.com` |
| Service hostname | `mail.km0digital.com` |
| DB | PostgreSQL |
| Antivirus | Rspamd only |
| Scale target | 1000+ mailboxes by end of year |

## Acceptance criteria

- [ ] Compose stack starts; all services healthy
- [ ] PostgreSQL schema applied; provisioning script creates a test mailbox
- [ ] Inbound SMTP (port 25) and submission (587) configured in Postfix
- [ ] Dovecot IMAPS (993) serves Maildir for virtual users
- [ ] Rspamd milter integrated with Postfix
- [ ] Roundcube reachable via Nginx HTTPS template (loopback upstream)
- [ ] `scripts/verify-mail-stack.sh` documents smoke checks
- [ ] `docs/runbook.md` covers deploy, backup, and DNS checklist
- [ ] No secrets in Git; `.env.example` documents required vars
- [ ] Pre-plan updated only if decisions changed during implementation

## References

- `docs/issue-mail-preplan.md`
- OpenCloud SMTP env: `/opt/opencloud/opencloud-compose/.env` (`NOTIFICATIONS_SMTP_*`)

## Testing instructions

_(Append concrete commands when implementation is complete — tester agent fills verification.)_

```bash
# Placeholder — replace with real checks after deploy
cd /opt/km0-mail
docker compose ps
docker compose logs --tail=50 postfix dovecot rspamd roundcube postgres
./scripts/verify-mail-stack.sh
```
