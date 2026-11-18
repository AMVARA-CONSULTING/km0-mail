---
## Closing summary (TOP)

- **What happened:** Mailcow login dark mode left low-contrast chrome (FIDO snow-on-snow, Bootstrap `#555` text-secondary, weak helper links) after a half-applied km0 theme.
- **What was done:** Updated `theme/dark.css` and `0081-custom-mailcow.css` with login card/FIDO/text-secondary tokens plus an `html:has(#dark-mode-theme)` safety net; branding applied live.
- **What was tested:** Tester PASS on live `mail.km0digital.com` — light/dark PNGs, FIDO Mist contrast 10.42, inputs 15.37, text-secondary 14.17, Forgot/admin Signal links readable; branding CSS tokens present.
- **Why closed:** All acceptance criteria passed after SOGo P0 dependency was CLOSED.
- **Closed at (UTC):** 2026-11-18 23:55

---

# WIP-0-20261118-2347-mailcow-login-dark-mode-contrast

## GitHub Issue
- **Number:** 0
- **Title:** Fix Mailcow login dark mode: card + FIDO contrast
- **Labels:** `ui,p1,mailcow,a11y`
- **Created:** 2026-11-19

## Meta
- **Status:** `closed`
- **Priority:** P1
- **Depends on:** CLOSED-0-*-sogo-dark-theme-contrast-fix (done)
- **Source:** Sentinel browser audit login page 2026-11-19
- **Sentinel watch:** `mailcow-brand-qa-20261119`
- **Catalog project:** `km0-mail`
- **Host:** `amvara10`
- **Assigned Agent:** tester

## What's wrong / Why
Login page dark toggle leaves a light card; FIDO2 button is dark-on-dark; footer/helper links low contrast. Half-applied `km0` theme / `0081-custom-mailcow.css`.

## One-sentence diff
Mailcow login is coherent in light and dark: all controls readable, no dark-on-dark buttons.

## Plan (coder)
Fix `config/mailcow-branding/theme/dark.css` + `0081-custom-mailcow.css` for `.login` / FIDO / card surfaces. Toggle both themes and PNG-proof.

## Implementation (2026-11-18 UTC)
- Promoted after SOGo P0 CLOSED (`done/2026/11/18/CLOSED-0-20261118-2329-sogo-dark-theme-contrast-fix.md`).
- Root cause (live Playwright): dark card/inputs were mostly OK after km0 theme, but (1) `.text-secondary` (lang control) stayed Bootstrap `#555` on dark card; (2) `#fido2-login` used Snow-on-Snow (button blended into card); (3) no always-on safety net if theme dark.css half-applied.
- `theme/dark.css`: login card surfaces + `--bs-card-*` / `--bs-secondary-*`; FIDO/mist secondary buttons; `.text-secondary` → ink-muted; helper links Signal teal.
- `0081-custom-mailcow.css`: `html:has(#dark-mode-theme)` login safety net mirroring the same tokens.
- Applied live via `./scripts/apply-mailcow-branding.sh`; docs FAIL criteria + CHANGELOG.
- Coder PNG + computed styles: `autoagents/var/login-qa-20261118/` (light/dark; FIDO bg Mist `#2A3344`, text-secondary ink-muted).

## Acceptance Criteria
- [x] Dark mode: login card and inputs readable (light ink on dark OR dark ink on light card — coherent)
- [x] FIDO2/WebAuthn button: text contrast OK in both themes
- [x] "Forgot password" / admin links readable
- [x] PNG proof for light + dark; FAIL on dark-on-dark *(coder evidence; tester must re-verify)*
- [x] Promote from hold only after SOGo P0 CLOSED

## Testing instructions
1. Confirm branding applied (or re-run `./scripts/apply-mailcow-branding.sh` from `/opt/km0-mail`).
2. Open https://mail.km0digital.com/ logged out; hard-refresh (Ctrl+Shift+R).
3. **Light:** capture full-window PNG of login card (width ≥1280). Confirm dark ink on light card; FIDO2 button readable; Forgot/admin links Signal teal.
4. Toggle dark mode (moon switch). **Dark:** capture PNG. Confirm:
   - Login card is dark Snow (not a white island on dark body).
   - Inputs: light ink / placeholders on dark fields.
   - FIDO2 button: light ink on Mist surface (distinct from card); icon readable — **FAIL if dark-on-dark**.
   - Lang / moon `.text-secondary` chrome is light muted ink (not Bootstrap `#555`).
   - “Forgot password”, “Log in as admin”, domain-admin links readable (Signal teal OK).
