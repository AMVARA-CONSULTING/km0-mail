#!/usr/bin/env python3
"""
Issue Checker Agent — creates FEAT task files from open GitHub issues.
Uses gh CLI; repo from AGENT_GH_REPO env (default AMVARA-CONSULTING/km0-mail).
Posts GitHub comment + agent:planned when a FEAT file is created.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_DIR = os.path.join(SCRIPT_DIR, "tasks")
GH_REPO = os.environ.get("AGENT_GH_REPO", "AMVARA-CONSULTING/km0-mail")
MAX_PER_RUN = int(os.environ.get("AGENT_001_MAX_ISSUES", "3"))

sys.path.insert(0, SCRIPT_DIR)
from bump_version import bump_version  # noqa: E402
from gh_issue_sync import ensure_gh_auth, notify_planned  # noqa: E402


def _gh(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


def has_task_file(issue_num: int) -> bool:
    if not os.path.isdir(TASKS_DIR):
        return False
    prefix = f"FEAT-{issue_num}-"
    return any(f.startswith(prefix) for f in os.listdir(TASKS_DIR))


def get_open_issues() -> list[dict]:
    try:
        result = _gh(
            "issue",
            "list",
            "--repo",
            GH_REPO,
            "--state",
            "open",
            "--json",
            "number,title,url",
        )
        if result.returncode != 0:
            print(result.stderr.strip(), file=sys.stderr)
            return []
        return json.loads(result.stdout)
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def fetch_issue_details(issue_num: int) -> dict | None:
    try:
        result = _gh(
            "issue",
            "view",
            str(issue_num),
            "--repo",
            GH_REPO,
            "--json",
            "body,state,title,url,labels,createdAt",
        )
        if result.returncode != 0:
            return None
        data = json.loads(result.stdout)
        data["number"] = int(issue_num)
        return data
    except (json.JSONDecodeError, FileNotFoundError):
        return None


def create_task(issue: dict) -> str:
    num = issue["number"]
    title = issue["title"]
    url = issue["url"]
    body = issue.get("body") or ""
    created = issue.get("createdAt", "")
    labels = issue.get("labels", [])
    labels_str = ", ".join(str(l.get("name", "")) for l in labels) if labels else "none"

    clean_body = body.replace("\n", " ") if body else "[No issue body]"
    summary = clean_body[:250].strip()
    if len(clean_body) > 250:
        summary += "..."

    slug = title.lower()
    for ch in " /_":
        slug = slug.replace(ch, "-")
    slug = "".join(c if c.isalnum() or c == "-" else "" for c in slug)[:40].strip("-") or "issue"

    now = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    filename = f"FEAT-{num}-{now}-{slug}.md"
    filepath = os.path.join(TASKS_DIR, filename)

    content = f"""# {title}

## GitHub Issue
- **Issue:** {url}
- **Number:** #{num}
- **Labels:** {labels_str}
- **Created:** {created}
- **Redmine:** #7605 (tracking ticket when configured in autoagents/.env)

## Problem / goal
{summary}

## High-level instructions for coder
- Read the full issue at {url}
- Follow **`docs/issue-mail-preplan.md`** for architecture, DNS, ports, and phases
- Implement under `docker-compose.yml`, `config/`, `nginx/`, `scripts/`, `sql/`, `docs/`
- Phase 1 focus: Postfix + Dovecot + Rspamd + Roundcube + PostgreSQL on same VPS as OpenCloud
- User addresses: `@km0digital.com`; service hostname: `mail.km0digital.com`
- No OpenCloud LDAP unification in phase 1; include `mail_accounts.opencloud_uuid` nullable in SQL
- Light SMTP relay from localhost for OpenCloud / marketing / register-api / km0-web (see pre-plan)
- Add **Testing instructions** before renaming to UNTESTED-

## References
- Pre-plan: docs/issue-mail-preplan.md
- Repo: https://github.com/{GH_REPO}
- Runbook: docs/runbook.md (create/update during implementation)
"""
    os.makedirs(TASKS_DIR, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return filepath


def run_workflow() -> bool:
    print("=" * 60)
    print("Issue Checker (autoagents)")
    print(f"Repo: {GH_REPO}")
    print("=" * 60)

    if not ensure_gh_auth():
        print("\ngh not authenticated — run ./scripts/setup-autoagents-gh.sh", file=sys.stderr)
        return False

    issues = get_open_issues()
    if not issues:
        print("\nNo open GitHub issues.")
        return False

    created = 0
    for issue in issues:
        if created >= MAX_PER_RUN:
            print(f"\nReached limit ({MAX_PER_RUN}) for this run.")
            break
        num = issue["number"]
        if has_task_file(num):
            print(f"  skip #{num} — FEAT file exists")
            continue
        details = fetch_issue_details(num)
        if not details:
            print(f"  skip #{num} — could not fetch details")
            continue
        labels = [l.get("name", "") for l in details.get("labels", [])]
        if "agent:planned" in labels:
            print(f"  skip #{num} — agent:planned")
            continue
        path = create_task(details)
        basename = os.path.basename(path)
        print(f"  created: {basename}")
        bump_version(f"task:FEAT-{num}")
        notify_planned(num, basename)
        created += 1

    print(f"\nCreated {created} task file(s)")
    return created > 0


if __name__ == "__main__":
    run_workflow()
