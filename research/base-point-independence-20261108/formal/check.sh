#!/usr/bin/env bash
# Build the dependency-free Lake project with the pinned toolchain and record
# the receipt. Usage: formal/check.sh   (lean and lake on PATH, elan or a
# release archive of leanprover/lean4:v4.34.1)
set -euo pipefail
cd "$(dirname "$0")"
SRC=BasePointIndependence/Core.lean
{
  echo "# Lean check receipt"
  echo "date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "toolchain (lean-toolchain): $(cat lean-toolchain)"
  echo "lean --version: $(lean --version)"
  echo "sha256 $SRC: $(sha256sum "$SRC" | cut -d' ' -f1)"
  echo "command: lake build && lake env lean $SRC"
  echo "--- output (every '#print axioms' line; an unfinished proof would list the sorry axiom here) ---"
  lake build >/dev/null
  lake env lean "$SRC"
  echo "--- exit: $? ---"
} | tee RECEIPT.txt
if grep "depends on axioms" RECEIPT.txt | grep -q sorryAx; then echo "sorryAx found" >&2; exit 1; fi
