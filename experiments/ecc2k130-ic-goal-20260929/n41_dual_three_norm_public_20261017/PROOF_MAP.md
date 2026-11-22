# Proof map

The construction uses two three-source reciprocal-coordinate norm equations and
one public-target Semaev-three equation. The Boolean witness control verifies
all generated clauses and XOR rows for an archived six-pair point relation.

| Statement | Proof or check | Exact scope |
| --- | --- | --- |
| Two exact three-pair point sums joined at the public point give a six-pair point relation | `DualThreeJoin.exact_halves_join`, `DualThreeJoin.lean` | Any additive commutative group, under the three stated point-equality hypotheses; kernel checked with no axioms |
| The nested norm encodes the product over eight source-root choices | `n41_three_code_nested_norm_20261015/PROOF_MAP.md` and its frozen finite-field replay | Algebraic construction and fixed-instance audit; the general norm-to-curve bridge remains open in Lean |
| Each half and public S3 constraint admits the archived six-pair point witness | `build_result.json`, `join_audit_result.json`, `verification.json` | One N41 public point; all 561,815 clauses and 27,153 native XOR rows checked on the witness assignment |
| An arbitrary satisfying Boolean model yields an exact six-pair point relation | Open | Recover source roots, choose signs, check distinct usable columns and replay all six points against the public point |

Toolchain: `leanprover/lean4:v4.34.1`. Build from this directory with
`lean DualThreeJoin.lean`; `lean_build.exit`, `lean_build.stdout`, and
`lean_build.stderr` preserve the command result and axiom audit. The checked
theorem is a structural implication only: S3 and the norm are coordinate
conditions, and their general bridge to exact curve points is not assumed in
the theorem.
