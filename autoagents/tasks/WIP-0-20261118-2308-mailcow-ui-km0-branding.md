# Mailcow UI + SOGo: apply KM0 brand design

## GitHub Issue
- **Issue:** (create if needed; track under mail hub)
- **Number:** #0
- **Redmine:** #8480 / hub #7605

## Problem / goal
Mail.km0digital.com now runs **Mailcow + SOGo** (legacy Roundcube stopped). The UI still looks stock Mailcow. Align login, Mailcow UI chrome, and SOGo shell with **KM0 Digital** brand (logo, colours, typography) without breaking SSO or upgrades.

## High-level instructions for coder
- Source of brand truth: km0-web / existing Roundcube plugin @config/roundcube/plugins/km0_theme@ (colours, logo assets) and public site brand tokens where helpful.
- Prefer Mailcow-supported customize paths (Admin → Configuration → Customize / custom CSS & logos under Mailcow data dirs). Do **not** fork SOGo/Mailcow core if a customize hook exists.
- Keep @mail.km0digital.com@ hostname; do not change ports or reverse-proxy contract (host nginx → :8880).
- Preserve SOGo SSO via @/sogo-auth@.
- Document how to re-apply after @./update.sh@ / image pull.
- Reference @docs/mailcow-cutover-status.md@ and @docs/runbook.md@.
- English for commits/docs; no secrets in git.

## Out of scope
- Keycloak IdP attach (Phase 4 — paused)
- Deleting km0-mail volumes
- Functional mail routing changes

## Testing instructions
(to be filled by coder before UNTESTED-)
