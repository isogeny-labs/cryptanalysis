#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
lake build
actual=$(lake env lean AxiomAudit.lean)
expected=$(cat <<'AXIOMS'
'OrbitQuotient.mem_pairTotals_iff' depends on axioms: [propext, Quot.sound]
'OrbitQuotient.triple_matches_iff_pair_lookup' depends on axioms: [propext, Quot.sound]
AXIOMS
)
printf '%s\n' "$actual"
if [[ "$actual" != "$expected" ]]; then
  echo 'Lean axiom audit differs from the reviewed foundation set.' >&2
  exit 1
fi
