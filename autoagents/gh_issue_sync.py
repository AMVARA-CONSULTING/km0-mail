#!/usr/bin/env python3
"""
GitHub issue sync for autoagents — comments, labels, close.
Uses gh CLI; repo from AGENT_GH_REPO (default AMVARA-CONSULTING/km0-mail).
Requires GH_TOKEN or gh auth login (see scripts/setup-autoagents-gh.sh).
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from typing import Iterable, Optional

GH_REPO = os.environ.get("AGENT_GH_REPO", "AMVARA-CONSULTING/km0-mail")

AGENT_LABELS = (
    "agent:planned",
    "agent:wip",
    "agent:untested",
    "agent:testing",
)


def _run_gh(args: list[str], *, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    return subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
        check=False,
    )


def gh_available() -> bool:
    try:
        r = _run_gh(["auth", "status", "--hostname", "github.com"], timeout=15)
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def ensure_gh_auth() -> bool:
    """Return True when gh can call the API (GH_TOKEN or stored login)."""
    if gh_available():
        return True
    token = os.environ.get("GH_TOKEN", "").strip()
    if not token:
        return False
    try:
        proc = subprocess.run(
            ["gh", "auth", "login", "--hostname", "github.com", "--with-token"],
            input=token + "\n",
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        return proc.returncode == 0 and gh_available()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _issue_has_agent_comment(issue_num: int, marker: str) -> bool:
    r = _run_gh(
        [
            "issue",
            "view",
            str(issue_num),
            "--repo",
            GH_REPO,
            "--json",
            "comments",
        ],
        timeout=30,
    )
    if r.returncode != 0:
        return False
    import json

    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError:
        return False
    for c in data.get("comments") or []:
        body = (c.get("body") or "").lower()
        if marker.lower() in body:
            return True
    return False


def _add_labels(issue_num: int, labels: Iterable[str]) -> bool:
    ok = True
    for label in labels:
        r = _run_gh(
            [
                "issue",
                "edit",
                str(issue_num),
                "--repo",
                GH_REPO,
                "--add-label",
                label,
            ],
            timeout=30,
        )
        if r.returncode != 0:
            ok = False
            print(
                f"  warn: could not add label {label!r} to #{issue_num}: {r.stderr.strip()}",
                file=sys.stderr,
            )
    return ok


def _remove_labels(issue_num: int, labels: Iterable[str]) -> None:
    for label in labels:
        _run_gh(
            [
                "issue",
                "edit",
                str(issue_num),
                "--repo",
                GH_REPO,
                "--remove-label",
                label,
            ],
            timeout=30,
        )


def comment(issue_num: int, body: str) -> bool:
    r = _run_gh(
        [
            "issue",
            "comment",
            str(issue_num),
            "--repo",
            GH_REPO,
            "--body",
            body,
        ],
        timeout=30,
    )
    if r.returncode != 0:
        print(
            f"  error: gh issue comment #{issue_num}: {r.stderr.strip()}",
            file=sys.stderr,
        )
        return False
    return True


def notify_planned(issue_num: int, feat_basename: str) -> bool:
    marker = "agent 001"
    if _issue_has_agent_comment(issue_num, marker):
        print(f"  skip GitHub notify #{issue_num} — Agent 001 comment exists")
        return True
    body = (
        f"🤖 **Agent 001:** Added FEAT task for this issue.\n\n"
        f"- Task file: `autoagents/tasks/{feat_basename}`\n"
        f"- Next: feature coder (010) picks up **FEAT-{issue_num}-*** → **WIP** → **UNTESTED**.\n"
        f"- Labels: `agent:planned`"
    )
    if not comment(issue_num, body):
        return False
    _add_labels(issue_num, ("agent:planned",))
    print(f"  GitHub: commented + agent:planned on #{issue_num}")
    return True


def notify_closed(issue_num: int, summary: str) -> bool:
    """Final comment, remove agent labels, close issue."""
    body = (
        f"🤖 **Agent 030 (closing):** Work completed and archived.\n\n"
        f"{summary.strip()}\n\n"
        f"Task moved under `autoagents/tasks/done/`."
    )
    if not comment(issue_num, body):
        return False
    _remove_labels(issue_num, AGENT_LABELS)
    r = _run_gh(
        [
            "issue",
            "close",
            str(issue_num),
            "--repo",
            GH_REPO,
        ],
        timeout=30,
    )
    if r.returncode != 0:
        print(
            f"  error: gh issue close #{issue_num}: {r.stderr.strip()}",
            file=sys.stderr,
        )
        return False
    print(f"  GitHub: closed #{issue_num}")
    return True


def extract_closing_summary(task_text: str) -> str:
    m = re.search(
        r"## Closing summary \(TOP\)\s*\n(.*?)\n---",
        task_text,
        re.DOTALL | re.IGNORECASE,
    )
    if m:
        return m.group(1).strip()
    return "Closing summary not found in task file."


def issue_num_from_closed_basename(basename: str) -> Optional[int]:
    m = re.match(r"^CLOSED-(\d+)-", basename)
    return int(m.group(1)) if m else None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Usage: gh_issue_sync.py close autoagents/tasks/CLOSED-N-....md",
            file=sys.stderr,
        )
        sys.exit(1)
    if sys.argv[1] == "close" and len(sys.argv) == 3:
        path = sys.argv[2]
        bn = os.path.basename(path)
        num = issue_num_from_closed_basename(bn)
        if num is None:
            print(f"Could not parse issue number from {bn}", file=sys.stderr)
            sys.exit(1)
        if not ensure_gh_auth():
            print("gh not authenticated (set GH_TOKEN or run setup-autoagents-gh.sh)", file=sys.stderr)
            sys.exit(1)
        with open(path, encoding="utf-8") as f:
            text = f.read()
        ok = notify_closed(num, extract_closing_summary(text))
        sys.exit(0 if ok else 1)
    print("Unknown command", file=sys.stderr)
    sys.exit(1)
