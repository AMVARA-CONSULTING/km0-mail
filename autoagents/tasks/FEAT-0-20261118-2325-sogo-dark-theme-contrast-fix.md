# FEAT-0-20261118-2325-sogo-dark-theme-contrast-fix

## GitHub Issue
- **Number:** 0
- **Title:** Fix SOGo KM0 dark theme: contrast + mixed light list pane
- **URL:**
- **Labels:** `ui,p0,mailcow,sogo,a11y`
- **Created:** 2026-11-19

## Meta
- **Status:** `ready-for-dev`
- **Generated:** 2026-11-19T00:22Z
- **Priority:** P0
- **Assigned Agent:** `010 → 020 → 030 → 040`
- **Depends on:** none (supersedes premature CLOSED branding pack QA)
- **Source:** Human (2026-11-19) — dark-on-dark SOGo + half dark mode; Sentinel browser audit
- **Human refs:** Discord screenshot attachment; Maestro Sentinel chrome audit 2026-11-19
- **Version at dump:** `1.0.5927`
- **Sentinel watch:** `mailcow-brand-qa-20261119`
- **Catalog project:** `km0-mail`
- **Host:** `amvara10`

## Research
- Angular Material theming: background palette + `contrastDefaultColor` / `contrastDarkColors` must yield light ink on dark surfaces — https://material.angularjs.org/latest/Theming/03_configuring_a_theme
- Mailcow SOGo customize mounts: `data/conf/sogo/custom-theme.js` + `custom-sogo.js` (re-apply via `scripts/apply-mailcow-branding.sh`)
- Local pack: `config/mailcow-branding/sogo/custom-theme.js` — current `.dark()` + grey extend leaves folder labels / empty-state as ~rgba(0,0,0,.87) on navy; list pane stays white
- Prior CLOSED task must not be treated as done until AC below pass

## What's wrong / Why
Operator screenshot + Sentinel browser: SOGo shows dark chrome with **unreadable dark text** (folders, "No mensaje seleccionado", profile email) and a **bright white message list** (mixed theme). Stock Material contrast tokens were not verified in a real browser before CLOSE.

## One-sentence diff
SOGo Mail views are fully readable dark (or fully readable light) with WCAG-ish contrast; no dark-on-dark and no white list island.

## Plan (coder)
**Root cause / approach:** Fix `custom-theme.js` palette contrast (Ink on Paper/Snow) and add CSS overrides in `custom-sogo.js` / a small CSS inject for mailbox list + empty state + sidenav links. Re-run apply script. Do not mark done without PNG proof.
**Files (likely):**
- `config/mailcow-branding/sogo/custom-theme.js`
- `config/mailcow-branding/sogo/custom-sogo.js`
- `scripts/apply-mailcow-branding.sh`
- `docs/mailcow-branding.md` (update smoke + FAIL criteria)
**Out of scope:** Keycloak; Mailcow login dark toggle (separate FEAT); changing mail routing

## Acceptance Criteria
- [ ] Folder names in sidenav: light ink on dark surface (readable at a glance)
- [ ] Empty state "No mensaje seleccionado" (or locale equiv): light ink on dark surface
- [ ] Message list pane background matches theme (no white island in dark theme) OR whole UI is consistently light — pick one coherent mode; prefer coherent dark
- [ ] Selected folder / unread badges remain visible (Signal teal OK)
- [ ] Profile block (name + email + quota text) readable
- [ ] `./scripts/apply-mailcow-branding.sh` re-applies cleanly
- [ ] Testing agent attaches/saves PNG of Mail + empty preview; **FAIL if dark-on-dark remains**
- [ ] Do not CLOSE based on curl greps alone

## Testing instructions
1. Apply branding; hard-refresh SOGo (Ctrl+Shift+R) as `luipy@ldeluipy.es` via Webmail SSO.
2. Open Mail → Inbox; capture full-window PNG (sidebar + list + preview).
3. With no message selected, confirm empty-state contrast.
4. Open Sent / Drafts; confirm list pane not a white clash if dark theme.
5. Read PNGs with vision; **FAIL** if any primary UI text is dark-on-dark or list is white-on-dark-chrome mix.
6. Platforms: desktop Chrome width ≥1280.

## Status
| Phase | Status |
|-------|--------|
| Created | ready |
| Development | |
| Testing | |
| Closed | |
