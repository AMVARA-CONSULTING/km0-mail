---
## Closing summary (TOP)

- **What happened:** Parallel FEATs (#10–#15 and opencloud) lacked an ordered blocker list, and Agent 001 was recreating FEAT tasks after they left FEAT status.
- **What was done:** Published `docs/agent-pipeline-mail-activate.md` with cross-issue coordination comments; fixed `issue_checker_agent.py` / `001-gh-reviewer.md` dedupe to cover WIP/UNTESTED/TESTING/CLOSED and pipeline labels.
- **What was tested:** Docs, CHANGELOG, GH comments, and issue-checker dry run all **PASS** (tester report 2026-07-25).
- **Why closed:** All acceptance criteria passed; docs-only verification complete.
- **Closed at (UTC):** 2026-07-25 14:53
---

# FEAT-Task: DOCS — Agent pipeline order for mail SSO / activate

## GitHub Issue
- **Number:** #16
- **URL:** https://github.com/AMVARA-CONSULTING/km0-mail/issues/16
- **Labels:** documentation

## Problem / goal
Parallel FEATs (#10–#15, opencloud #23–#26, spike #12) race. Coders need an ordered blocker list.
Agent 001 was recreating `FEAT-<N>` after tasks moved to UNTESTED (dedupe only checked `FEAT-*`).

## High-level instructions for coder
1. Add `docs/agent-pipeline-mail-activate.md` (order from issue body)
2. Comment on #10–#15 and opencloud #23–#26 with link; mark #12 blocked until foundations
3. Optionally add pointer in `docs/agent-loop.md`
4. FEAT→UNTESTED (docs-only test = file exists + comments)
5. Fix `issue_checker_agent.py` + `001-gh-reviewer.md` dedupe so FEATs are not recreated

## Acceptance criteria
- [x] Doc published; cross-issue comments done
- [x] 001 dedupe covers WIP/UNTESTED/TESTING/CLOSED + pipeline labels

## Implementation notes (2026-07-25)
- Added `docs/agent-pipeline-mail-activate.md` with required order (steps 1–9), parallel work (#10/#23/#22), and explicit agent blockers.
- Pointer from `docs/agent-loop.md`; CHANGELOG entry under Unreleased.
- Commented km0-mail #8–#15 (incl. #12 blocked) and km0-opencloud #22–#26 with link to the order doc.
- No `blocked` label in repo; #12 blocker is documented in issue comment + FEAT-12 body.
- **Follow-up:** `has_task_file()` now matches any `FEAT|WIP|UNTESTED|TESTING|CLOSED-<N>-*`; skip also on `agent:planned|wip|untested|testing`. Documented in pipeline doc + `001-gh-reviewer.md`. Duplicate FEAT-14/15/16 (1450) removed.

## Testing instructions

Docs + dedupe verification:

1. Confirm file exists and is readable:
   ```bash
   test -f /opt/km0-mail/docs/agent-pipeline-mail-activate.md && head -n 20 /opt/km0-mail/docs/agent-pipeline-mail-activate.md
   ```
2. Confirm `docs/agent-loop.md` links the pipeline doc (grep `agent-pipeline-mail-activate`).
3. Confirm CHANGELOG Unreleased mentions issue #16 and Agent 001 dedupe.
4. Spot-check GitHub comments exist:
   ```bash
   gh api repos/AMVARA-CONSULTING/km0-mail/issues/12/comments --jq '.[].body' | grep -i blocked
   gh api repos/AMVARA-CONSULTING/km0-mail/issues/16/comments --jq 'length'
   gh api repos/AMVARA-CONSULTING/km0-opencloud/issues/24/comments --jq '.[].body' | grep -i 'step 3'
   ```
5. Confirm issue checker does **not** recreate FEATs for issues already UNTESTED:
   ```bash
   # No FEAT-14/15/16 duplicates under tasks/
   ls /opt/km0-mail/autoagents/tasks/FEAT-1[456]-*.md 2>/dev/null || echo 'no duplicate FEATs'
   python3 /opt/km0-mail/autoagents/issue_checker_agent.py
   # Expect: skip #9–#16 (task file exists and/or pipeline labels); Created 0 task file(s)
   ```
6. No Docker / mail stack changes required for this task.

## Test report

1. **Date/time (UTC) and log window:** 2026-07-25 14:52:50 UTC → 14:53:01 UTC. Docs/dedupe only — no mail-stack log window.
2. **Environment:** branch `main` @ `e9e5d86`; compose/Docker **N/A** (task explicitly docs-only). Stack readiness: not required.
3. **What was tested:** Pipeline doc existence + content; `docs/agent-loop.md` pointer; CHANGELOG Unreleased (#16 + Agent 001 dedupe); GH comments on #12 (blocked), #16 (count), opencloud #24 (step 3); no duplicate `FEAT-14/15/16`; `issue_checker_agent.py` dry run skips #9–#16 and creates 0 files; dedupe code paths present.
4. **Results:**
   - `docs/agent-pipeline-mail-activate.md` exists and readable — **PASS** (`head` shows title, purpose, product rule, required-order table)
   - `docs/agent-loop.md` links pipeline doc — **PASS** (line 50: `docs/agent-pipeline-mail-activate.md`)
   - CHANGELOG Unreleased mentions #16 and Agent 001 dedupe — **PASS** (lines 12–13)
   - GH #12 comments mark blocked — **PASS** (`Blocked` / `BLOCKED — do not start` coordination comments)
   - GH #16 has comments — **PASS** (`comments | length` → 6)
   - opencloud #24 comment mentions step 3 — **PASS** (`this is **step 3** — **hard-blocks** prod activate CTA`)
   - No duplicate FEAT-14/15/16 — **PASS** (`no duplicate FEATs`)
   - Issue checker skips existing pipeline tasks, creates 0 — **PASS** (skip #9–#16; `Created 0 task file(s)`)
   - Dedupe covers WIP/UNTESTED/TESTING/CLOSED + labels — **PASS** (`_TASK_STATUSES`, `agent:planned|wip|untested|testing` in `issue_checker_agent.py`)
5. **Overall:** **PASS**
6. **URLs tested:** N/A (docs + `gh api` / local files only). Issue refs: https://github.com/AMVARA-CONSULTING/km0-mail/issues/16 , #12; https://github.com/AMVARA-CONSULTING/km0-opencloud/issues/24
7. **Relevant log excerpts:**
   ```
   issue_checker: skip #16 … #9 — task file exists (FEAT/WIP/UNTESTED/TESTING/CLOSED)
   issue_checker: Created 0 task file(s)
   ls FEAT-1[456]-*.md → no duplicate FEATs
   agent-loop.md:50 → docs/agent-pipeline-mail-activate.md
   ```
