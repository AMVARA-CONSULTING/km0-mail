# Task workflow (autoagents / km0-mail)

Tasks move through a single pipeline. See **`docs/agent-loop.md`** for roles and GitHub label conventions. **Before renaming task files**, sync with **`./scripts/git-sync-main.sh`**.

## Filename pattern

`<STATUS>-<GITHUB-ISSUE-NUMBER>-<YYYYMMDD>-<HHMM>-<slug>.md`

For **NEW-** tasks without an issue number, use `NEW-0-` or omit issue segment: `NEW-YYYYMMDD-HHMM-<slug>.md`.

Examples: `FEAT-7605-20260614-1200-self-hosted-mail-stack.md`, `CLOSED-7605-20260620-1200-self-hosted-mail-stack.md`

The **`<YYYYMMDD>`** segment places archived tasks under **`done/YYYY/MM/DD/`**.

## Statuses

| Status       | Meaning |
|--------------|--------|
| **new**      | Task defined, not started (incidents from logs). |
| **feat**     | Feature-sized task from GitHub issue. |
| **wip**      | Work in progress. When done → **UNTESTED-**. |
| **untested** | Implementation done; **Testing instructions** appended. |
| **testing**  | Tester is verifying. |
| **closed**   | Verified; ready for closing reviewer. |

## Flow

```text
  new   ─┐
         ├─→  wip  →  untested  →  testing  →  closed  →  done/YYYY/MM/DD/
  feat  ─┘
```

On test failure: **testing → wip**, then **wip → untested** when ready.

## Archiving

```bash
./scripts/move-agent-task-to-done.sh autoagents/tasks/CLOSED-7605-20260620-1200-example.md
```

→ **`autoagents/tasks/done/2026/06/20/CLOSED-7605-20260620-1200-example.md`**

When Redmine is configured (`REDMINE_URL`, `REDMINE_API_KEY`, `REDMINE_ISSUE_ID` in `autoagents/.env`), the move script also posts an English Textile (`.red`) closing summary to the Redmine issue via `autoagents/redmine_sync.py`.

## Rules of thumb

- **`autoagents/VERSION`:** patch bumps on every loop prompt and each new FEAT task; committer always pushes it.
- **feat → wip** when feature coder starts.
- **wip → untested** when implementation complete + **Testing instructions** at end.
- **untested → testing** when tester starts.
- **testing → closed** on pass; **testing → wip** on fail.
- **closed → done/** after closing summary (move script).
