#!/usr/bin/env bash
#
# Secret-leak gate. Scans the added lines of a diff for forbidden patterns.
#
# The pattern list is supplied via the GREP_GATE_PATTERNS env var, NOT hardcoded
# here, so this public file never enumerates the internal markers it guards
# against. In CI the value comes from the GREP_GATE_PATTERNS Actions secret;
# locally, export it from the maintainer's pattern source before running.
#
#   GREP_GATE_PATTERNS='pat1|pat2|...' bash scripts/grep-gate.sh [git-diff-range]
#
# Default range is origin/main...HEAD. Exit 1 (with the offending lines) on any hit.
set -euo pipefail

: "${GREP_GATE_PATTERNS:?GREP_GATE_PATTERNS is not set — export the maintainer pattern list}"
range="${1:-origin/main...HEAD}"

hits="$(git diff "$range" | grep -E '^\+' | grep -iE "$GREP_GATE_PATTERNS" || true)"
if [ -n "$hits" ]; then
  echo "✗ grep-gate BLOCKED — forbidden pattern in added lines:"
  echo "$hits"
  exit 1
fi
echo "✓ grep-gate clean ($range)"
