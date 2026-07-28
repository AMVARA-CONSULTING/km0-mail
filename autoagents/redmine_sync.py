#!/usr/bin/env python3
"""
Redmine note sync for autoagents — posts a Textile (.red) closing summary
when a CLOSED task is archived.

Env (autoagents/.env):
  REDMINE_URL       — e.g. https://redmine.amvara.de
  REDMINE_API_KEY   — X-Redmine-API-Key
  REDMINE_ISSUE_ID  — target Redmine issue (integer)
  REDMINE_ACTIVITY_ID — time_entry activity (default 10 = Service Management)

Records task duration in the note and as a Redmine time_entry.
Uses stdlib urllib only (no httpx).
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Optional

NOTE_AUTHOR = "km0-mail autoagents"
NOTES_DIR = "/root/redminenotes"
REDMINE_ACTIVITY_ID = int(os.environ.get("REDMINE_ACTIVITY_ID", "10"))
TASK_STAMP_RE = re.compile(
    r"^(?:CLOSED|NEW|FEAT|WIP|UNTESTED|TESTING)-\d+-(\d{8})-(\d{4})-",
    re.IGNORECASE,
)
# Closing summary uses Markdown bold: **Closed at (UTC):** YYYY-MM-DD HH:MM
# Allow optional closing ** after the colon so the date is still captured.
CLOSED_AT_RE = re.compile(
    r"Closed at \(UTC\):\*{0,2}\s*(\d{4}-\d{2}-\d{2})\s+(\d{1,2}:\d{2})",
    re.IGNORECASE,
)
CLOSED_AT_BULLET_RE = re.compile(
    r"^-\s+\*\*Closed at \(UTC\):\*\*\s*(\d{4}-\d{2}-\d{2})\s+(\d{1,2}:\d{2})\s*$",
    re.IGNORECASE | re.MULTILINE,
)


class RedmineError(Exception):
    """Redmine API call failed."""


class IssueNotFound(RedmineError):
    """Redmine issue does not exist."""


def add_redmine_note(
    base_url: str,
    api_key: str,
    issue_id: int,
    notes: str,
    *,
    timeout: float = 60.0,
) -> None:
    """PUT /issues/{id}.json with a journal note. Raises on HTTP errors."""
    url = f"{base_url.rstrip('/')}/issues/{issue_id}.json"
    payload = json.dumps({"issue": {"notes": notes}}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        method="PUT",
        headers={
            "X-Redmine-API-Key": api_key,
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status >= 400:
                raise RedmineError(f"Redmine PUT issue failed: {resp.status}")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:500]
        if exc.code == 404:
            raise IssueNotFound(f"Issue #{issue_id} not found") from exc
        raise RedmineError(
            f"Redmine PUT issue failed: {exc.code} {body}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RedmineError(f"Redmine request failed: {exc.reason}") from exc


def add_redmine_time_entry(
    base_url: str,
    api_key: str,
    issue_id: int,
    hours: float,
    comments: str,
    *,
    activity_id: Optional[int] = None,
    spent_on: Optional[str] = None,
    timeout: float = 60.0,
) -> None:
    """POST /time_entries.json — official spent-time log."""
    url = f"{base_url.rstrip('/')}/time_entries.json"
    payload = {
        "time_entry": {
            "issue_id": issue_id,
            "hours": round(float(hours), 2),
            "comments": comments[:255],
            "activity_id": activity_id if activity_id is not None else REDMINE_ACTIVITY_ID,
            "spent_on": spent_on or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        }
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "X-Redmine-API-Key": api_key,
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status >= 400:
                raise RedmineError(f"Redmine POST time_entry failed: {resp.status}")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:500]
        if exc.code == 404:
            raise IssueNotFound(f"Issue #{issue_id} not found for time_entry") from exc
        raise RedmineError(
            f"Redmine POST time_entry failed: {exc.code} {body}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RedmineError(f"Redmine time_entry request failed: {exc.reason}") from exc


def parse_task_start_utc(basename: str) -> Optional[datetime]:
    """Start time from task filename stamp (UTC). Prefer WIP-refresh stamp."""
    m = TASK_STAMP_RE.match(basename)
    if not m:
        return None
    try:
        return datetime.strptime(f"{m.group(1)}{m.group(2)}", "%Y%m%d%H%M").replace(
            tzinfo=timezone.utc
        )
    except ValueError:
        return None


def parse_closed_at_utc(summary: str) -> Optional[datetime]:
    """
    End time from closing summary Closed at (UTC) field.

    Accepts both plain and Markdown-bold forms:
      Closed at (UTC): 2026-07-25 14:36
      - **Closed at (UTC):** 2026-07-25 14:36
    """
    m = CLOSED_AT_BULLET_RE.search(summary) or CLOSED_AT_RE.search(summary)
    if not m:
        return None
    try:
        return datetime.strptime(f"{m.group(1)} {m.group(2)}", "%Y-%m-%d %H:%M").replace(
            tzinfo=timezone.utc
        )
    except ValueError:
        return None


def format_duration_label(delta: timedelta) -> str:
    total_sec = max(0, int(delta.total_seconds()))
    hours, rem = divmod(total_sec, 3600)
    minutes, _ = divmod(rem, 60)
    if hours and minutes:
        human = f"{hours} h {minutes} min"
    elif hours:
        human = f"{hours} h"
    else:
        human = f"{max(minutes, 1) if total_sec > 0 else 0} min"
    decimal_h = round(total_sec / 3600.0, 2)
    if total_sec > 0 and decimal_h < 0.01:
        decimal_h = 0.01
    return f"{human} ({decimal_h:.2f} h)"


def compute_task_duration(
    task_basename: str, summary_text: str
) -> tuple[Optional[str], Optional[float], Optional[str]]:
    """
    Return (label, hours, spent_on_yyyy_mm_dd) from filename stamp → Closed at.

    Never falls back to datetime.now() for the end time: a missing Closed at
    means we skip time logging rather than inventing inflated hours.
    """
    start = parse_task_start_utc(task_basename)
    end = parse_closed_at_utc(summary_text)
    if start is None or end is None or end < start:
        return None, None, None
    delta = end - start
    label = format_duration_label(delta)
    hours = round(max(delta.total_seconds(), 0) / 3600.0, 2)
    if delta.total_seconds() > 0 and hours < 0.01:
        hours = 0.01
    return label, hours, end.strftime("%Y-%m-%d")


def get_redmine_config() -> tuple[str, str, int] | None:
    """Return (base_url, api_key, issue_id) when fully configured, else None."""
    base_url = os.environ.get("REDMINE_URL", os.environ.get("REDMINE_BASE_URL", "")).strip()
    api_key = os.environ.get("REDMINE_API_KEY", "").strip()
    issue_raw = os.environ.get("REDMINE_ISSUE_ID", "").strip()
    if not base_url or not api_key or not issue_raw:
        return None
    try:
        issue_id = int(issue_raw)
    except ValueError:
        print(
            f"  warn: REDMINE_ISSUE_ID must be an integer, got {issue_raw!r}",
            file=sys.stderr,
        )
        return None
    return base_url, api_key, issue_id


def extract_closing_summary(task_text: str) -> str:
    m = re.search(
        r"## Closing summary \(TOP\)\s*\n(.*?)\n---",
        task_text,
        re.DOTALL | re.IGNORECASE,
    )
    if m:
        return m.group(1).strip()
    return ""


def _parse_summary_bullets(summary: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in summary.splitlines():
        m = re.match(r"^-\s+\*\*(.+?):\*\*\s*(.*)$", line.strip())
        if m:
            fields[m.group(1).strip()] = m.group(2).strip()
    return fields



def format_closing_note_textile(
    *,
    task_basename: str,
    github_issue_num: Optional[int],
    summary_text: str,
    repo: str = "AMVARA-CONSULTING/km0-mail",
    duration_label: Optional[str] = None,
) -> str:
    """Build English Textile note body (.red rules — no Markdown fences)."""
    fields = _parse_summary_bullets(summary_text)
    closed_at = fields.get("Closed at (UTC)", "")
    if not closed_at:
        closed_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    gh_ref: str
    if github_issue_num is None:
        gh_ref = "n/a"
    elif github_issue_num == 0:
        gh_ref = "none (no GitHub issue)"
    else:
        gh_ref = f"#{github_issue_num}"
    lines = [
        "h2. Autoagents task completed",
        "",
        f"*Date:* {closed_at}",
        f"*Repository:* @{repo}@",
        f"*Task file:* @autoagents/tasks/{task_basename}@",
        f"*GitHub issue:* {gh_ref}",
    ]
    if duration_label:
        lines.append(f"*Time taken:* {duration_label}")
    lines.extend(
        [
            "",
            "---",
            "",
            "h3. Summary",
            "",
        ]
    )

    label_map = (
        ("What happened", "What happened"),
        ("What was done", "What was done"),
        ("What was tested", "What was tested"),
        ("Why closed", "Why closed"),
    )
    for key, heading in label_map:
        value = fields.get(key, "")
        if value:
            lines.append(f"* *{heading}:* {value}")
        else:
            lines.append(f"* *{heading}:* _(not recorded)_")

    if summary_text and not fields:
        lines.append("")
        lines.append("> Raw closing summary:")
        for raw_line in summary_text.splitlines():
            stripped = raw_line.strip()
            if stripped:
                lines.append(f"> {stripped}")

    lines.extend(
        [
            "",
            "---",
            "",
            f"_Auto-generated by {NOTE_AUTHOR}. Textile (.red) format; English prose._",
        ]
    )
    return "\n".join(lines)


def _note_body_with_author(*, author_label: str, formatted: str) -> str:
    return f"*Posted by:* {author_label}\n\n{formatted}"


def save_note_copy(basename: str, body: str) -> str:
    os.makedirs(NOTES_DIR, exist_ok=True)
    stem = re.sub(r"\.md$", "", basename)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    path = os.path.join(NOTES_DIR, f"autoagents-{stem}-{stamp}.red")
    with open(path, "w", encoding="utf-8") as f:
        f.write(body)
    return path


def issue_num_from_closed_basename(basename: str) -> Optional[int]:
    m = re.match(r"^CLOSED-(\d+)-", basename)
    return int(m.group(1)) if m else None


def notify_redmine(task_path: str) -> bool:
    """Post formatted closing note to Redmine. Returns True on success or skip."""
    cfg = get_redmine_config()
    if cfg is None:
        print("  skip Redmine — REDMINE_URL, REDMINE_API_KEY, or REDMINE_ISSUE_ID unset")
        return True

    base_url, api_key, issue_id = cfg
    bn = os.path.basename(task_path)
    gh_num = issue_num_from_closed_basename(bn)

    with open(task_path, encoding="utf-8") as f:
        task_text = f.read()

    summary = extract_closing_summary(task_text)
    duration_label, hours, spent_on = compute_task_duration(bn, summary)
    formatted = format_closing_note_textile(
        task_basename=bn,
        github_issue_num=gh_num,
        summary_text=summary,
        duration_label=duration_label,
    )
    posted = _note_body_with_author(author_label=NOTE_AUTHOR, formatted=formatted)

    copy_path = save_note_copy(bn, formatted)
    print(f"  Redmine: saved .red copy at {copy_path}")

    note_ok = False
    try:
        add_redmine_note(base_url, api_key, issue_id, posted)
        note_ok = True
    except IssueNotFound as exc:
        print(f"  error: {exc}", file=sys.stderr)
        return False
    except RedmineError as exc:
        print(f"  error: {exc}", file=sys.stderr)
        # Note failed — still try time_entry directly.
        if hours is not None and duration_label and spent_on:
            try:
                add_redmine_time_entry(
                    base_url,
                    api_key,
                    issue_id,
                    hours,
                    f"autoagents: {bn} — {duration_label}",
                    spent_on=spent_on,
                )
                print(f"  Redmine: logged time_entry after note failure ({bn})")
            except (IssueNotFound, RedmineError) as te:
                print(f"  error: time_entry also failed: {te}", file=sys.stderr)
        return False

    issue_url = f"{base_url.rstrip('/')}/issues/{issue_id}"
    print(f"  Redmine: posted note to issue #{issue_id} ({issue_url})")
    if duration_label:
        print(f"  Redmine: note includes Time taken: {duration_label}")
    else:
        print("  Redmine warn: could not compute task duration for note", file=sys.stderr)

    if hours is not None and duration_label and spent_on:
        comment = f"autoagents: {bn} — {duration_label}"
        try:
            add_redmine_time_entry(
                base_url,
                api_key,
                issue_id,
                hours,
                comment,
                spent_on=spent_on,
            )
            print(f"  Redmine: time_entry posted {hours:.2f} h ({duration_label})")
        except (IssueNotFound, RedmineError) as exc:
            print(f"  error: time_entry failed, retrying directly: {exc}", file=sys.stderr)
            try:
                add_redmine_time_entry(
                    base_url,
                    api_key,
                    issue_id,
                    hours,
                    comment,
                    spent_on=spent_on,
                )
                print(f"  Redmine: time_entry posted on retry {hours:.2f} h")
            except (IssueNotFound, RedmineError) as te:
                print(f"  error: time_entry retry failed: {te}", file=sys.stderr)

    return note_ok


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Usage:\n"
            "  redmine_sync.py note <path/to/CLOSED-....md>\n"
            "  redmine_sync.py test [--dry-run]",
            file=sys.stderr,
        )
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "note" and len(sys.argv) == 3:
        ok = notify_redmine(sys.argv[2])
        sys.exit(0 if ok else 1)

    if cmd == "test":
        dry_run = "--dry-run" in sys.argv[2:]
        cfg = get_redmine_config()
        if cfg is None:
            print(
                "REDMINE_URL, REDMINE_API_KEY, and REDMINE_ISSUE_ID must be set",
                file=sys.stderr,
            )
            sys.exit(1)
        base_url, api_key, issue_id = cfg
        now = datetime.now(timezone.utc)
        # Fixed 12-minute window for predictable Time taken in the note.
        start_utc = now - timedelta(minutes=12)
        stamp = start_utc.strftime("%Y%m%d-%H%M")
        closed_utc = now.strftime("%Y-%m-%d %H:%M")
        sample_bn = f"CLOSED-0-{stamp}-redmine-sync-duration-test.md"
        summary_text = (
            "- **What happened:** Integration test for Redmine note + duration.\n"
            "- **What was done:** Verified Time taken in note and time_entry.\n"
            "- **What was tested:** PUT /issues/{id}.json and POST /time_entries.json.\n"
            "- **Why closed:** Smoke test.\n"
            f"- **Closed at (UTC):** {closed_utc}"
        )
        duration_label, hours, spent_on = compute_task_duration(sample_bn, summary_text)
        sample = format_closing_note_textile(
            task_basename=sample_bn,
            github_issue_num=0,
            summary_text=summary_text,
            duration_label=duration_label,
        )
        posted = _note_body_with_author(author_label=NOTE_AUTHOR, formatted=sample)
        print("--- formatted note ---")
        print(posted)
        print("--- end ---")
        if dry_run:
            print("Dry run — not posted.")
            sys.exit(0)
        try:
            add_redmine_note(base_url, api_key, issue_id, posted)
        except (IssueNotFound, RedmineError) as exc:
            print(f"error: note failed: {exc}", file=sys.stderr)
            if hours is not None and duration_label and spent_on:
                try:
                    add_redmine_time_entry(
                        base_url,
                        api_key,
                        issue_id,
                        hours,
                        f"autoagents: {sample_bn} — {duration_label}",
                        spent_on=spent_on,
                    )
                    print("Logged time_entry after note failure.")
                except (IssueNotFound, RedmineError) as te:
                    print(f"error: time_entry also failed: {te}", file=sys.stderr)
                    sys.exit(1)
            sys.exit(1)
        print(f"Posted test note to {base_url}/issues/{issue_id}")
        if hours is not None and duration_label and spent_on:
            add_redmine_time_entry(
                base_url,
                api_key,
                issue_id,
                hours,
                f"autoagents: {sample_bn} — {duration_label}",
                spent_on=spent_on,
            )
            print(f"Posted time_entry {hours:.2f} h ({duration_label})")
        sys.exit(0)

    print("Unknown command", file=sys.stderr)
    sys.exit(1)
