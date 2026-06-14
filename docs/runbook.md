# km0-mail operations runbook

> **Stack:** Postfix + Dovecot + Rspamd + Roundcube + PostgreSQL (Docker Compose)  
> **Hostname:** `mail.km0digital.com` · **Addresses:** `@km0digital.com`  
> **Repo:** `/opt/km0-mail`

Architecture reference: [`issue-mail-preplan.md`](issue-mail-preplan.md)

---

## Components

| Service | Container | Host ports | Role |
|---------|-----------|------------|------|
| PostgreSQL | `km0-mail-postgres-1` | internal | Virtual users, aliases, Roundcube DB |
| Postfix | `km0-mail-postfix-1` | 25, 587 | MX, submission, localhost relay |
| Dovecot | `km0-mail-dovecot-1` | 993 | IMAPS, LMTP delivery, SASL for Postfix |
| Rspamd | `km0-mail-rspamd-1` | internal | Anti-spam milter, DKIM signing |
| Roundcube | `km0-mail-roundcube-1` | 127.0.0.1:8080 | Webmail (Nginx TLS on :443) |

---

## First deploy

### 1. Secrets and Compose

```bash
cd /opt/km0-mail
cp .env.example .env
chmod 600 .env
# Edit passwords and ROUNDCUBE_DES_KEY
docker compose build
docker compose up -d
docker compose ps
docker compose logs -f postfix dovecot rspamd roundcube
```

### 2. Operational mailboxes

```bash
./scripts/km0-mail-admin create-mailbox postmaster@km0digital.com
./scripts/km0-mail-admin create-mailbox noreply@km0digital.com
./scripts/km0-mail-admin list-mailboxes
```

### 3. DKIM DNS record

```bash
./scripts/setup-dkim.sh
# Add TXT at Joker.com: mail._domainkey → value from script output
docker compose restart rspamd postfix
```

### 4. DNS (Joker.com)

| Type | Host | Value |
|------|------|-------|
| MX | `@` | `10 mail.km0digital.com` |
| A | `mail` | `116.202.10.106` |
| TXT | `@` | `v=spf1 mx a:mail.km0digital.com -all` |
| TXT | `mail._domainkey` | *(from setup-dkim.sh)* |
| TXT | `_dmarc` | `v=DMARC1; p=none; rua=mailto:postmaster@km0digital.com; adkim=s; aspf=s` |

**PTR (Hetzner):** `116.202.10.106` → `mail.km0digital.com`

Verify:

```bash
dig +short km0digital.com MX
dig +short mail.km0digital.com A
dig +short -x 116.202.10.106
```

### 5. Firewall (UFW)

Allow mail ports in addition to existing `22/80/443`:

```bash
ufw allow 25/tcp comment 'SMTP MX'
ufw allow 587/tcp comment 'SMTP submission'
ufw allow 993/tcp comment 'IMAPS'
ufw status verbose
```

### 6. Nginx + TLS (webmail only)

```bash
sudo cp nginx/sites-available/mail /etc/nginx/sites-available/mail
sudo ln -sf /etc/nginx/sites-available/mail /etc/nginx/sites-enabled/mail
sudo nginx -t

sudo certbot certonly --webroot -w /var/www/certbot \
  -d mail.km0digital.com --non-interactive --agree-tos -m postmaster@km0digital.com

sudo systemctl reload nginx
curl -sI https://mail.km0digital.com/ | head
```

Roundcube is **not** exposed on public HTTP; only `127.0.0.1:8080` for Nginx upstream.

### 7. Optional: host LE certs for IMAPS

Uncomment the LetsEncrypt volume mounts in `docker-compose.yml` for Dovecot, then:

```bash
docker compose up -d dovecot
```

### 8. Smoke test

```bash
./scripts/verify-mail-stack.sh
```

---

## Provisioning

```bash
# Mailbox
./scripts/km0-mail-admin create-mailbox user@km0digital.com

# Alias
./scripts/km0-mail-admin create-alias info@km0digital.com user@km0digital.com

# List
./scripts/km0-mail-admin list-mailboxes
./scripts/km0-mail-admin list-aliases
```

