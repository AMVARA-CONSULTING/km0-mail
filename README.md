# km0-mail

Self-hosted mail stack for **KM0 Digital** — Postfix, Dovecot, Rspamd, Roundcube, and PostgreSQL on the same Debian VPS as OpenCloud.

**Service hostname:** `mail.km0digital.com` · **User addresses:** `@km0digital.com`

> Operations and architecture: [`docs/issue-mail-preplan.md`](docs/issue-mail-preplan.md) · Agent workflow: [`docs/agent-loop.md`](docs/agent-loop.md)

---

## Status

**Phase 1 implementation in repo.** Docker Compose, configs, Nginx template, SQL schema, and ops scripts are ready for operator deploy on the VPS. DNS, TLS, UFW, and mailbox provisioning are documented in [`docs/runbook.md`](docs/runbook.md).

```bash
cp .env.example .env && chmod 600 .env
docker compose up -d
./scripts/verify-mail-stack.sh
```

---

## Repository layout

```
/opt/km0-mail/
├── docker-compose.yml   # Postfix, Dovecot, Rspamd, Roundcube, PostgreSQL
├── config/              # postfix, dovecot, rspamd, roundcube, fail2ban
├── nginx/               # Host vhost template (mail.km0digital.com)
├── sql/init/            # PostgreSQL schema bootstrap
├── scripts/             # km0-mail-admin, backup, verify, git-sync
├── autoagents/          # Cursor agent loop (GitHub Issues → FEAT tasks)
└── docs/
    ├── issue-mail-preplan.md
    ├── runbook.md
    └── agent-loop.md
```

Related repos:

| Repo | Role |
|------|------|
| [km0-opencloud](https://github.com/AMVARA-CONSULTING/km0-opencloud) | OpenCloud + Dex (`cloud.km0digital.com`) |
| [km0-web](https://github.com/AMVARA-CONSULTING/km0-web) | Corporate site (`km0digital.com`) |

---

## Quick start (autoagents)

```bash
git clone git@github.com:AMVARA-CONSULTING/km0-mail.git /opt/km0-mail
cd /opt/km0-mail
./scripts/setup-git-author.sh          # Luipy56 <yoelberjaga@gmail.com> (repo-local)
cp autoagents/.env.example autoagents/.env   # GH_TOKEN, optional Redmine #7605
./scripts/setup-autoagents-gh.sh
./autoagents/autoagents-loop.sh 001
```

---

## License

Deployment configuration in this repository is [MIT](LICENSE).
