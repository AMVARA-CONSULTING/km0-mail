# OpenCloud cross-repo integration — Mail SSO (issue #3)

km0-mail SSO reuses Dex at `https://cloud.km0digital.com/dex`. These changes belong in **km0-opencloud** (sibling repo) and must be deployed before SSO works end-to-end.

## Dex static clients (`dex/config.yaml`)

Add to `staticClients`:

```yaml
- id: km0-mail-web
  redirectURIs:
    - https://mail.km0digital.com/index.php/login/oauth
  name: KM0 Mail Webmail
  secret: <ROUNDCUBE_OAUTH_CLIENT_SECRET from km0-mail .env>

- id: km0-mail-dovecot
  name: KM0 Mail Dovecot introspection
  secret: <DOVECOT_OAUTH_CLIENT_SECRET from km0-mail .env>
```

Restart Dex after editing. Secrets must match `/opt/km0-mail/.env`.

## register-api mailbox hook

After successful Graph user creation (`POST /register` → 201), call km0-mail provision API:

```http
POST http://127.0.0.1:8092/provision
Authorization: Bearer <MAIL_PROVISION_API_TOKEN>
Content-Type: application/json

{"email":"user@km0digital.com","password":"<same as registration>","opencloud_uuid":"<from Graph response if available>"}
```

Or from host:

```bash
cd /opt/km0-mail
./scripts/km0-mail-admin provision-sso-mailbox user@km0digital.com
```

## register-api CORS / origin

Either:

- Set `ALLOWED_ORIGIN=https://mail.km0digital.com` (breaks OpenCloud register), **or**
- Rely on mail nginx proxy (`/api/register` → `127.0.0.1:8091`) so browser `Origin` is `https://mail.km0digital.com` — register-api must accept that origin (multi-origin support or separate env).

Recommended: extend register-api to accept comma-separated `ALLOWED_ORIGINS` including both cloud and mail hostnames.

## Operator checklist (both repos)

| Step | Repo | Action |
|------|------|--------|
| 1 | km0-mail | Set OAuth + provision secrets in `.env`; `docker compose up -d --build` |
| 2 | km0-opencloud | Add Dex clients; restart Dex |
| 3 | km0-opencloud | register-api mail provision hook + allowed origin |
| 4 | host | `rsync host-www/mail-auth/` → `/var/www/mail-auth/` |
| 5 | host | Deploy `nginx/sites-available/mail`; reload nginx |
| 6 | smoke | Google + LDAP + legacy `postmaster@` login |

See also [`docs/runbook.md`](runbook.md) § Webmail SSO.
