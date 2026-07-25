# Agent pipeline: mail SSO / activate (Google & OIDC)

> **Purpose:** Ordered blocker list so feature-coders do not race spike/hub work ahead of identity + wizard foundations.  
> **Tracking:** km0-mail [#16](https://github.com/AMVARA-CONSULTING/km0-mail/issues/16) · Redmine #7605  
> **Related pre-plans:** [issue-mail-preplan.md](./issue-mail-preplan.md), [issue-mail-registration-preplan.md](./issue-mail-registration-preplan.md)

## Product rule (identity)

- Cloud IdP for Google/OIDC users remains **Google (or Apple, etc.)** — freemail is `contact_email`, not the mailbox.
- Mailbox is always `foo@km0digital.com` (or future custom domain), linked via `mail_accounts.opencloud_uuid`.
- Roundcube **OAuth login** uses **Dex LDAP** so the token `email` claim equals the mailbox (Dovecot `username_attribute=email`). Do not rely on freemail→mailbox remap in `oauth_login` alone.
- Password Roundcube login works independently of OAuth once the mailbox exists.

## Required order

Do **not** start a later step until earlier foundations have a clear path (merged or UNTESTED with a viable approach). Issue numbers:

| Step | Repo | Issue | Topic | Agent note |
|------|------|-------|--------|------------|
| 1 | km0-mail | [#8](https://github.com/AMVARA-CONSULTING/km0-mail/issues/8) | Roundcube login i18n path (doubled skins) | Close when tester passes (UNTESTED) |
| 2 | km0-mail | [#9](https://github.com/AMVARA-CONSULTING/km0-mail/issues/9) | Dovecot OAuth2 / IMAP XOAUTH2 for Roundcube Dex LDAP | Soft-blocks silent OAuth entry; password path can proceed |
| 3 | km0-opencloud | [#24](https://github.com/AMVARA-CONSULTING/km0-opencloud/issues/24) | Preserve Google OIDC identity after Graph mail rewrite | **Hard-blocks** prod activate CTA |
| 4 | km0-opencloud | [#25](https://github.com/AMVARA-CONSULTING/km0-opencloud/issues/25) | Cloud-origin activate-mail wizard + hub deep-link | Wizard URL required by hub CTA |
| 5 | km0-mail | [#13](https://github.com/AMVARA-CONSULTING/km0-mail/issues/13) | UNIQUE `opencloud_uuid` + `contact_email` index | Before prod activate; aligns with register-api |
| 6 | km0-mail | [#14](https://github.com/AMVARA-CONSULTING/km0-mail/issues/14) (supersedes [#11](https://github.com/AMVARA-CONSULTING/km0-mail/issues/11)) | Hub `sso=all` cookie, Google-safe `sso-continue`, activate CTA | Cross-repo: `/opt/km0-auth/host-www/` |
| 7 | km0-mail | [#15](https://github.com/AMVARA-CONSULTING/km0-mail/issues/15) | Post-activate verify path (password → inbox → LDAP OAuth) | After wizard + password login |
| 8 | km0-opencloud | [#26](https://github.com/AMVARA-CONSULTING/km0-opencloud/issues/26) | Apple (and future OIDC) parity | After Google path is stable |
| 9 | km0-mail | [#12](https://github.com/AMVARA-CONSULTING/km0-mail/issues/12) | SPIKE: Google IdP directly into Roundcube | **Done — wontfix** ([design](./spike-google-idp-roundcube-mailbox-map.md)); must not block 1–8 |

### Parallel / supporting work (do not reorder foundations)

| Repo | Issue | Role |
|------|-------|------|
| km0-mail | [#10](https://github.com/AMVARA-CONSULTING/km0-mail/issues/10) | Activate/link APIs on `mail-provision-api` (uuid + contact_email); can progress with #13 |
| km0-opencloud | [#23](https://github.com/AMVARA-CONSULTING/km0-opencloud/issues/23) | register-api activate-mail for existing users; coordinates with #10 / #13 |
| km0-opencloud | [#22](https://github.com/AMVARA-CONSULTING/km0-opencloud/issues/22) | Session gate honors `service=mail` → sso-continue (do not revert) |

## Explicit blockers for agents

- **[#12](https://github.com/AMVARA-CONSULTING/km0-mail/issues/12)** decided **wontfix** — see [`spike-google-idp-roundcube-mailbox-map.md`](./spike-google-idp-roundcube-mailbox-map.md). Do not re-open Google→Roundcube without a new product mandate.
- **Do not double-implement [#11](https://github.com/AMVARA-CONSULTING/km0-mail/issues/11)** — implement hub goals under [#14](https://github.com/AMVARA-CONSULTING/km0-mail/issues/14); leave #11 with a pointer comment only.
- **[#14](https://github.com/AMVARA-CONSULTING/km0-mail/issues/14)** waits on opencloud #24 + #25 for identity + wizard URL; soft-block #9 for silent OAuth.
- **[#10](https://github.com/AMVARA-CONSULTING/km0-mail/issues/10)** must not ship activate UX that strands Google users (coordinate opencloud #24).
- **Agent 001 dedupe:** do not recreate `FEAT-<N>` when `WIP|UNTESTED|TESTING|CLOSED-<N>-*` already exists in `autoagents/tasks/`, or when the issue already has `agent:planned|wip|untested|testing`. Enforced in `autoagents/issue_checker_agent.py`.

## Hub / auth surfaces

Hub scripts live in **`/opt/km0-auth/host-www/`** (no autoagents loop). Mail FEATs that edit hub files must add a sibling `NEW-` under `/opt/km0-auth/tasks/` and deploy via km0-auth deploy scripts when that is the host pattern.

## Loop reference

General autoagents roles and labels: [agent-loop.md](./agent-loop.md).
