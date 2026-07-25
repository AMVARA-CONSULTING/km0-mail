# FEAT-Task: DOCS — Agent pipeline order for mail SSO / activate

## GitHub Issue
- **Number:** #16
- **URL:** https://github.com/AMVARA-CONSULTING/km0-mail/issues/16
- **Labels:** documentation

## Problem / goal
Parallel FEATs (#10–#15, opencloud #23–#26, spike #12) race. Coders need an ordered blocker list.

## High-level instructions for coder
1. Add `docs/agent-pipeline-mail-activate.md` (order from issue body)
2. Comment on #10–#15 and opencloud #23–#26 with link; mark #12 blocked until foundations
3. Optionally add pointer in `docs/agent-loop.md`
4. FEAT→UNTESTED (docs-only test = file exists + comments)

## Acceptance criteria
- [x] Doc published; cross-issue comments done

## Implementation notes (2026-07-25)
- Added `docs/agent-pipeline-mail-activate.md` with required order (steps 1–9), parallel work (#10/#23/#22), and explicit agent blockers.
- Pointer from `docs/agent-loop.md`; CHANGELOG entry under Unreleased.
- Commented km0-mail #8–#15 (incl. #12 blocked) and km0-opencloud #22–#26 with link to the order doc.
- No `blocked` label in repo; #12 blocker is documented in issue comment + FEAT-12 body.

## Testing instructions

Docs-only verification:

1. Confirm file exists and is readable:
   ```bash
   test -f /opt/km0-mail/docs/agent-pipeline-mail-activate.md && head -n 20 /opt/km0-mail/docs/agent-pipeline-mail-activate.md
   ```
2. Confirm `docs/agent-loop.md` links the pipeline doc (grep `agent-pipeline-mail-activate`).
3. Confirm CHANGELOG Unreleased mentions issue #16.
4. Spot-check GitHub comments exist:
   ```bash
   gh api repos/AMVARA-CONSULTING/km0-mail/issues/12/comments --jq '.[].body' | grep -i blocked
   gh api repos/AMVARA-CONSULTING/km0-mail/issues/16/comments --jq 'length'
   gh api repos/AMVARA-CONSULTING/km0-opencloud/issues/24/comments --jq '.[].body' | grep -i 'step 3'
   ```
5. No Docker / mail stack changes required for this task.
