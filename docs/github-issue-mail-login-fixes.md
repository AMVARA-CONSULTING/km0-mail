# GitHub issue — fix KM0 login (IMAP auth, input icons, i18n)

Published via `gh issue create` — see GitHub for issue number.

---

## Title

```
fix(ui): KM0 login — restore IMAP auth, fix input icons, add language switch
```

## Labels

- `bug`

---

## Summary

Issue #4 delivered the KM0 Roundcube login skin, but **production login is broken** and the form UI is incomplete:

1. **IMAP connection error** — logging in as `postmaster@km0digital.com` returns `401 Unauthorized` and Roundcube shows *"ERROR DE CONEXIÓN CON EL IMAP"* (`POST /?_task=login` → 401).
2. **Input icons misaligned** — Elastic `input-group-prepend` user/lock icons render as broken grey boxes beside username/password fields (should match OpenCloud: clean inputs, no prepend icons).
3. **No language switch** — OpenCloud login has CA/ES/EN/DE; KM0 mail login is missing this (minimum: **English** as default or selectable).

---

## Root cause analysis (confirmed on server 2026-06-16)

### IMAP / 401

| Observation | Detail |
|-------------|--------|
| Dovecot container | **Restart loop** — `docker compose ps` shows `Restarting` |
| Logs | `/entrypoint.sh: DOVECOT_OAUTH_CLIENT_SECRET required` |
| Git state | SSO revert removed OAuth from `docker-compose.yml` and `entrypoint.sh` |
| Running image | **Stale Dovecot image** still built from SSO-era entrypoint requiring OAuth env vars |
| Roundcube | Up and serving skin; cannot reach IMAP on `dovecot:993` |

**Fix:** Rebuild Dovecot image from current repo (`docker compose build dovecot --no-cache`) and recreate container. Verify port 993 and IMAP auth with `postmaster@km0digital.com`. Do **not** reintroduce OAuth env vars unless SSO is re-planned.

Issue #4 testing marked valid login **N/A** because Dovecot was already down — this should have blocked closing #4.

### Input icons

Skin CSS (`skins/km0/styles/km0-login.css`) converts login `<table>` rows to `display: block` but does **not** style or hide Elastic’s `.input-group-prepend` / `.input-group-text` (user + lock icons). OpenCloud auth uses plain inputs without prepend icons.

**Fix:** Either hide prepend icons on login (`display: none` on `.input-group-prepend`) **or** restyle as inline flex (prefer hide — matches OpenCloud).

Affected DOM (from browser):

```text
form#login-form > table > tbody > tr.form-group.row > td.input.input-group.input-group-lg
```

### i18n

`skins/km0/templates/login.html` hardcodes Spanish tagline (*"Origen local · Impacto digital"*) and has no language switch. OpenCloud reference: `host-www/opencloud-auth/login.html` + `/dex/theme/i18n.js` (CA, ES, EN, DE).

**Fix (minimum):** Default Roundcube locale to **English** (`$config['language'] = 'en_US'` in `config.inc.php`) **or** add KM0 language switch on login page reusing OpenCloud i18n pattern / Roundcube labels.

---

## Scope

### In scope

- [ ] Restore Dovecot (rebuild + verify IMAP login for `postmaster@km0digital.com`)
- [ ] Fix login input styling (remove/fix broken prepend icons)
- [ ] Add language support (minimum EN; ideally CA/ES/EN/DE like OpenCloud)
- [ ] Update runbook with Dovecot rebuild note after SSO revert
- [ ] Re-test and document — do not close until **valid password login** passes in browser

### Out of scope

- SSO / Dex / Google login
- Self-registration
- Inbox UI redesign

---

## Implementation hints

### Dovecot recovery

```bash
cd /opt/km0-mail
git pull   # ensure post-SSO-revert entrypoint
docker compose build dovecot --no-cache
docker compose up -d dovecot
docker compose logs --tail=20 dovecot   # must NOT show OAuth secret error
nc -vz 127.0.0.1 993
docker compose exec dovecot doveadm auth test postmaster@km0digital.com '<password>'
```

### Icon CSS (example)

```css
body.task-login #login-form .input-group-prepend,
body.task-login #login-form .input-group-text {
  display: none !important;
}
body.task-login #login-form .input-group .form-control {
  border-radius: 12px;
  width: 100%;
}
```

### i18n options

| Approach | Pros |
|----------|------|
| `$config['language'] = 'en_US'` | Quick default English |
| Roundcube `login.html` + labels | Uses Roundcube gettext |
| Port OpenCloud `i18n.js` + switch | Matches cloud UX |

Reference: km0-opencloud `host-www/opencloud-auth/login.html`, `dex/web/themes/km0/i18n.js`

---

## External documentation

| Topic | Link |
|-------|------|
| Roundcube skins | https://github.com/roundcube/roundcubemail/wiki/Skins |
| Roundcube localization | https://github.com/roundcube/roundcubemail/wiki/Configuration#language |
| Roundcube login template | https://github.com/roundcube/roundcubemail/tree/master/skins/elastic/templates/login.html |
| Dovecot auth troubleshooting | https://doc.dovecot.org/main/core/config/auth/passdb.html |
| Dovecot SQL passdb | https://doc.dovecot.org/main/core/config/auth/databases/sql.html |

---

## Test plan

### Infrastructure (must pass before UI sign-off)

- [ ] `docker compose ps` — **dovecot Up**, not Restarting
- [ ] `docker compose logs dovecot` — no `DOVECOT_OAUTH_CLIENT_SECRET` errors
- [ ] `nc -vz mail.km0digital.com 993` — open
- [ ] `./scripts/verify-mail-stack.sh` — all green (including Dovecot)

### Login auth (browser — **required**)

- [ ] `https://mail.km0digital.com/` — KM0 skin loads
- [ ] Login `postmaster@km0digital.com` + correct password → **inbox** (no IMAP error, no 401)
- [ ] Wrong password → styled error on same page (no white screen)
- [ ] DevTools: `POST /?_task=login` → **302/200 success**, not 401, on valid credentials

### UI

- [ ] Username/password fields — **no** broken grey icon boxes (match OpenCloud clean inputs)
- [ ] Logo, gradient title, navy card unchanged
- [ ] Language switch visible OR default English strings on login
- [ ] Mobile ~375px — form usable

### Regression

- [ ] SMTP/IMAP delivery unchanged
- [ ] `./scripts/km0-mail-admin list-mailboxes` unchanged

---

## Acceptance criteria

- [ ] `postmaster@km0digital.com` can log in via webmail and read mail
- [ ] Login inputs visually match OpenCloud (no misaligned prepend icons)
- [ ] English available (default or via switch)
- [ ] Runbook documents Dovecot rebuild after image/entrypoint changes
- [ ] Issue not closed until browser login test passes (unlike #4)

---

## Related

- #4 — KM0-branded Roundcube login (closed prematurely; Dovecot N/A)
- #3 — SSO revert (`d65eff5`)
- OpenCloud login reference: km0-opencloud `host-www/opencloud-auth/login.html`
