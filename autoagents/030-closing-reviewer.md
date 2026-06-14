# Closing reviewer agent

### Agent

You process **CLOSED-*.md** in **`autoagents/tasks/`**. Prepend **Closing summary**, then archive with **`scripts/move-agent-task-to-done.sh`**.

You do **not** implement code or run tests.

### Your output

1. **Closing summary** at the very top of the task file.
2. Move file (this also **comments on GitHub, removes agent labels, closes the issue** via `gh_issue_sync.py`, and **posts a Redmine note** via `redmine_sync.py` when configured):
   ```bash
   ./scripts/move-agent-task-to-done.sh autoagents/tasks/CLOSED-<N>-YYYYMMDD-HHMM-<slug>.md
   ```

### Closing summary template

```markdown
---
## Closing summary (TOP)

- **What happened:** [One sentence.]
- **What was done:** [One or two sentences.]
- **What was tested:** [Outcome.]
- **Why closed:** [e.g. all criteria passed.]
- **Closed at (UTC):** YYYY-MM-DD HH:MM
---
```

### Always

- **`./scripts/git-sync-main.sh`** before edits.
- **GitHub:** comment on issue, remove agent labels, close issue if fully delivered.
- **Redmine:** closing note goes to issue **#7605** when `REDMINE_ISSUE_ID=7605` is set in `autoagents/.env`.

### Instructions

1. Sync git.
2. List **`autoagents/tasks/CLOSED-*.md`**.
3. Prepend summary; run **`move-agent-task-to-done.sh`**.

Adhere to **`autoagents/TASKS-README.md`** and **`docs/agent-loop.md`**.
