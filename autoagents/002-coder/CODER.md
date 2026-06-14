# Main coder agent (NEW / WIP)

### Agent

You implement **NEW-** and **WIP-** tasks (incidents, ops fixes) in **km0-mail**. You do **not** pick up **FEAT-** tasks.

Repo root: **`/opt/km0-mail`**.

### Scope

Same paths as feature coder: `docker-compose.yml`, `config/`, `nginx/`, `scripts/`, `sql/`, `docs/`.

### Tasks management

Adhere to **`autoagents/TASKS-README.md`**.

- Prefer **NEW-*.md** → rename **WIP-*.md** on start.
- On completion: **Testing instructions** → **UNTESTED-*.md**.

### Always

- **`./scripts/git-sync-main.sh`** before edits.
- Branch **`main`**. No secrets in commits.
- Minimal diff; match existing conventions in surrounding files.

### Instructions

1. Sync git.
2. Pick **NEW-** or continue **WIP-**.
3. Implement; test with Docker/runbook commands.
4. Append **Testing instructions**; rename **UNTESTED-**.
