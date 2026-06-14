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

- `docker-compose.yml` — modular stack (custom Postfix/Dovecot images, Rspamd, Roundcube, PostgreSQL)
- `sql/init/` — `mail_accounts`, `mail_aliases`, `mail_domains` (+ nullable `opencloud_uuid`)
- `config/` — Postfix virtual SQL maps, Dovecot SQL auth, Rspamd milter/DKIM, Roundcube overrides
- `nginx/sites-available/mail` — HTTPS webmail reverse proxy template
- `scripts/km0-mail-admin` — mailbox/alias provisioning CLI
- `scripts/backup-maildir.sh`, `scripts/verify-mail-stack.sh`, `scripts/setup-dkim.sh`
- `docs/runbook.md`, `docs/CHANGELOG.md`
- `config/fail2ban/jail.d/km0-mail.local` — host jail template

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
  --server 127.0.0.1 --port 587 --header "Subject: relay test"
```

### Provisioning / aliases

```bash
./scripts/km0-mail-admin create-mailbox user@km0digital.com
./scripts/km0-mail-admin create-alias info@km0digital.com user@km0digital.com
./scripts/km0-mail-admin list-mailboxes
./scripts/km0-mail-admin list-aliases
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

**Date/time (UTC):** 2026-06-14T12:13:00Z – 2026-06-14T12:16:00Z  
**Log window:** container logs from stack start (~12:11 UTC) through test end  
**Branch / commit:** `main` @ `fb7e489`  
**Environment:** VPS `/opt/km0-mail`, `docker compose` project `km0-mail`, 5 services up ~1 min before testing

**Stack readiness:** `./scripts/verify-mail-stack.sh` exited 0 (“All critical checks passed”); all five compose services `Up`; ports 25/587/993/8080 listening; `nc -vz mail.km0digital.com {25,587,993}` succeeded immediately (no polling needed).

### Results

| Criterion | Result | Evidence |
|-----------|--------|----------|
| Docker services (postgres, postfix, dovecot, rspamd, roundcube) | **PASS** | `docker compose ps` — all `Up`; verify script `[OK]` for each |
| Local ports 25, 587, 993, 8080 | **PASS** | `ss` + verify script; external `nc -vz` to 116.202.10.106 |
| PostgreSQL schema (`mail_accounts`, `mail_aliases`, `mail_domains`) | **PASS** | verify script: `mail schema tables present` |
| `./scripts/verify-mail-stack.sh` | **PASS** | exit 0; critical checks passed |
| `./scripts/km0-mail-admin` provisioning | **PASS** | Created `testuser@`, alias `info@→testuser@`; list commands returned expected rows |
| `./scripts/backup-maildir.sh` | **PASS** | `BACKUP_ROOT=/tmp/km0-mail-backup-test` → sql.gz, maildir tar, rspamd tar created |
| Roundcube local HTTP (`127.0.0.1:8080`) | **PASS** | `HTTP/1.1 200 OK`; login page renders (“KM0 Mail Login”) |
| Postfix SQL maps (manual `postmap -q`) | **PASS** | Inside container: `postmaster@` → `km0digital.com/postmaster/`; alias `info@` → `testuser@` |
| SMTP RCPT / local mail delivery | **FAIL** | `RCPT TO:<postmaster@km0digital.com>` → `451 4.3.0 Temporary lookup failure`; Python SMTP on :25/:587 same; sendmail message stuck in queue (`6C51526E86E` in maildrop) |
| Localhost SMTP relay (587 STARTTLS) | **FAIL** | Python `smtplib` + STARTTLS: “Connection unexpectedly closed” |
| Alias delivery (port 25) | **FAIL** | `RCPT TO:<info@km0digital.com>` → `451 4.3.0 Temporary lookup failure` |
| DNS MX `km0digital.com` | **WARN** | No MX record (operator prerequisite per runbook) |
| DNS A `mail.km0digital.com` | **PASS** | `116.202.10.106` |
| DNS PTR 116.202.10.106 | **WARN** | Generic Hetzner PTR (`static.106.10.202.116.clients.your-server.de.`) — not mail-specific |
| HTTPS webmail `https://mail.km0digital.com/` | **FAIL** | `curl` SSL error (exit 60); verify script warns — Nginx vhost + cert not deployed |
| Inbound/outbound external mail (Gmail, SPF/DKIM) | **N/A** | Requires MX + TLS webmail; not configured |
| Roundcube interactive login | **N/A** | UI reachable; credentials not exercised (delivery broken) |
| Rspamd spam sample | **N/A** | No mail accepted through Postfix for filtering |

**Overall: FAIL** — stack starts and admin tooling works, but **Postfix rejects all local recipients with 451 lookup failure** despite working `postmap -q` lookups; mail cannot be delivered or relayed.

**URLs tested:** `http://127.0.0.1:8080/` (PASS), `https://mail.km0digital.com/` (FAIL — TLS/nginx not deployed)

### Log excerpts

```
# verify-mail-stack.sh
[OK]   postgres/postfix/dovecot/rspamd/roundcube running
[OK]   port 25/587/993 listening
[OK]   mail schema tables present
[WARN] MX not found for km0digital.com
[WARN] https://mail.km0digital.com/ not reachable

# roundcube-1
[Sun Jun 14 12:11:26.079619 2026] Apache/2.4.62 ... resuming normal operations
172.22.0.1 - - [14/Jun/2026:12:12:16 +0000] "HEAD / HTTP/1.1" 200 509

# SMTP session (host → 127.0.0.1:25)
S: 250 2.1.0 Ok
C: RCPT TO:<postmaster@km0digital.com>
S: 451 4.3.0 <postmaster@km0digital.com>: Temporary lookup failure

# postfix queue
6C51526E86E  root → postmaster@km0digital.com  (stuck in maildrop after sendmail)
```

**Follow-up for coder:** Investigate Postfix smtpd recipient validation vs `postmap -q` (chroot/proxymap/rspamd milter interaction); confirm LMTP delivery to Dovecot :24 once RCPT succeeds. Operator items (MX, Nginx/certbot, PTR) remain per runbook.

