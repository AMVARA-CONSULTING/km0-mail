#!/usr/bin/env bash
# Pin commit author for this repo (repo-local only — does not touch global git config).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

git config --local user.name "Luipy56"
git config --local user.email "yoelberjaga@gmail.com"

echo "Git author for $(basename "$REPO_ROOT") (local):"
git config --local --get user.name
git config --local --get user.email