Mail passwords are **independent** from OpenCloud (phase 1). `opencloud_uuid` remains NULL until a future sync job.

`km0-mail-admin` creates Maildir `cur/new/tmp` and reloads Postfix hash maps automatically. To rebuild maps manually:

```bash
docker compose exec postfix build-hash-maps.sh
```

---

## Localhost SMTP relay (OpenCloud / apps)

Apps on the same host send via `127.0.0.1:587` **without auth** (restricted by Postfix `mynetworks`).

Example OpenCloud `.env` (after stack is live; OpenCloud runs in Docker — use `host.docker.internal`, not `127.0.0.1`):

```env
SMTP_HOST=host.docker.internal
SMTP_PORT=587
SMTP_SENDER=OpenCloud Notifications <noreply@km0digital.com>
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_INSECURE=true
SMTP_AUTHENTICATION=none
SMTP_TRANSPORT_ENCRYPTION=none
```

Also add to OpenCloud `external-proxy/opencloud.yml` `extra_hosts`: `host.docker.internal:host-gateway` (see km0-opencloud overrides).

Test relay from host:

```bash
swaks --to postmaster@km0digital.com --from noreply@km0digital.com \
  --server 127.0.0.1 --port 587 --header "Subject: relay test"
```

---

## Mail client settings

| Setting | Value |
|---------|-------|
| IMAP server | `mail.km0digital.com` |
| IMAP port | `993` (SSL/TLS) |
| SMTP server | `mail.km0digital.com` |
| SMTP port | `587` (STARTTLS) |
| Username | full address `user@km0digital.com` |
| Password | mailbox password from `km0-mail-admin` |

---

## Backups

Daily cron (align with OpenCloud):

```bash
echo '0 2 * * * root BACKUP_ROOT=/var/backups/km0-mail /opt/km0-mail/scripts/backup-maildir.sh >> /var/log/km0-mail-backup.log 2>&1' \
  | sudo tee /etc/cron.d/km0-mail-backup
```

Manual:

```bash
BACKUP_ROOT=/var/backups/km0-mail ./scripts/backup-maildir.sh
```

---

## Fail2ban

Copy jail template to host:

```bash
sudo cp config/fail2ban/jail.d/km0-mail.local /etc/fail2ban/jail.d/
sudo fail2ban-client reload
sudo fail2ban-client status
```

---

## Troubleshooting

| Symptom | Checks |
|---------|--------|
| Inbound bounce | `dig MX`, `nc -vz mail.km0digital.com 25`, `docker compose logs postfix` |
| Outbound spam folder | SPF/DKIM/DMARC/PTR — `Authentication-Results` headers |
| OpenCloud notify fail | Postfix `mynetworks`, `swaks` relay test on 587 |
| Roundcube 502 | `curl -sI http://127.0.0.1:8080/`, Nginx error log |
| Queue growth | `docker compose exec postfix mailq` |
| Auth failure | `./scripts/km0-mail-admin list-mailboxes`, Dovecot logs |
| 451 recipient lookup failure | `docker compose exec postfix build-hash-maps.sh`, check `postmap -q user@domain hash:/etc/postfix/virtual-mailbox-maps` |
| Mail stuck in queue (LMTP) | `docker compose exec postfix mailq`, verify Dovecot user: `doveadm user -f home user@km0digital.com` |

```bash
cd /opt/km0-mail
docker compose ps
docker compose logs --tail=100 postfix dovecot rspamd
```

---

## Rollback

1. `docker compose down` (retain volumes for data recovery)
2. Revert OpenCloud SMTP to previous outbound if needed
3. Disable Nginx `mail` vhost
4. Update/remove MX at Joker.com to stop inbound delivery

---

## References

- Pre-plan: [`issue-mail-preplan.md`](issue-mail-preplan.md)
- OpenCloud runbook: `/opt/opencloud/docs/runbook.md`
- Agent loop: [`agent-loop.md`](agent-loop.md)
