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

Mailbox passwords are set by the self-contained public `POST /api/register` (`mail-provision-api`, :8092) when users self-register; no cross-repo km0-opencloud register-api (:8091) is required for the happy path. CLI mailboxes are created verified by default.

## Public registration (Model A + B)

Deploy auth static files and updated nginx vhost:

```bash
sudo rsync -a host-www/mail-auth/ /var/www/mail-auth/
sudo cp nginx/sites-available/mail /etc/nginx/sites-available/mail
sudo nginx -t && sudo systemctl reload nginx
```

Apply DB migration on existing volumes (non-destructive):

```bash
./scripts/apply-registration-migration.sh
docker compose up -d --build
```

That script also applies `sql/init/04-one-mailbox-per-uuid.sql` (issue #13): unique `opencloud_uuid` (NULLs allowed), `contact_email` index, and clears duplicate uuid links on older rows before creating the unique index.

**Provision API** (Bearer `MAIL_PROVISION_API_TOKEN`, localhost `:8092`):

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/provision` | Create/link mailbox; same uuid+email → `200 exists`; same uuid+other email → `409 uuid_already_linked` |
| `POST` | `/activate` | Activate Mail for Cloud user: `local_part` + `opencloud_uuid` + `contact_email` + `password` → `foo@km0digital.com` (rejects freemail mailbox) |
| `POST` | `/link` | Attach `opencloud_uuid` (+ optional `contact_email`) to an existing mailbox |
| `GET` | `/lookup/by-uuid/<opencloud_uuid>` | Resolve mailbox; `404` + `activate_required` if missing |
| `GET` | `/lookup/by-contact/<contact_email>` | Resolve by freemail contact |

**Activate Mail (Google / OIDC Cloud users):** freemail stays `contact_email`; mailbox is always `@km0digital.com` (or custom). After activate:

1. **Password login** — Roundcube native form at `/index.php?_task=login&activated=1` (works without waiting on OAuth/#9). Google IdP cannot open the mailbox or complete verify.
2. **Verify** — open the in-band verification email in the inbox → `/verify?token=…`. Pending mailboxes can read; outbound SMTP on 587 stays blocked until verified. Roundcube shows `km0_verification_banner` while `verification_status=pending`.
3. **LDAP OAuth** (optional) — Dex `connector_id=ldap` once IDM `mail` equals the mailbox and Dovecot XOAUTH2 is live (#9). Do not use Google IdP for Roundcube ([#12 wontfix](spike-google-idp-roundcube-mailbox-map.md)).

`POST /activate` response `entry` includes `password_login_url` (with `activated=1`), `verify_path`, and ordered `next_steps`.

**Hub SSO (OPTIONAL / LEGACY — Cloud users only, issue #14, supersedes #11):** the Auth Hub / Dex path is **not** the default entry point. It applies only to existing OpenCloud (Google/OIDC) users who want SSO. When used, the Auth Hub sets `sso=all` on the cloud bridge and `?service=mail` (not `?service=cloud` alone); after Cloud login, `/sso-continue` is a **chooser** (LDAP OAuth / [Activate KM0 Mail](https://cloud.km0digital.com/activate-mail.html) / mailbox password) — no auto `prompt=none` (avoids Google-only loops). Session-gate `#22` cloud→`/files` unchanged. Identity preserve: opencloud #24. Pipeline: [`agent-pipeline-mail-activate.md`](agent-pipeline-mail-activate.md).

### Post-activate checklist (issue #15)

Operator / QA happy path (no Google for mail):

1. Cloud user completes [activate-mail.html](https://cloud.km0digital.com/activate-mail.html) → success copy points to Roundcube password login (`activated=1`).
2. Sign in at `https://mail.km0digital.com/index.php?_task=login&activated=1` with `foo@km0digital.com` + mailbox password — banner explains verify step.
3. Inbox shows verification mail; open link → `https://mail.km0digital.com/verify?token=…` succeeds.
4. Confirm outbound: submit on 587 works only after verified (pre-verify = reject).
5. Optional: hub LDAP OAuth into Roundcube as same mailbox (needs #9).

| URL | Purpose |
|-----|---------|
| `/` | Serves the native branded login page (`login.html`, HTTP 200) — **canonical**. Roundcube tasks with `?args` go to `/index.php` |
| `/login.html` | Native branded login (mailbox email + password primary; hub/LDAP SSO demoted to "Other ways to sign in") |
| `/index.php?_task=login` | Roundcube password form (add `&activated=1` after activate) |
| `/register` | Self-registration Model A (`@km0digital.com`) or B (custom domain) — served locally; `POST /api/register` → `mail-provision-api` (:8092) |
| `/domain.html?domain=example.com` | DNS wizard (Model B) |
| `/verify?token=…` | Email verification (Model A / activate) |

**Auth tracks:** native mailbox password login (Roundcube SQL passdb) is the canonical path — no Auth Hub redirect. LDAP OAuth (Dex `connector_id=ldap` only — Google is Cloud IdP, not Roundcube) is **optional/legacy** for Cloud users. See [`opencloud-registration-integration.md`](opencloud-registration-integration.md) for the optional km0-opencloud prerequisites.

**Pre-verification:** pending mailboxes can log in and receive mail; outbound SMTP on port 587 is blocked until verified.

**Test account:** use `test@km0digital.com` after provisioning via register flow or `./scripts/km0-mail-admin create-mailbox test@km0digital.com`.

`km0-mail-admin` creates Maildir `cur/new/tmp` and reloads Postfix hash maps automatically. To rebuild maps manually:

```bash
docker compose exec postfix build-hash-maps.sh
```

---

## Custom domain onboarding (Model B, end-to-end)

Runs a customer-owned domain on this stack: inbound delivery, native password login
for `user@customdomain`, and outbound mail DKIM-signed with the domain's **own** key.
Everything is DB-driven — no per-domain config edits or code changes. Example below
uses `ldeluipy.es`; substitute any real domain the operator controls DNS for.

1. **Register** — the user signs up in `custom` mode (self-service or operator):

   ```bash
   curl -s -X POST https://mail.km0digital.com/api/register -H 'Content-Type: application/json' \
     -d '{"email":"admin@ldeluipy.es","mail_mode":"custom","password":"<strong-pass>"}'
   ```

   Creates a **pending** `mail_domains` row (`active=false`) and the mailbox, and the
   response `continue_to` sends the browser to `/domain.html?domain=ldeluipy.es`.

2. **DNS wizard** — `/domain.html?domain=ldeluipy.es` loads and calls the public
   `GET /api/mail/domain/<domain>/status`. On first view the domain's DKIM keypair is
   generated and persisted (both public and **private** keys in `mail_domains`), and the
   four records to publish are shown. Add them at the registrar:

   | Type | Host | Value |
   |------|------|-------|
   | TXT | `@` | `km0-mail-verification=<token>` |
   | MX | `@` | `mail.km0digital.com` (priority 10) |
   | TXT (SPF) | `@` | `v=spf1 mx a:mail.km0digital.com ~all` |
   | TXT (DKIM) | `mail._domainkey` | `v=DKIM1; k=rsa; p=<public key from wizard>` |

3. **Verify** — the user clicks **Check again**, which POSTs to
   `/api/mail/domain/<domain>/check` (public, per-IP rate-limited). When all four
   records resolve, the domain flips to `active=true` / `verified` and, in one step:
   - **Inbound:** `reload_postfix_maps()` rebuilds the Postfix hash maps so
     `@ldeluipy.es` is an accepted `virtual_mailbox_domain`.
   - **Outbound:** the domain's private key is materialized to
     `/var/lib/rspamd/dkim/ldeluipy.es.mail.key` (owned by `_rspamd`, `0600`) and Rspamd
     is soft-reloaded (SIGHUP). Rspamd's generic `$domain.$selector.key` map then signs
     outbound mail from `admin@ldeluipy.es` with `d=ldeluipy.es`.

4. **Login** — `admin@ldeluipy.es` signs in at the native login with email + password
   (Dovecot SQL passdb; no OAuth required). Custom mailboxes are `verified` once their
   domain verifies, so outbound on 587 is unblocked.

**Operator checks:**

```bash
# domain active + both DKIM keys stored
docker compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c \
  "SELECT name, active, verification_status, (dkim_public_key IS NOT NULL) pub, (dkim_private_key IS NOT NULL) priv FROM mail_domains WHERE name='ldeluipy.es';"
# signing key present in Rspamd
docker compose exec rspamd ls -l /var/lib/rspamd/dkim/ | grep ldeluipy
# Postfix accepts the domain
docker compose exec postfix postmap -q ldeluipy.es hash:/etc/postfix/virtual-mailbox-domains
```

**Recovery:** the private key lives in the (trusted) DB. If the Rspamd volume is lost,
the next successful `/check` for the domain re-materializes the key from the DB — no key
rotation or DNS change needed. To force re-materialization, POST `/check` again.

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

## Roundcube branding (KM0 skin)

Webmail login uses a custom **`km0`** skin (extends Elastic) mounted from `skins/km0/`. Inbox UI remains standard Elastic; only the login page is KM0-branded.

After changing skin assets or `config/roundcube/config.inc.php`:

```bash
cd /opt/km0-mail
docker compose up -d roundcube
curl -sI http://127.0.0.1:8080/ | head -5
# Hard-refresh browser cache when verifying login CSS/logo
```

Skin files: `skins/km0/templates/login.html`, `skins/km0/styles/km0-login.css`, `skins/km0/js/i18n.js`, `skins/km0/images/logo.svg`, `skins/km0/images/favicon.svg`.

Asset URLs in skin templates must be **skin-relative** (e.g. `/js/i18n.js`, `/images/logo.svg`). Do not hardcode `/skins/km0/...` — Roundcube prefixes the skin path and would double it.

Login page language switch (CA/ES/EN/DE) uses client-side i18n; default Roundcube locale is `en_US` in `config/roundcube/config.inc.php`.

---

## Dovecot image rebuild

After changing `docker/dovecot/entrypoint.sh`, `Dockerfile`, or reverting SSO/OAuth env requirements, **rebuild the Dovecot image** — a stale image keeps the old entrypoint and the container will restart-loop:

```bash
cd /opt/km0-mail
git pull
docker compose build dovecot --no-cache
docker compose up -d dovecot
docker compose logs --tail=20 dovecot   # expect "OAuth2/XOAUTH2 enabled" or "OAuth2 disabled"
nc -vz 127.0.0.1 993
docker compose exec dovecot doveadm auth test postmaster@km0digital.com '<password>'
# CAPABILITY should list AUTH=XOAUTH2 when OAuth is enabled:
# openssl s_client -connect 127.0.0.1:993 -quiet <<<'' | head -1
```

**OAuth2 / LDAP SSO:** The Dovecot image uses **Dovecot CE 2.4** from `repo.dovecot.org` (not Debian Bookworm 2.3). CE 2.4 has built-in OAuth2/XOAUTH2. When `DOVECOT_OAUTH_CLIENT_SECRET` is set, the entrypoint enables `xoauth2`/`oauthbearer` plus Dex token introspection (`username_attribute=email`). SQL `plain`/`login` remain available for password users. Without the secret, password-only auth is used.

**Rebuild note:** Dovecot 2.4 config syntax differs from 2.3 (`mail_driver`/`mail_path`, `ssl_server_*_file`, named listeners, inline SQL). Do not revert `config/dovecot/dovecot.conf` to 2.3 syntax.

After changing Postfix sender-verification templates or entrypoint, rebuild Postfix too:

```bash
docker compose build postfix --no-cache && docker compose up -d postfix
docker compose exec postfix postconf smtpd_sender_restrictions
```

Symptom: `docker compose ps` shows Dovecot **Restarting**; Roundcube login returns 401 / *IMAP connection error*; `doveadm auth test` times out with *Couldn't connect to auth socket*.

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