5. Optional: clear `localStorage.mailcow_theme` and load with OS dark preference; same dark AC.
6. Optional curl (not sufficient to PASS):
   ```bash
   curl -sS https://mail.km0digital.com/ | grep -E 'KM0 Mail|mailcow_dark_css'
   # dark bundle should mention fido2-login / login-card after apply
   DARK=$(curl -sS https://mail.km0digital.com/ | grep -oP "mailcow_dark_css = '\K[^']+")
   curl -sS "https://mail.km0digital.com$DARK" | grep -E 'fido2-login|text-secondary|141B28'
   curl -sS https://mail.km0digital.com/cache/$(curl -sS https://mail.km0digital.com/ | grep -oP 'href="/cache/\K[^"]+\.css' | head -1) | grep 'html:has(#dark-mode-theme)'
   ```
7. Evidence dir from coder (re-shot OK): `autoagents/var/login-qa-20261118/` (`05-after-fix-dark.png`, `06-after-fix-light.png`, `computed-dark.json`).

## Status
| Phase | Status |
|-------|--------|
| Created | parked |
| Dependency | SOGo P0 CLOSED |
| Implementation | done |
| Ready for tester | yes |
| Testing | PASS |
| Closed | 2026-11-18T23:54:01Z |

## Test report

1. **Date/time (UTC) and log window:** Start `2026-11-18T23:52:41Z` → end `2026-11-18T23:54:01Z`. Evidence gathered in that window against live `mail.km0digital.com`.
2. **Environment:** Branch `main` (`3cc9e93`). Mailcow compose project `mailcowdockerized-*` (nginx Up ~2m at test time; php-fpm/postfix/dovecot/rspamd Up). URL `https://mail.km0digital.com/`. Repo `/opt/km0-mail`. GitHub issue `#0` — no real issue; `agent:testing` label N/A.
3. **What was tested:** Login light/dark contrast ACs (card, inputs, FIDO2, `.text-secondary` chrome, Forgot/admin links); branding CSS presence (`mailcow_dark_css`, `html:has(#dark-mode-theme)`, `#fido2-login` / `#141B28` tokens); Playwright re-shot + computed styles; infra readiness (HTTP 200, MX/A, ports 25/587/993).
4. **Results:**
   - **Stack ready:** **PASS** — `curl -sI https://mail.km0digital.com/` → HTTP/2 200; MX `mail.km0digital.com.`; A `116.202.10.106`; `nc` 25/587/993 succeeded. Knew ready via HTTP 200 + open mail ports + `mailcowdockerized-nginx-mailcow-1` Up (not a fixed sleep).
   - **Branding applied:** **PASS** — HTML title `KM0 Mail`; dark bundle contains `#fido2-login`, `#141B28` (Snow), `#2A3344` (Mist); custom cache CSS contains `html:has(#dark-mode-theme)` safety net.
   - **Light: card/inputs/FIDO readable:** **PASS** — card `rgb(255,255,255)` / ink `rgb(11,18,32)`; FIDO ink on Mist-adjacent light surface contrast **17.28**. PNG: `autoagents/var/login-qa-tester-20261118/tester-light.png`.
   - **Dark: card Snow (not white island):** **PASS** — card bg `rgb(20, 27, 40)` (= `#141B28`); body Paper `rgb(11, 18, 32)`.
   - **Dark: inputs light ink on dark fields:** **PASS** — `#login_user` color `rgb(230,233,237)` on `rgb(11,18,32)`, contrast **15.37**.
   - **Dark: FIDO light ink on Mist (not dark-on-dark):** **PASS** — `#fido2-login` color `rgb(230,233,237)` on `rgb(42,51,68)` Mist, contrast **10.42**; icon inherits ink. Distinct from card Snow.
   - **Dark: `.text-secondary` / moon chrome muted ink (not `#555`):** **PASS** — `rgba(230, 233, 237, 0.65)` on card Snow, contrast **14.17**.
   - **Forgot / admin links readable:** **PASS** — dark: Signal `rgb(45,212,191)` (Forgot contrast **9.27**, admin **10.06**); light: plaque teal `rgb(15,118,110)` still readable on white card.
   - **PNG proof light + dark:** **PASS** — tester re-shot `tester-light.png` / `tester-dark.png` + JSON; coder artifacts still present under `autoagents/var/login-qa-20261118/`.
5. **Overall:** **PASS**
6. **URLs tested:** `https://mail.km0digital.com/`; dark CSS `/cache/593042e89d6bc1069649d630304333b214f6a2aa-5878a134ba5ada11ac935d479bbb1f31ddd25668.css`; custom `/cache/593042e89d6bc1069649d630304333b214f6a2aa.css`.
7. **Log excerpts:** nginx access during window: `GET /` 200, dark/custom CSS 200; no nginx errors related to branding. Playwright: `ASSERT_PASS` (see `tester-computed-dark.json`).
