# km0-mail

Self-hosted mail stack for **KM0 Digital** — Postfix, Dovecot, Rspamd, Roundcube, and PostgreSQL on the same Debian VPS as OpenCloud.

**Service hostname:** `mail.km0digital.com` · **User addresses:** `@km0digital.com`

> Operations and architecture: [`docs/issue-mail-preplan.md`](docs/issue-mail-preplan.md) · Agent workflow: [`docs/agent-loop.md`](docs/agent-loop.md)

---

## Status

**Pre-implementation.** This repository holds the pre-plan, autoagents workflow, and (during implementation) Docker Compose, configs, and Nginx templates. The mail stack is not deployed yet.

---

## Repository layout

```
/opt/km0-mail/
├── autoagents/          # Cursor agent loop (GitHub Issues → FEAT tasks)
├── docs/
│   ├── issue-mail-preplan.md
│   └── agent-loop.md
├── scripts/             # git-sync, setup-autoagents-gh, move-agent-task-to-done
└── (implementation)     # docker-compose.yml, config/, nginx/, sql/ — coming in FEAT work
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
