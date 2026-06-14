---
## Closing summary (TOP)

- **What happened:** Phase 1 self-hosted mail stack for KM0 Digital (#2) was implemented and verified after fixing Postfix/Dovecot delivery blockers.
- **What was done:** Added Postfix PostgreSQL hash maps, LMTP routing to Dovecot, Dovecot SQL userdb fixes, maildir provisioning in `km0-mail-admin`, and updated runbook/CHANGELOG.
- **What was tested:** Tester PASS — `verify-mail-stack.sh`, RCPT/LMTP delivery, alias routing, localhost 587 relay, Roundcube HTTP 200, and backup script; DNS MX/PTR and Nginx TLS remain operator follow-ups.
- **Why closed:** All critical delivery criteria passed; remaining WARN items are documented operator prerequisites, not code regressions.
- **Closed at (UTC):** 2026-06-14 12:36
---

# Feat 0: Self-hosted mail stack for KM0 Digital

## GitHub Issue
- **Issue:** https://github.com/AMVARA-CONSULTING/km0-mail/issues/2
- **Number:** #2
- **Labels:** none
- **Created:** 2026-06-14T12:02:13Z
- **Redmine:** #7605 (tracking ticket when configured in autoagents/.env)

## Problem / goal
# plan: Self-hosted mail stack for KM0 Digital  > **Purpose:** GitHub issue draft for implementing production mail on the existing KM0 VPS.   > **Target:** `mail.km0digital.com` on Debian 13 (same host as OpenCloud), Nginx for webmail TLS only.   >...

## High-level instructions for coder
- Read the full issue at https://github.com/AMVARA-CONSULTING/km0-mail/issues/2
- Follow **`docs/issue-mail-preplan.md`** for architecture, DNS, ports, and phases
- Implement under `docker-compose.yml`, `config/`, `nginx/`, `scripts/`, `sql/`, `docs/`
- Phase 1 focus: Postfix + Dovecot + Rspamd + Roundcube + PostgreSQL on same VPS as OpenCloud
- User addresses: `@km0digital.com`; service hostname: `mail.km0digital.com`
- No OpenCloud LDAP unification in phase 1; include `mail_accounts.opencloud_uuid` nullable in SQL
- Light SMTP relay from localhost for OpenCloud / marketing / register-api / km0-web (see pre-plan)
- Add **Testing instructions** before renaming to UNTESTED-

## References
- Pre-plan: docs/issue-mail-preplan.md
- Repo: https://github.com/AMVARA-CONSULTING/km0-mail
- Runbook: docs/runbook.md (create/update during implementation)

## Implementation summary

Phase 1 stack was already in repo; this pass fixed **mail delivery blockers** found by the tester:

| Fix | Files |
|-----|-------|
| Postfix hash maps from PostgreSQL (451 RCPT tempfail) | `docker/postfix/build-hash-maps.sh`, `docker/postfix/entrypoint.sh`, `docker/postfix/Dockerfile` |
| Postfix LMTP to Dovecot (queue stuck, DNS/chroot) | `config/postfix/master.cf`, `docker/postfix/entrypoint.sh` |
| Dovecot SQL userdb/LMTP (451 internal error) | `docker/dovecot/entrypoint.sh`, `config/dovecot/dovecot-sql.conf.ext.template` |
| Maildir provisioning + map reload | `scripts/km0-mail-admin` |
| Docs | `docs/CHANGELOG.md`, `docs/runbook.md` |

Verified locally: RCPT 250, mail queued and delivered to Maildir, `./scripts/verify-mail-stack.sh` passes.

## Testing instructions

### Prerequisites (operator)

1. Copy secrets: `cp .env.example .env && chmod 600 .env` (set strong passwords)
2. Deploy stack: `docker compose build && docker compose up -d`
3. Create operational mailboxes:
   ```bash
   ./scripts/km0-mail-admin create-mailbox postmaster@km0digital.com
   ./scripts/km0-mail-admin create-mailbox noreply@km0digital.com
   ```
4. Configure DNS at Joker.com (MX, A, SPF, DKIM via `./scripts/setup-dkim.sh`, DMARC, PTR) — see `docs/runbook.md`
5. UFW: allow 25, 587, 993/tcp
6. Deploy Nginx vhost + certbot for `mail.km0digital.com`

### Automated smoke test

```bash
cd /opt/km0-mail
./scripts/verify-mail-stack.sh
```

Expected: all Docker services running; ports 25/587/993/8080 listening; PostgreSQL schema present.

### Container checks

```bash
docker compose ps
docker compose logs --tail=50 postfix dovecot rspamd roundcube
```

### Postfix recipient + delivery (critical)

```bash
# Map lookup
docker compose exec postfix postmap -q postmaster@km0digital.com hash:/etc/postfix/virtual-mailbox-maps
# Expected: km0digital.com/postmaster/

# SMTP accept + LMTP delivery (port 25, from mynetworks)
(echo "EHLO test"; echo "MAIL FROM:<noreply@km0digital.com>"; echo "RCPT TO:<postmaster@km0digital.com>"; echo "DATA"; echo "Subject: delivery test"; echo ""; echo "body"; echo "."; echo "QUIT") | nc -w 10 127.0.0.1 25
docker compose exec postfix mailq   # Expected: empty
docker compose exec dovecot find /var/mail/vhosts/km0digital.com/postmaster/new -type f
```

### DNS (when configured)

```bash
dig +short km0digital.com MX
dig +short mail.km0digital.com A
dig +short -x 116.202.10.106
```

### Webmail

```bash
curl -sI http://127.0.0.1:8080/ | head    # local (before Nginx)
curl -sI https://mail.km0digital.com/ | head  # after Nginx + TLS
```

Login to Roundcube as `postmaster@km0digital.com` with password from `km0-mail-admin`.

### Localhost SMTP relay

```bash
swaks --to postmaster@km0digital.com --from noreply@km0digital.com \
  --server 127.0.0.1 --port 587 --tls --header "Subject: relay test"
```

### Provisioning / aliases

```bash
./scripts/km0-mail-admin create-mailbox user@km0digital.com
./scripts/km0-mail-admin create-alias info@km0digital.com user@km0digital.com
./scripts/km0-mail-admin list-mailboxes
./scripts/km0-mail-admin list-aliases
docker compose exec postfix postmap -q info@km0digital.com hash:/etc/postfix/virtual-alias-maps
```

### Dovecot user lookup

```bash
docker compose exec dovecot doveadm user -f home postmaster@km0digital.com
# Expected: /var/mail/vhosts/km0digital.com/postmaster
```

### Functional (requires DNS + external mail)

| # | Test | Expected |
|---|------|----------|
| 1 | Inbound from Gmail to `postmaster@km0digital.com` | Delivered; visible in Roundcube |
| 2 | Outbound from `noreply@` to external address | Received; SPF/DKIM pass in headers |
| 3 | IMAP 993 + SMTP 587 with mailbox creds | Send/receive OK |
| 4 | OpenCloud notification via `127.0.0.1:587` | From `noreply@km0digital.com` |
| 5 | Alias delivery | `info@` → target mailbox |

### Backup

```bash
BACKUP_ROOT=/var/backups/km0-mail ./scripts/backup-maildir.sh
```

---

## Test report

**Date/time (UTC):** 2026-06-14T12:35:14Z – 2026-06-14T12:35:44Z  
**Log window:** Docker logs from 2026-06-14T12:30:00Z onward (postfix, dovecot, rspamd, roundcube)

### Environment

| Item | Value |
|------|-------|
| Branch | `main` @ `010bc9a` |
| Compose project | `km0-mail` (all 5 services Up) |
| Host | mail.km0digital.com / 116.202.10.106 |
| Stack readiness | `docker compose ps` showed all services running; `./scripts/verify-mail-stack.sh` reported “All critical checks passed”; ports 25/587/993/8080 confirmed listening |

### What was tested

Implementation fixes for Postfix hash maps, LMTP→Dovecot delivery, Dovecot SQL userdb, maildir provisioning, plus smoke/functional checks from Testing instructions.

### Results

| Criterion | Result | Evidence |
|-----------|--------|----------|
| `./scripts/verify-mail-stack.sh` | **PASS** | All Docker services running; ports 25/587/993/8080 OK; PostgreSQL schema present |
| Docker services healthy | **PASS** | `docker compose ps`: postfix, dovecot, rspamd, roundcube, postgres all Up |
| Postfix virtual-mailbox map | **PASS** | `postmap -q postmaster@km0digital.com` → `km0digital.com/postmaster/` |
| Postfix virtual-alias map | **PASS** | `postmap -q info@km0digital.com` → `testuser@km0digital.com` |
| SMTP RCPT + LMTP delivery (port 25) | **PASS** | RCPT 250, DATA 250 queued; `mailq` empty; messages in `postmaster/new/` |
| Dovecot user lookup | **PASS** | `doveadm user -f home postmaster@km0digital.com` → `/var/mail/vhosts/km0digital.com/postmaster` |
| Alias delivery (`info@` → `testuser@`) | **PASS** | RCPT 250, queued; message in `testuser/new/` |
| Localhost SMTP relay (587 STARTTLS) | **PASS** | Python smtplib STARTTLS send succeeded |
| Roundcube local (127.0.0.1:8080) | **PASS** | `curl -sI` → HTTP/1.1 200 OK |
| External mail ports (25/587/993) | **PASS** | `nc -vz mail.km0digital.com` all succeeded |
| Maildir backup script | **PASS** | `BACKUP_ROOT=/tmp/km0-mail-backup-test ./scripts/backup-maildir.sh` completed (pg dump + maildir + rspamd archives) |
| DNS A record | **PASS** | `dig +short mail.km0digital.com A` → `116.202.10.106` |
| DNS MX record | **WARN** | MX not configured yet (expected per operator prerequisites) |
| PTR / reverse DNS | **WARN** | `116.202.10.106` → `static.106.10.202.116.clients.your-server.de.` (not `mail.km0digital.com`) |
| HTTPS webmail (Nginx + TLS) | **WARN** | `curl https://mail.km0digital.com/` SSL error — Nginx vhost not deployed yet |
| Roundcube interactive login | **N/A** | Not exercised in this automated run; local HTTP 200 confirms service up |
| Inbound/outbound external mail (Gmail) | **N/A** | Requires DNS MX/SPF/DKIM/DMARC + PTR (operator step) |
| Rspamd spam rejection | **PASS** | Bare `EHLO test` correctly rejected (554 5.7.1, score 19.90/15.00 — SURBL on EHLO); well-formed local mail accepted (score −0.10) |

### Overall: **PASS**

All **critical** delivery blockers fixed in this task are verified: hash map lookups succeed, RCPT accepts, LMTP delivers to Maildir, queue drains, aliases resolve, and localhost 587 relay works. DNS MX, PTR, DKIM, and Nginx/TLS remain operator follow-ups documented in the runbook — not regressions from this code pass.

### URLs tested

- http://127.0.0.1:8080/ — **PASS** (200)
- https://mail.km0digital.com/ — **WARN** (TLS not configured on host)
- mail.km0digital.com:25, :587, :993 — **PASS** (TCP connect)

### Relevant log excerpts

Rspamd accepted well-formed local delivery (prior run, same stack):

```
rspamd_task_write_log: ... (default: F (no action): [-0.10/15.00] ...), rcpts: <postmaster@km0digital.com>
```

Rspamd rejected malformed test (EHLO `test`, missing headers — expected):

```
rspamd_task_write_log: ... (default: T (reject): [19.90/15.00] [MW_SURBL_MULTI(7.50){test:helo;}, ...])
554 5.7.1 Spam message rejected
```

Successful SMTP session (tester run, RFC-compliant headers):

```
250 2.1.5 Ok
354 End data with <CR><LF>.<CR><LF>
250 2.0.0 Ok: queued as 5010226E876
```

Maildir evidence:

```
/var/mail/vhosts/km0digital.com/postmaster/new/1781440527.M501771P48.dovecot,...
/var/mail/vhosts/km0digital.com/testuser/new/1781440535.M222467P48.dovecot,...
```

