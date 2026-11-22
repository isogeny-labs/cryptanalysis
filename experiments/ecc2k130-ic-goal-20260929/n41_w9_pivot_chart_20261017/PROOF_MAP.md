# Pivot-chart decoder proof map

For the frozen N41 curve `EC1N41Ckb1h7d5e80d3c4d0`, let
`P : F₂⁸ → GF(2⁴¹)` map the eight final-pair code bits to the
rotated pair-product basis. At each intermediate reciprocal `w`, the
last-link resultant is

`L_w(P(code)) = q(w)`, where `L_w(p) = a(w)p² + b(w)p`.

For any eight output coordinates `J`, the eight-by-eight binary chart is
`π_J ∘ L_w ∘ P`. When it has rank eight, ordinary binary elimination
gives a left inverse `decode_J`. Thus a solution to the full 41-coordinate
equation has the unique code `decode_J(π_J(q))`; conversely that code is
a solution exactly when all 41 coordinates agree. This is a direct
linear-algebra implication with no distribution assumption. The seven
recorded charts cover all 284 source-positive `w` rows. Controls with no
invertible selected chart use a full-matrix pivot fallback.

| Result | Formal or computational check | Status |
| --- | --- | --- |
| Left inverse plus full syndrome is equivalent to the full equation | `PivotChart.decoded_iff_full_equation` | Lean checked, no axioms |
| Left inverse makes the projected code map injective | `PivotChart.projected_injective` | Lean checked, no axioms |
| Each of 284 rows has an invertible selected chart and the recorded code satisfies all 41 equations | `verify.py`, `verification.stdout` | Exact integer-field replay |
| Selected chart, fallback, and panel outcomes | `audit_sage.py`, `audit_result.json` | Independent checked-Sage replay using low-pivot elimination |

The formal theorem is polymorphic in code, output, and chart types. Its
`leftInverse` hypothesis corresponds to the finite rank-eight certificate
checked by `verify.py` on every listed positive row. The Lean module does
not encode the concrete 41-bit field, the seven chart matrices, or the
finite rank certificate. A full Lean formalization of those concrete
matrices remains open; the checked-Sage and exact integer replays audit
that bridge separately.

Toolchain: `leanprover/lean4:v4.34.1` in `lean-toolchain`.
`lean PivotChart.lean` completed successfully; `lean.stdout` contains
both `#print axioms` results. `lean4checker --fresh` was unavailable in
the current environment. `audit_protocol.json` hashes the Sage script,
selected result, input table, and checked launcher runtime receipt.
