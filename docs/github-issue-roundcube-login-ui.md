# GitHub issue draft — KM0-branded Roundcube login (Elastic skin)

Create this issue on **AMVARA-CONSULTING/km0-mail**.

---

## Title

```
feat(ui): KM0-branded Roundcube login — custom Elastic skin
```

## Labels

- `enhancement`

(autoagents will add `agent:planned` when picked up)

---

## Issue body

Copy everything below this line into the GitHub issue description.

---

## Summary

Style **Roundcube’s native login screen** at `https://mail.km0digital.com` to match the KM0 Cloud visual identity (same look and feel as OpenCloud’s branded auth pages). Users open webmail and see **one** login page — username + password — with KM0 logo, colours, and typography.

**No SSO, no Dex, no Google button, no separate `/login.html` wrapper, no self-registration in this issue.**

Issue #3 (webmail SSO) was reverted because it added an extra auth layer that still landed on vanilla Roundcube. This issue fixes the actual UX gap: **restyle Roundcube itself**.

---

## Product decisions (fixed)

| Decision | Value |
|----------|--------|
| Login UX | **Single screen** — Roundcube login only (`/` → Roundcube) |
| Auth method | Existing **mailbox password** (Dovecot SQL passdb) — unchanged |
| Visual reference | OpenCloud auth pages: navy background, Inter font, KM0 logo, gradient accent |
| Reference repo paths (opencloud) | `host-www/opencloud-auth/login.html`, `logo.svg`, `favicon.svg` |
| i18n | Match OpenCloud login languages if feasible: **CA, ES, EN, DE** (or ES + EN minimum) |
| Registration | **Out of scope** — no `/register`, no register-api proxy |
| SSO / OAuth / Dex | **Out of scope** — deferred (`docs/github-issue-mail-sso.md`) |
| Nginx | Direct proxy to Roundcube (`127.0.0.1:8080`) — no static auth pages |

---

## What “done” looks like

1. User visits `https://mail.km0digital.com` → KM0-styled login (not default Elastic blue/grey).
2. KM0 logo visible on login; product name **KM0 Mail**; link to `https://km0digital.com` in footer/support area.
3. Favicon matches KM0 (svg or png).
4. After successful login, standard Roundcube Elastic inbox (inbox skin may stay default Elastic for v1 — login is the priority).
5. No redirect to `/login.html`; no broken register form.

---

## Implementation approach (recommended)

### Option A — Custom skin (preferred)

1. Copy Roundcube **Elastic** skin to `skins/km0/` (or `skins/km0-elastic/`).
2. Override login-related assets:
   - `styles/styles.less` / CSS — navy `#0b1220`, card styling, gradient accents
   - `templates/login.html` — logo markup, layout
   - `meta.json` — skin name, extends `elastic` if using inheritance
3. Mount skin in `docker-compose.yml`:

   ```yaml
   roundcube:
     volumes:
       - ./skins/km0:/var/www/html/skins/km0:ro
   ```

4. Set in `config/roundcube/config.inc.php`:

   ```php
   $config['skin'] = 'km0';
   $config['product_name'] = 'KM0 Mail';
   $config['support_url'] = 'https://km0digital.com/';
   ```

5. Copy brand assets from OpenCloud (`logo.svg`, `favicon.svg`) into the skin’s `images/` directory.

### Option B — Login plugin + CSS only (fallback)

If full skin fork is too heavy for v1, use a minimal plugin that injects custom CSS on the login task only. Prefer Option A for maintainability.

---

## Files to touch (this repo)

| Path | Action |
|------|--------|
| `skins/km0/` | **Create** — custom skin (templates, styles, images) |
| `config/roundcube/config.inc.php` | Set `skin`, ensure `product_name` / `support_url` |
| `docker-compose.yml` | Mount skin volume on `roundcube` service |
| `nginx/sites-available/mail` | **No auth-page locations** — verify direct proxy only |
| `docs/runbook.md` | Short “Roundcube branding” deploy note (restart roundcube after skin change) |

**Do not add:** `host-www/mail-auth/`, OAuth env vars, Dovecot OAuth, provision API.

---

## Visual spec (from OpenCloud login)

| Token | Value |
|-------|--------|
| Background | `#0b1220` + subtle purple radial gradient |
| Font | [Inter](https://fonts.google.com/specimen/Inter) (400–700) |
| Accent gradient | `#ff5f2e` → `#e040a0` → `#7b3fe4` → `#007bff` |
| Card | ~440px, rounded 20px, glass-style border `rgba(255,255,255,0.08)` |
| Logo | KM0 SVG, ~192px on login |

Source: `/opt/opencloud/host-www/opencloud-auth/login.html` (inline styles) — adapt to Roundcube Less/CSS structure, do not iframe external pages.

---

## External documentation

| Topic | Link |
|-------|------|
| Roundcube skins | https://github.com/roundcube/roundcubemail/wiki/Skins |
| Roundcube skin development | https://github.com/roundcube/roundcubemail/wiki/Skin-development |
| Roundcube configuration | https://github.com/roundcube/roundcubemail/wiki/Configuration |
| Elastic skin (upstream reference) | https://github.com/roundcube/roundcubemail/tree/master/skins/elastic |
| Roundcube Docker image | https://hub.docker.com/r/roundcube/roundcubemail |
| Less/CSS (Elastic uses Less) | https://lesscss.org/ |

---

## Operator actions

| # | Action | Required? |
|---|--------|-----------|
| 1 | `docker compose up -d roundcube` after skin mount | Yes |
| 2 | Clear browser cache / hard refresh on login | Yes (verify) |
| 3 | Google Cloud Console | **No** |
| 4 | Dex / OpenCloud changes | **No** |
| 5 | DNS / MX changes | **No** |

Deploy nginx only if the vhost template changed (should remain simple Roundcube proxy).

---

## Out of scope

- Self-registration (`/register`, register-api)
- SSO (Dex, Google, LDAP OIDC)
- Dovecot / Postfix auth changes
- Inbox UI redesign (beyond login page for v1)
- Email verification flows

---

## Test plan

- [ ] `https://mail.km0digital.com` shows KM0-branded login (no `/login.html` redirect)
- [ ] Logo and favicon load (no 404 on skin assets)
- [ ] Login with CLI-provisioned mailbox (`km0-mail-admin create-mailbox`) succeeds
- [ ] Wrong password shows error on styled page (still readable)
- [ ] Mobile viewport (~375px): login card usable
- [ ] `./scripts/verify-mail-stack.sh` passes
- [ ] OpenCloud / mail delivery unchanged (regression)

---

## Acceptance criteria

- [ ] Native Roundcube login matches KM0 Cloud auth visual language
- [ ] No extra login layer or nginx auth static pages
- [ ] No SSO/OAuth/register code added
- [ ] Runbook updated with skin deploy steps

---

## Follow-up (separate issues — do not implement here)

1. **Registration** — register-api + mailbox provisioning + CORS (km0-mail + km0-opencloud)
2. **SSO** — revised Dex OIDC plan (`docs/github-issue-mail-sso.md`, rewrite before use)

---

## Related

- Reverted SSO attempt: GitHub issue #3, `docs/github-issue-mail-sso.md`
- Mail pre-plan: `docs/issue-mail-preplan.md`
- OpenCloud login reference: km0-opencloud `host-www/opencloud-auth/`
