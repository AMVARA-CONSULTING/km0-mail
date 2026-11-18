# Mailcow / SOGo KM0 branding pack

Source of truth for **KM0 Digital** look on `mail.km0digital.com` (Mailcow UI + SOGo).

Brand tokens match Roundcube `skins/km0` and km0-web: Paper / Snow / Mist / Ink / Signal, IBM Plex Sans, K0 lettermark.

## What this pack contains

| Path | Applied to |
|------|------------|
| `theme/` | `/opt/mailcow-dockerized/data/web/css/themes/km0/` (`dark.css` = login + UI dark contrast) |
| `0081-custom-mailcow.css` | `…/data/web/css/build/0081-custom-mailcow.css` (always-on; login dark safety net via `html:has(#dark-mode-theme)`) |
| `assets/logo*.svg` | Redis `MAIN_LOGO` / `MAIN_LOGO_DARK` + SOGo logo mounts |
| `sogo/custom-theme.js` | SOGo Material dark palette (ink on 500/600/700; surfaces on 200/300/A400) |
| `sogo/custom-sogo.js` | **Must keep** Mailcow SSO login redirect + `mc_logout`; also injects `#km0-sogo-contrast` CSS |

## Apply / re-apply

From `/opt/km0-mail`:

```bash
./scripts/apply-mailcow-branding.sh
```

Sets Redis UI texts (`KM0 Mail`), selects theme `km0`, copies logos/CSS/JS, restarts `nginx-mailcow` and `sogo-mailcow`.

## After `./update.sh`

Mailcow updates can overwrite `data/web` files that came from git, and SOGo image layers. Redis keys usually survive.

1. Finish Mailcow `./update.sh` as usual.
2. Re-run `./scripts/apply-mailcow-branding.sh` from this repo.
3. Spot-check login, SOGo (`/SOGo/`), and `/sogo-auth` SSO.

Optional: add a Mailcow `pre_update_hook.sh` / post-update note that calls this script.

## Do not

- Fork SOGo or Mailcow PHP core for cosmetics.
- Change host nginx → `:8880` contract or ports.
- Remove the SOGo → `/user` login redirect in `custom-sogo.js`.
