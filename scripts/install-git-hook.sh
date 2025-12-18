#!/usr/bin/env bash
# Install the included pre-push hook into .git/hooks (for local developers)
set -euo pipefail
HOOK_SRC="$(pwd)/scripts/git-hooks/pre-push"
HOOK_DEST="$(pwd)/.git/hooks/pre-push"

if [ ! -d ".git" ]; then
  echo "This repository doesn't look like a Git repo (no .git directory). Run from repo root." >&2
  exit 1
fi

mkdir -p "$(pwd)/.git/hooks"
cp -f "$HOOK_SRC" "$HOOK_DEST"
chmod +x "$HOOK_DEST"

echo "Installed pre-push hook to .git/hooks/pre-push"

echo "To remove: rm .git/hooks/pre-push"
