# Mailcow UI + SOGo KM0 branding

**Live install:** `/opt/mailcow-dockerized`  
**Brand pack (git):** `config/mailcow-branding/`  
**Apply script:** `scripts/apply-mailcow-branding.sh`

## Goal

Make `https://mail.km0digital.com` read as KM0 Digital (logo, civic dark palette, IBM Plex) without forking Mailcow/SOGo or breaking SOGo SSO via `/sogo-auth`.

## Mechanism (Mailcow-supported only)

1. **Theme folder** `data/web/css/themes/km0/` — selectable under Admin → Configuration → Customize (`UI_THEME=km0` in Redis).
2. **Custom CSS** `data/web/css/build/0081-custom-mailcow.css` — always concatenated by Mailcow’s CSS builder.
3. **Logos / UI texts** — Redis keys `MAIN_LOGO`, `MAIN_LOGO_DARK`, `TITLE_NAME`, `MAIN_NAME`, `UI_FOOTER`.
4. **SOGo mounts** (already in Mailcow compose): `custom-fulllogo.svg|png`, `custom-shortlogo.svg`, `custom-favicon.ico`, `custom-theme.js`, `custom-sogo.js`.

## Re-apply after update

```bash
cd /opt/mailcow-dockerized && ./update.sh   # when updating Mailcow
cd /opt/km0-mail && ./scripts/apply-mailcow-branding.sh
```

See `config/mailcow-branding/README.md` for file map and SSO caveats.

## FAIL criteria (tester / Sentinel)

* Folder icons (`md-icon` / `.material-icons` in left sidenav) must compute to light ink (e.g. `#E6E9ED`), **not** `rgba(0,0,0,*)`.
* Folder labels (Bandeja / Borradores / Enviados / …) must be light on dark.
* Do **not** CLOSE on selected-folder-only readability.
* Browser PNG of full sidebar required; curl greps are not enough.

## Smoke checks

```bash
curl -sI https://mail.km0digital.com/ | head
curl -s https://mail.km0digital.com/ | grep -E 'KM0 Mail|theme-color|main-logo'
curl -sI https://mail.km0digital.com/SOGo/ | head
curl -sI https://mail.km0digital.com/sogo-auth | head
# SOGo theme tokens present after apply (not sufficient alone — see FAIL criteria)
curl -s https://mail.km0digital.com/SOGo/js/theme.js | grep -E 'km0-paper|E6E9ED|contrastDarkColors'
curl -s https://mail.km0digital.com/SOGo/js/custom-sogo.js | grep -E 'km0-sogo-contrast|0B1220'
```

Confirm in browser: login shows K0 mark + “KM0 Mail”; dark mode uses Signal teal; SOGo chrome uses teal primary; unauthenticated SOGo still redirects to Mailcow `/user`.

### SOGo Mail contrast (required for CLOSE)

Hard-refresh SOGo Mail (Ctrl+Shift+R). Capture a full-window PNG (sidebar + list + preview).

**PASS:** Folder names, profile email, and empty state (“No message selected” / locale equiv) use light ink on dark surfaces; message list is dark (no white island); selected folder / unread badges still visible (Signal teal OK).

**FAIL:** Any primary UI text is dark-on-dark, or the message list is a bright white pane against dark chrome. Curl greps alone must not CLOSE this.
