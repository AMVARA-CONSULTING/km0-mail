"""Bump autoagents/VERSION patch (shared by loop shell and Python helpers)."""
from __future__ import annotations

import os
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def bump_version(label: str = "") -> str:
    script = os.path.join(SCRIPT_DIR, "bump-version.sh")
    args = [script]
    if label:
        args.append(label)
    proc = subprocess.run(
        args,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "bump-version.sh failed")
    return (proc.stdout.strip() or "").splitlines()[-1]


def read_version() -> str:
    path = os.path.join(SCRIPT_DIR, "VERSION")
    if not os.path.isfile(path):
        return "1.0.0"
    with open(path, encoding="utf-8") as f:
        return f.read().strip() or "1.0.0"
