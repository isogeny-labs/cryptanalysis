#!/usr/bin/env bash
# Check the Lean development with the pinned toolchain and record the receipt.
# Usage: formal/check.sh [path-to-lean-binary]
set -euo pipefail
cd "$(dirname "$0")"
LEAN="${1:-lean}"
{
  echo "# Lean check receipt"
  echo "date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "toolchain (lean-toolchain): $(cat lean-toolchain)"
  echo "lean --version: $("$LEAN" --version)"
  echo "sha256 BasePointIndependence.lean: $(sha256sum BasePointIndependence.lean | cut -d' ' -f1)"
  echo "command: lean BasePointIndependence.lean"
  echo "--- output (every '#print axioms' line; an unfinished proof would list the sorry axiom here) ---"
  "$LEAN" BasePointIndependence.lean
  echo "--- exit: $? ---"
} | tee RECEIPT.txt
if grep "depends on axioms" RECEIPT.txt | grep -q sorryAx; then echo "sorryAx found" >&2; exit 1; fi
