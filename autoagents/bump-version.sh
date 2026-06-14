#!/usr/bin/env bash
# Bump semver patch in autoagents/VERSION (MAJOR.MINOR.PATCH).
# Usage: bump-version.sh [label-for-log]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VF="${SCRIPT_DIR}/VERSION"
LABEL="${1:-}"

ver="1.0.0"
if [[ -f "$VF" ]]; then
  read -r ver < "$VF" || ver="1.0.0"
  ver="${ver//[[:space:]]/}"
fi
if [[ ! "$ver" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  ver="1.0.0"
fi

IFS=. read -r major minor patch <<< "$ver"
patch=$((patch + 1))
new="${major}.${minor}.${patch}"
printf '%s\n' "$new" > "$VF"

if [[ -n "$LABEL" ]]; then
  echo "autoagents VERSION ${ver} → ${new} (${LABEL})" >&2
else
  echo "autoagents VERSION ${ver} → ${new}" >&2
fi
printf '%s\n' "$new"
