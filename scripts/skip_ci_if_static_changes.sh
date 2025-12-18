#!/usr/bin/env bash
# Append [ci skip] to the last commit message if all changed files are static-only.
# Usage: run this before `git push`; you can also install the pre-push hook using
# `scripts/install-git-hook.sh` to run it automatically.
set -euo pipefail

# Make sure we have a reference to compare against
git fetch origin main >/dev/null 2>&1 || true

# Find changed files in current branch vs origin/main (if available), otherwise against last commit
CHANGED=$(git diff --name-only --cached)
if [ -z "$CHANGED" ]; then
  # staged empty; check commits since origin/main
  if git rev-parse --verify origin/main >/dev/null 2>&1; then
    CHANGED=$(git diff --name-only origin/main...HEAD)
  else
    CHANGED=$(git diff --name-only HEAD~1..HEAD 2>/dev/null || true)
  fi
fi

if [ -z "$CHANGED" ]; then
  echo "No changed files detected; nothing to do."
  exit 0
fi

# Patterns that we consider "static-only" changes
STATIC_PATTERNS='^(static/|core/static/|staticfiles/|.*\.png$|.*\.svg$|.*\.json$|service-worker\.js$|manifest\.json$)'

# If any changed file does NOT match the static patterns, skip
for f in $CHANGED; do
  if ! echo "$f" | egrep -q "$STATIC_PATTERNS"; then
    echo "Non-static change detected: $f"
    echo "Not adding [ci skip]."
    exit 0
  fi
done

# All changed files are static-only, amend last commit message to include [ci skip]
LAST_MSG=$(git log -1 --pretty=%B)
if echo "$LAST_MSG" | grep -q '\[ci skip\]'; then
  echo "Last commit message already contains [ci skip]."
  exit 0
fi

echo "All changes are static-only → appending [ci skip] to last commit message."

git commit --amend -m "$LAST_MSG [ci skip]"

echo "Amended last commit with [ci skip]. Remember to push: git push --force-with-lease origin $(git rev-parse --abbrev-ref HEAD)"
exit 0
