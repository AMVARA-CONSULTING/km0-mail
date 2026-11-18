# Mailcow cutover status (mail.km0digital.com)

**Host:** amvara10 · **Live:** `/opt/mailcow-dockerized` · **Legacy:** `/opt/km0-mail` (stopped, volumes kept)

## Done (Phases 0–3 + ops)

* Backup under `/root/backups/km0-mail-pre-mailcow-*`
* Parallel Mailcow install; import 8 domains / ~40 mailboxes / aliases
* Maildir sync; cutover ports 25/465/587/993; nginx → Mailcow `:8880`
* SOGo SSO fixed (proxy + SOGo bootstrap after domain import)
* Bulk mailbox passwords; catch-all `@ldeluipy.es` → `luipy@ldeluipy.es`
* Redmine migration ticket: #8480 (parent hub #7605)

## Paused — Phase 4 (do not start until soak)

**Why pause:** cutover is fresh; sending reputation is still recovering. Phase 4 changes auth and clients; a bad IdP wire-up would look like “mail is down” while spamscore noise continues. Keep local passwords as the working path for now.

Phase 4 items (when resumed):

1. Domain admins (per-domain self-serve)
2. Keycloak client + Mailcow IdP (pilot user first)
3. Certbot → Mailcow SSL hook
4. Dependents (provision-api, MMS already pointed at Mailcow, SMTP consumers)
5. DKIM/DNS review if keys changed
6. Then Phase 5 soak ≥14 days before deleting km0-mail volumes

## Ports

* Public mail: **unchanged** 25 / 465 / 587 / 993
* UI: HTTPS 443 → host nginx → Mailcow HTTP 8880 (8444 local HTTPS)

## Branding

Roundcube `km0_theme` is legacy. Mailcow/SOGo KM0 look: pack in `config/mailcow-branding/`, apply with `scripts/apply-mailcow-branding.sh` (re-run after Mailcow `./update.sh`). See `docs/mailcow-branding.md`.
