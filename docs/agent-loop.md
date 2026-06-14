# autoagents loop — km0-mail

Orchestrated multi-agent workflow using **cursor-agent** and **GitHub Issues**. No Ollama or local LLM required.

## Quick start

```bash
# 1. GitHub CLI (Luipy56)
cp autoagents/.env.example autoagents/.env
# Edit .env — set GH_TOKEN if gh is not logged in; REDMINE_ISSUE_ID=7605 for closing notes
./scripts/setup-autoagents-gh.sh

# 2. Single step
./autoagents/autoagents-loop.sh 001

# 3. Full loop (every 5 min)
./autoagents/autoagents-loop.sh
```

## Pipeline (one cycle)

| Step | Prompt | Trigger |
|------|--------|---------|
| 001 | `001-gh-reviewer.md` | Open GH issues without FEAT file, or Docker log incidents |
| 010 | `010-feature-coder.md` | `FEAT-*.md` (up to 5× per cycle) |
| 002 | `002-coder/CODER.md` | `NEW-*.md` / `WIP-*.md` |
| 012 | `012-feature-coder-handoff.md` | `WIP-*.md` handoff check |
| 020 | `020-test.md` | `UNTESTED-*.md` / `TESTING-*.md` |
| 030 | `030-closing-reviewer.md` | `CLOSED-*.md` |
| 040 | `040-committer.md` | Uncommitted changes (optional; `AGENT_COMMITTER_USE_CURSOR=1`) |

## GitHub labels

| Label | Meaning |
|-------|---------|
| `agent:planned` | 001 created FEAT task |
| `agent:wip` | Coder working |
| `agent:untested` | Ready for tester |
| `agent:testing` | Tester active |

Create labels in the repo if missing.

## Repo conventions

- Branch: **`main`**
- Remote: **`git@github.com:AMVARA-CONSULTING/km0-mail.git`**
- Git sync: **`./scripts/git-sync-main.sh`**
- Task docs: **`autoagents/TASKS-README.md`**
- Architecture pre-plan: **`docs/issue-mail-preplan.md`**
- Cursor skill: **`.cursor/skills/autoagents/SKILL.md`**
- Redmine tracking ticket: **#7605**

## Direct user prompts vs autoagents

- **autoagents loop** — structured TASK/FEAT/TEST workflow driven by task files and GitHub.
- **Direct IDE chat** — same engineering discipline; follow minimal diff and runbook conventions.

## Environment

| Variable | Default |
|----------|---------|
| `AGENT_GH_REPO` | `AMVARA-CONSULTING/km0-mail` |
| `AGENT_GIT_BRANCH` | `main` |
| `AGENT_LOOP_SLEEP_MINUTES` | `5` |
| `AGENT_COMMITTER_USE_CURSOR` | `1` (full committer via cursor-agent) |
| `AGENT_LOOP_TMP` | `autoagents/var/loop` (inside repo; not `/tmp`) |
| `GH_TOKEN` | from `autoagents/.env` |
| `REDMINE_URL` | Redmine base URL (optional; closing notes) |
| `REDMINE_API_KEY` | Redmine API key (optional) |
| `REDMINE_ISSUE_ID` | `7605` — target Redmine issue for autoagents notes |

Preflight digest: `autoagents/var/loop/001-latest-context.txt`

**Version counter:** `autoagents/VERSION` (semver). Patch increments automatically on each agent prompt run and each FEAT task created; the committer must always commit and push it.

## Docker containers monitored (001 preflight)

When the stack is deployed (`COMPOSE_PROJECT_NAME=km0-mail`):

- `km0-mail-postfix-1`
- `km0-mail-dovecot-1`
- `km0-mail-rspamd-1`
- `km0-mail-roundcube-1`
- `km0-mail-postgres-1`
