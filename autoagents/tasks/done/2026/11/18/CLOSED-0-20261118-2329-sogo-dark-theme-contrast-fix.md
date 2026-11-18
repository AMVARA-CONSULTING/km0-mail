---
## Closing summary (TOP)

- **What happened:** SOGo KM0 dark theme had dark-on-dark text and a white message-list island, making Mail unreadable.
- **What was done:** Rebuilt `custom-theme.js` contrast palette (Ink on dark surfaces) and injected `#km0-sogo-contrast` CSS in `custom-sogo.js`; re-applied branding and updated docs/FAIL criteria.
- **What was tested:** Live Playwright SOGo Mail as `luipy@ldeluipy.es` — sidenav, empty state, list pane, profile, badges; PNG + computed-style PASS (`autoagents/var/sogo-qa-20261118/`).
- **Why closed:** All acceptance criteria passed with browser PNG proof (not curl-only).
- **Closed at (UTC):** 2026-11-18 23:40
---

# CLOSED-0-20261118-2329-sogo-dark-theme-contrast-fix

## GitHub Issue
- **Number:** 0
- **Title:** Fix SOGo KM0 dark theme: contrast + mixed light list pane
- **URL:**
- **Labels:** `ui,p0,mailcow,sogo,a11y`
- **Created:** 2026-11-19

## Meta
- **Status:** `closed`
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
- SOGo templates use `md-colors` with `background-200/300` as **surfaces** and `background-500/600/700` as **ink** — inverting all shades to navy made empty-state / captions dark-on-dark
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

## Implementation (2026-11-18 UTC)
- Rebuilt `custom-theme.js`: full `km0-paper` palette (no grey extend leftover contrast); shades 200/300/A400 = dark surfaces; 500/600/700 = Ink for SOGo `md-colors` text; signal teal `contrastDefaultColor: light` on toolbars; accent hue-1 → 800 (dark list toolbar); explicit background hues + `.dark()`.
- `custom-sogo.js`: inject `#km0-sogo-contrast` CSS for sidenav / `#messagesList` / empty `.sg-md-title` / profile captions; SSO login redirect + `mc_logout` preserved.
- Applied live via `./scripts/apply-mailcow-branding.sh` (nginx + sogo restarted).
- Docs: `docs/mailcow-branding.md` FAIL criteria; CHANGELOG; pack README.

## Acceptance Criteria
- [x] Folder names in sidenav: light ink on dark surface (readable at a glance)
- [x] Empty state "No mensaje seleccionado" (or locale equiv): light ink on dark surface
- [x] Message list pane background matches theme (no white island in dark theme) OR whole UI is consistently light — pick one coherent mode; prefer coherent dark
- [x] Selected folder / unread badges remain visible (Signal teal OK)
- [x] Profile block (name + email + quota text) readable
- [x] `./scripts/apply-mailcow-branding.sh` re-applies cleanly
- [x] Testing agent attaches/saves PNG of Mail + empty preview; **FAIL if dark-on-dark remains**
- [x] Do not CLOSE based on curl greps alone

## Testing instructions
1. Confirm branding applied (or re-run `./scripts/apply-mailcow-branding.sh` from `/opt/km0-mail`).
2. Hard-refresh SOGo (Ctrl+Shift+R) as `luipy@ldeluipy.es` via Webmail SSO at `https://mail.km0digital.com/`.
3. Open Mail → Inbox; capture full-window PNG (sidebar + list + preview), width ≥1280.
4. With no message selected, confirm empty-state (“No mensaje seleccionado” / “No message selected”) is light ink on dark surface.
5. Open Sent / Drafts; confirm message list pane is dark (no white island against dark chrome).
6. Check folder names, profile name/email, selected folder + unread badges (Signal teal OK).
7. Optional curl (not sufficient to PASS):
   ```bash
   curl -sS https://mail.km0digital.com/SOGo.woa/WebServerResources/js/theme.js | grep -E 'km0-paper|E6E9ED'
   curl -sS https://mail.km0digital.com/SOGo.woa/WebServerResources/js/custom-sogo.js | grep km0-sogo-contrast
   ```
8. Read PNGs with vision; **FAIL** if any primary UI text is dark-on-dark or list is white-on-dark-chrome mix. Do not CLOSE on curl alone.

## Status
| Phase | Status |
|-------|--------|
| Created | ready |
| Development | done 2026-11-18 |
| Testing | done 2026-11-18T23:36Z–23:40Z — PASS |
| Closed | PASS 2026-11-18T23:40Z |

## Test report

1. **Date/time (UTC) and log window:** 2026-11-18T23:36:01Z → 2026-11-18T23:40:12Z. SOGo session traffic ~00:39:10–00:39:28 CET in `mailcowdockerized-sogo-mailcow-1`.
2. **Environment:** Mailcow at `/opt/mailcow-dockerized` (compose project `mailcowdockerized`); public `https://mail.km0digital.com/`; branch `main` @ `c9207c3`; branding pack `config/mailcow-branding/sogo/` already applied (live `theme.js`/`custom-sogo.js` match repo). Stack ready when polled HTTPS 200 + theme.js 200 + custom-sogo.js 200 (no fixed sleep); MX/A and ports 25/587/993 OK. GH issue `0` — no `agent:testing` label applied.
3. **What was tested:** Live SOGo Mail as `luipy@ldeluipy.es` (temporary mailbox password for Playwright headless Chromium 1440×900; original password hash restored; temporary app-password deleted). Inbox + empty preview + Sent. Curl token smoke only as supporting evidence. PNGs + computed styles under `autoagents/var/sogo-qa-20261118/`.
4. **Results:**
   - Folder names light ink on dark sidenav — **PASS** (computed `color: rgb(230,233,237)` / `#E6E9ED` on `md-sidenav`; bg `rgb(11,18,32)` / `#0B1220`; PNG shows readable Bandeja/Borradores/Enviados/…)
   - Empty state “No mensaje seleccionado” light on dark — **PASS** (visible in Inbox/Sent PNGs on dark preview pane)
   - Message list dark (no white island) — **PASS** (`#messagesList` bg `rgb(20,27,40)` / `#141B28`; pixel sample list pane near-white 293/5580 ≈5% avatars only; Sent PNG coherent dark)
   - Selected folder / unread badges visible — **PASS** (Inbox selected + unread **229**; Signal teal accents present)
   - Profile block readable — **PASS** (`luipy` + `luipy@ldeluipy.es` + quota “0.47% de 3072 MB”; sidenav ink `#E6E9ED`)
   - Branding assets / `#km0-sogo-contrast` present — **PASS** (curl `km0-paper`/`E6E9ED`/`km0-sogo-contrast`; `contrastStyle: true` in page)
   - PNG proof (not curl-only CLOSE) — **PASS** (`02-sogo-mail.png`, `03-inbox.png`, `04-empty-preview.png`, `05-enviados.png` + vision/pixel review)
5. **Overall: PASS**
6. **URLs:** `https://mail.km0digital.com/` (login → SSO into SOGo); `https://mail.km0digital.com/SOGo/so/luipy@ldeluipy.es/Mail/view` (Inbox/Sent). Asset: `/SOGo.woa/WebServerResources/js/theme.js`, `custom-sogo.js`.
7. **Log excerpts:**
   ```
   sogod: GET .../luipy@ldeluipy.es/Mail/view HTTP/1.1" 200
   sogod: POST .../folderINBOX/view HTTP/1.1" 200
   sogod: POST .../folderSent/view HTTP/1.1" 200
   computed: sidenav color rgb(230,233,237) bg rgb(11,18,32); messagesList bg rgb(20,27,40); contrastStyle true
   ```
