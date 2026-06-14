---
name: autoagents
description: Runs the km0-mail autoagents loop (GitHub issues → FEAT tasks → cursor-agent coders/testers/closers). Use when working with autoagents/, task files (FEAT/NEW/WIP/UNTESTED/TESTING/CLOSED), autoagents-loop.sh, issue_checker_agent.py, or GitHub agent labels on AMVARA-CONSULTING/km0-mail. Redmine tracking ticket #7605.
---

# autoagents (km0-mail)

## Quick start

```bash
./scripts/setup-autoagents-gh.sh          # once: gh auth + issue list test
./autoagents/autoagents-loop.sh 001        # single step
./autoagents/autoagents-loop.sh            # full loop every 5 min
```

Requires **cursor-agent** on PATH. No Ollama.

## Task pipeline

See **`autoagents/TASKS-README.md`** and **`docs/agent-loop.md`**.

```text
FEAT/NEW → WIP → UNTESTED → TESTING → CLOSED → done/YYYY/MM/DD/
```

## Key paths

| Path | Purpose |
|------|---------|
| `autoagents/autoagents-loop.sh` | Orchestrator |
| `autoagents/VERSION` | Semver counter — patch +1 on every prompt/task (always commit) |
| `autoagents/issue_checker_agent.py` | GH → FEAT helper |
| `autoagents/gh_issue_sync.py` | GitHub comment/label/close on archive |
| `autoagents/redmine_sync.py` | Redmine closing notes (issue #7605) |
| `autoagents/tasks/` | Active task queue |
| `docs/issue-mail-preplan.md` | Mail stack architecture pre-plan |
| `scripts/git-sync-main.sh` | Sync before edits |
| `scripts/move-agent-task-to-done.sh` | Archive CLOSED tasks |
| `autoagents/.env` | GH_TOKEN, Redmine vars (gitignored) |

## Single commands

```bash
./autoagents/autoagents-loop.sh 001
./autoagents/autoagents-loop.sh feat
./autoagents/autoagents-loop.sh coder
./autoagents/autoagents-loop.sh tester
./autoagents/autoagents-loop.sh closing-review
./autoagents/autoagents-loop.sh committer
```

## Redmine

Closing summaries post to Redmine issue **#7605** when `REDMINE_URL`, `REDMINE_API_KEY`, and `REDMINE_ISSUE_ID=7605` are set in `autoagents/.env`.
