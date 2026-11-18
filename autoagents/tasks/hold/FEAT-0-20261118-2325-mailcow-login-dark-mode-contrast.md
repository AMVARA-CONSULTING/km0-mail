# FEAT-0-20261118-2325-mailcow-login-dark-mode-contrast

## GitHub Issue
- **Number:** 0
- **Title:** Fix Mailcow login dark mode: card + FIDO contrast
- **Labels:** `ui,p1,mailcow,a11y`
- **Created:** 2026-11-19

## Meta
- **Status:** `parked-until-sogo-p0`
- **Priority:** P1
- **Depends on:** FEAT-0-*-sogo-dark-theme-contrast-fix
- **Source:** Sentinel browser audit login page 2026-11-19
- **Sentinel watch:** `mailcow-brand-qa-20261119`
- **Catalog project:** `km0-mail`
- **Host:** `amvara10`

## What's wrong / Why
Login page dark toggle leaves a light card; FIDO2 button is dark-on-dark; footer/helper links low contrast. Half-applied `km0` theme / `0081-custom-mailcow.css`.

## One-sentence diff
Mailcow login is coherent in light and dark: all controls readable, no dark-on-dark buttons.

## Plan (coder)
Fix `config/mailcow-branding/theme/dark.css` + `0081-custom-mailcow.css` for `.login` / FIDO / card surfaces. Toggle both themes and PNG-proof.

## Acceptance Criteria
- [ ] Dark mode: login card and inputs readable (light ink on dark OR dark ink on light card — coherent)
- [ ] FIDO2/WebAuthn button: text contrast OK in both themes
- [ ] "Forgot password" / admin links readable
- [ ] PNG proof for light + dark; FAIL on dark-on-dark
- [ ] Promote from hold only after SOGo P0 CLOSED

## Testing instructions
1. Open https://mail.km0digital.com/ logged out.
2. Toggle dark/light; PNG each.
3. Vision-check FIDO button and labels.

## Status
| Phase | Status |
|-------|--------|
| Created | parked |
