# FEAT-Task: Post-activate verification happy path (password → verify → LDAP OAuth)

## GitHub Issue
- **Number:** #15
- **URL:** https://github.com/AMVARA-CONSULTING/km0-mail/issues/15
- **Labels:** enhancement
- **After:** activate wizard (#25) + password login; soft-after #9 for OAuth step

## Problem / goal
Users must verify `@km0` via inbox; Google-only path cannot skip password login for verify.

## High-level instructions for coder
1. Ensure hub/wizard success copy → Roundcube password login + verify banner
2. Runbook checklist activate→verify→send; CHANGELOG
3. Minimal UI links only; FEAT→UNTESTED

## Acceptance criteria
- [x] Documented + linked UX path without Google IdP for verify
- [x] No secrets

## Implementation notes (2026-07-25)

**km0-mail**
- `mail-provision-api` `entry` hints: `password_login_url` with `activated=1`, `verify_path`, ordered `next_steps`, Google-not-for-mail note
- Roundcube login skin: `?activated=1` and `?hint=google` / `google_only=1` banners (CA/ES/EN/DE) + CSS
- Docs: runbook post-activate checklist, CHANGELOG, opencloud-registration-integration

**Cross-repo**
- `/opt/opencloud` activate wizard success body + Roundcube link → `…/index.php?_task=login&activated=1`; Dex theme i18n (4 langs)
- `/opt/km0-auth` hub activate hint mentions verify; `MAIL_POST_ACTIVATE_LOGIN` / `goMailPostActivateLogin`; sibling `tasks/NEW-0-20260725-1436-hub-post-activate-verify-copy.md`

Inbound verify banner in Roundcube inbox (`km0_verification_banner`) already existed for `pending` mailboxes.

## Testing instructions

1. Provision API entry shape:
   ```bash
   cd /opt/km0-mail
   set -a; source .env; set +a
   curl -sS -X POST -H "Authorization: Bearer $MAIL_PROVISION_API_TOKEN" \
     -H 'Content-Type: application/json' \
     -d '{"local_part":"t15qa","opencloud_uuid":"qa-15-'"$(date +%s)"'","contact_email":"qa@gmail.com","password":"TmpPass15!x","send_verification":false}' \
     http://127.0.0.1:8092/activate | python3 -m json.tool
   ```
   Expect `entry.password_login_url` ending in `activated=1`, `entry.next_steps` starting with `password_login`, `entry.verify_path` = `https://mail.km0digital.com/verify`.

2. Roundcube activated banner (HTML + i18n):
   ```bash
   curl -sS 'https://mail.km0digital.com/index.php?_task=login&activated=1' | grep km0-activated-banner
   curl -sS 'https://mail.km0digital.com/skins/km0/js/i18n.js' | grep activatedBanner
   ```
   Browser: open the URL — success banner visible; with `&hint=google` warn banner also visible.

3. Wizard + hub copy:
   ```bash
   curl -sS https://cloud.km0digital.com/activate-mail.html | grep 'activated=1'
   curl -sS https://cloud.km0digital.com/dex/theme/i18n.js | grep -F 'verification email'
   curl -sS https://auth.km0digital.com/hub-auth.js | grep MAIL_POST_ACTIVATE_LOGIN
   /opt/km0-auth/scripts/verify-auth-hub.sh
   ```

4. Manual happy path (recommended):
   - Activate at `https://cloud.km0digital.com/activate-mail.html` → success → Open Roundcube (password URL with `activated=1`).
   - Password login as `foo@km0digital.com` → inbox shows verify mail + `km0-verify-banner` while pending.
   - Click `/verify?token=…` → success; outbound on 587 works.
   - Confirm Google cannot substitute for this path (no Google button on Roundcube password form).

5. Docs:
   ```bash
   grep -n 'Post-activate checklist\|activated=1' /opt/km0-mail/docs/runbook.md /opt/km0-mail/docs/CHANGELOG.md
   ```

6. Stack health: `docker compose ps` (mail-provision-api, roundcube, dovecot healthy). No secrets in diffs.
