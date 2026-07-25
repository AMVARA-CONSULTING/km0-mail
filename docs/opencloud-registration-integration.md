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
- **Activate Mail** (existing Google/OIDC Cloud users, opencloud #23): POST `http://127.0.0.1:8092/activate` with `local_part` (or `email`), `opencloud_uuid`, `contact_email` (freemail OK), `password` (≥8). Response includes `entry` hints: `password_login_url` (`…/index.php?_task=login&activated=1`), `verify_path`, ordered `next_steps` (password → open verification email → `/verify` → optional LDAP OAuth).
- Link existing mailbox: POST `/link` with `email` + `opencloud_uuid` (+ optional `contact_email`)
- On password change, POST to `/update-password`
- Activate / hub: `GET /lookup/by-uuid/<opencloud_uuid>` and `GET /lookup/by-contact/<email>` (same Bearer token). Missing mailbox → `404` + `activate_required: true`.
- Idempotency: second `/provision` or `/activate` with the same `opencloud_uuid` and email returns `200 exists`; same uuid with a different email returns `409 uuid_already_linked` (one mailbox per OpenCloud user)

## Identity model (Google / freemail OIDC)

| Concept | Value |
|---------|--------|
| Cloud IdP | Google (or Apple, …) — freemail address |
| Mailbox | Always `foo@km0digital.com` (or verified custom domain) |
| `contact_email` | Freemail / recovery address |
| `opencloud_uuid` | Link Cloud user ↔ mailbox (unique, issue #13) |
| Roundcube password | Works immediately after `/activate` — **required** to read verify mail |
| Verification | Inbox → `/verify?token=…`; outbound blocked until verified |
| Roundcube OAuth | Dex **LDAP only** so token `email` = mailbox (needs #9 XOAUTH2); optional after verify |

Do **not** enable Dex `connector_id=google` for Roundcube in this path — spike [#12](https://github.com/AMVARA-CONSULTING/km0-mail/issues/12) closed as **wontfix** ([design](./spike-google-idp-roundcube-mailbox-map.md)). Coordinate opencloud **#24** before shipping activate UX that rewrites Graph `mail` and breaks Google re-login.

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
- [ ] LDAP login at `/login.html` reaches Roundcube inbox (Dovecot OAuth2 / #9 — verify in tester)
- [x] Password login at `/index.php?_task=login` works for provisioned user
- [x] `@gmail.com` as mailbox rejected; as contact accepted
- [x] Cloud register checkbox provisions mail when checked
- [ ] `POST /activate` for Google Cloud user → `foo@km0digital.com` + uuid + contact_email; password Roundcube login works
- [ ] Lookup by uuid with no mailbox → `activate_required: true`
- [ ] Post-activate: password login → verification email → `/verify` → send enabled (no Google IdP for verify; issue #15)

See also: `docs/issue-mail-registration-preplan.md`, `docs/agent-pipeline-mail-activate.md` (km0-mail repo)
