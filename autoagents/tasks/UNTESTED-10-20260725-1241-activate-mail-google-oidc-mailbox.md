# FEAT-Task: Activate KM0 Mail for Google/OIDC Cloud users (mailbox foo@km0digital.com)

## GitHub Issue
- **Number:** #10
- **URL:** https://github.com/AMVARA-CONSULTING/km0-mail/issues/10
- **Labels:** enhancement, agent:wip
- **Redmine tracking:** #7605 (when configured)
- **Depends on:** #9 (OAuth→inbox for LDAP path); coordinates with opencloud #23, mail #11/#14
- **Must not clash:** #8 (i18n path), #22 session-gate (opencloud)

## Problem / goal
Google/OIDC-only Cloud users cannot get mail with freemail as mailbox. Activate Mail: user picks `foo` → mailbox `foo@km0digital.com`, `contact_email`=Gmail, `opencloud_uuid` linked. Roundcube **OAuth login** remains **Dex LDAP** so token `email` claim equals the mailbox (required by Dovecot `username_attribute=email`). Roundcube `oauth_login` cannot rewrite username — do not rely on freemail→mailbox remap in that hook alone.

## High-level instructions for coder
1. `./scripts/git-sync-main.sh`.
2. Extend `mail-provision-api`: activate/link APIs (lookup by `opencloud_uuid` / `contact_email`); indexes if missing; reject freemail as mailbox; allow freemail contact.
3. Document password + LDAP OAuth entry; leave Google-connector→Roundcube to #12 spike.
4. Soft-fail UX hooks only if needed; primary activate UI is hub (#11/#14) + register-api (#23).
5. Update `docs/issue-mail-registration-preplan.md` / CHANGELOG / runbook: Google = Cloud IdP; mailbox always @km0 or custom.
6. FEAT→WIP→UNTESTED; gh labels on #10.

## Acceptance criteria
- [x] Activate/link provisions `foo@km0digital.com` with uuid + contact_email
- [x] Password Roundcube login works without waiting on #9
- [x] LDAP OAuth path documented for post-#9
- [x] No freemail mailbox; no secrets; docs updated

## Blocker update (20260725-1325)
- Coordinate with opencloud **#24** (Google re-login after Graph mail PATCH). Do not ship activate UX that strands Google users. (API + docs only in this task; hub CTA remains #14.)

## Implementation notes (2026-07-25)
- `POST /activate`: `local_part`|`email` + required `opencloud_uuid`, `contact_email`, `password` (≥8); returns `entry` hints (password URL + LDAP OAuth notes + opencloud #24 warning).
- `POST /link`: attach uuid (+ optional contact) to existing mailbox.
- Lookups: `404` includes `activate_required: true`.
- Freemail domain as mailbox → `freemail_blocked` in validate + activate.
- Docs: registration preplan, opencloud-registration-integration, runbook, CHANGELOG.
- Relies on #13 unique uuid / contact indexes (already UNTESTED).
- No hub UI shipped (opencloud #24/#25 + mail #14).

## Testing instructions

1. Rebuild and health-check provision API:
   ```bash
   cd /opt/km0-mail
   docker compose up -d --build mail-provision-api
   curl -sS http://127.0.0.1:8092/health
   ```
2. Load token (`set -a; source .env; set +a`) and exercise activate flow:
   ```bash
   UUID="test10-$(date +%s)"
   LP="t10$(date +%s | tail -c 5)"
   # Missing mailbox → activate_required
   curl -sS -H "Authorization: Bearer $MAIL_PROVISION_API_TOKEN" \
     "http://127.0.0.1:8092/lookup/by-uuid/$UUID"
   # Freemail as mailbox rejected
   curl -sS -X POST -H "Authorization: Bearer $MAIL_PROVISION_API_TOKEN" \
     -H 'Content-Type: application/json' \
     -d "{\"email\":\"user@gmail.com\",\"opencloud_uuid\":\"$UUID\",\"contact_email\":\"user@gmail.com\",\"password\":\"TmpPass10!x\",\"send_verification\":false}" \
     http://127.0.0.1:8092/activate
   # Activate foo@km0digital.com
   curl -sS -w '\nHTTP:%{http_code}\n' -X POST \
     -H "Authorization: Bearer $MAIL_PROVISION_API_TOKEN" -H 'Content-Type: application/json' \
     -d "{\"local_part\":\"$LP\",\"opencloud_uuid\":\"$UUID\",\"contact_email\":\"c+$UUID@gmail.com\",\"password\":\"TmpPass10!x\",\"send_verification\":false}" \
     http://127.0.0.1:8092/activate
   # Idempotent + conflict
   curl -sS -w '\nHTTP:%{http_code}\n' -X POST \
     -H "Authorization: Bearer $MAIL_PROVISION_API_TOKEN" -H 'Content-Type: application/json' \
     -d "{\"local_part\":\"$LP\",\"opencloud_uuid\":\"$UUID\",\"contact_email\":\"c+$UUID@gmail.com\",\"password\":\"TmpPass10!x\",\"send_verification\":false}" \
     http://127.0.0.1:8092/activate
   curl -sS -w '\nHTTP:%{http_code}\n' -X POST \
     -H "Authorization: Bearer $MAIL_PROVISION_API_TOKEN" -H 'Content-Type: application/json' \
     -d "{\"local_part\":\"other$LP\",\"opencloud_uuid\":\"$UUID\",\"contact_email\":\"c+$UUID@gmail.com\",\"password\":\"TmpPass10!x\",\"send_verification\":false}" \
     http://127.0.0.1:8092/activate
   ```
3. Password IMAP auth (no OAuth required):
   ```bash
   docker compose exec -T dovecot doveadm auth test "${LP}@km0digital.com" 'TmpPass10!x'
   ```
4. Link path: provision mailbox without uuid, then `POST /link` with uuid + contact_email; expect `status=linked`.
5. Docs sanity:
   ```bash
   grep -n 'Activate Mail\|POST /activate\|Cloud IdP' \
     docs/issue-mail-registration-preplan.md \
     docs/opencloud-registration-integration.md \
     docs/runbook.md docs/CHANGELOG.md
   ```
6. Cleanup test rows:
   ```bash
   docker compose exec -T postgres psql -U mail -d mail -c \
     "DELETE FROM mail_accounts WHERE opencloud_uuid='$UUID' OR email='${LP}@km0digital.com';"
   ```
7. Pass when: activate creates `@km0digital.com` with contact freemail; freemail mailbox blocked; password auth succeeds; docs describe Google=Cloud IdP + LDAP OAuth path. Fail if secrets appear in git or freemail mailboxes are accepted.
