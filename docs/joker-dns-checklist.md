# DNS records to add at Joker.com for km0digital.com mail
#
# Operator checklist — update this file after running ./scripts/setup-dkim.sh
# if the DKIM public key changes.
#
# Server IP: 116.202.10.106
# Mail hostname: mail.km0digital.com

## Required for inbound mail from the Internet

| Type | Host / name | Value | Priority |
|------|-------------|-------|----------|
| **MX** | `@` (apex km0digital.com) | `mail.km0digital.com` | **10** |
| **A** | `mail` | `116.202.10.106` | — |

> You added the **A** record for `mail` — good. **MX on the apex is still missing** (verify script showed WARN). Without MX, Gmail/Outlook do not know where to deliver `@km0digital.com` mail.

## Required for outbound deliverability

| Type | Host | Value |
|------|------|-------|
| **TXT (SPF)** | `@` | `v=spf1 mx a:mail.km0digital.com -all` |
| **TXT (DKIM)** | `mail._domainkey` | See `./scripts/setup-dkim.sh` output (run on server after deploy) |
| **TXT (DMARC)** | `_dmarc` | `v=DMARC1; p=none; rua=mailto:postmaster@km0digital.com; adkim=s; aspf=s` |

### Current DKIM TXT (generated 2026-06-14)

Host: `mail._domainkey`

```
v=DKIM1; k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCafaJphyrHAzByV1rr23wZooe9DAUrgRr4cXHeMKQV6ovDTXEaru4spj3fx9Tw8x5gBHYiEMbyz1jI57zIDgVk13bFYi/y0o93gnN7cy3orh00Rs1JFLoSM2xhu5/j/xqU2I2H+4XXwpDhFud002l5sd/d+SHOdbBtXbeilf5xIwIDAQAB
```

(Joker: paste only the value inside quotes, or the full TXT string without parentheses.)

## Hetzner (not Joker) — reverse DNS (PTR)

In Hetzner Cloud/Robot, set **PTR** for `116.202.10.106` → **`mail.km0digital.com`**

Current PTR is wrong: `static.106.10.202.116.clients.your-server.de`

Without correct PTR, many providers spam-folder or reject outbound mail.

## Verify after DNS propagates (5–60 min)

```bash
dig +short km0digital.com MX
dig +short mail.km0digital.com A
dig +short km0digital.com TXT
dig +short mail._domainkey.km0digital.com TXT
dig +short _dmarc.km0digital.com TXT
dig +short -x 116.202.10.106
```

Expected MX: `10 mail.km0digital.com.`

## Webmail URL (after server Nginx + cert)

https://mail.km0digital.com/

Login: `user@km0digital.com` + password from `./scripts/km0-mail-admin create-mailbox`
