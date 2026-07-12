# km0-opencloud integration for public mail registration

Cross-repo work required on **AMVARA-CONSULTING/km0-opencloud** (sibling to km0-mail).

## Dex static clients

Add to Dex configuration:

| Client | Type | Redirect URI |
|--------|------|--------------|
| `km0-mail-web` | public | `https://mail.km0digital.com/index.php/login/oauth` |
| `km0-mail-dovecot` | confidential | (introspection only) |

Set secrets in km0-mail `.env`: `ROUNDCUBE_OAUTH_CLIENT_SECRET`, `DOVECOT_OAUTH_CLIENT_SECRET`.

## register-api extensions

- Accept `create_mail`, `mail_mode` (`km0`|`custom`), `desired_email`, `contact_email`
- Freemail blocklist for mailbox domains (not contact email)
- After IDM user creation, POST to `http://127.0.0.1:8092/provision` with Bearer `MAIL_PROVISION_API_TOKEN`
- On password change, POST to `/update-password`

## OpenCloud register UI

Optional checkbox on `cloud.km0digital.com` register form:

> Create a KM0 Mail account

When checked, pass `create_mail=true` and `mail_mode` to register-api.

## Mail hostname Dex UI

Expose **LDAP connector only** on mail auth pages. Hide Google connector for requests originating from `mail.km0digital.com`.

## Nginx on cloud host

register-api listens on `127.0.0.1:8091`. Mail nginx proxies `/api/register` same-origin (already in km0-mail vhost).

## Smoke checklist

- [x] Register `newuser@km0digital.com` via `/register` creates IDM + mailbox
- [ ] LDAP login at `/login.html` reaches Roundcube inbox (requires Dovecot OAuth2 driver on km0-mail — Debian Bookworm stock image pending)
- [x] Password login at `/index.php?_task=login` works for provisioned user
- [x] `@gmail.com` as mailbox rejected; as contact accepted
- [x] Cloud register checkbox provisions mail when checked

See also: `docs/issue-mail-registration-preplan.md` (km0-mail repo)
