# Result verification and formalization map

| Result | Lean declaration | Current verification |
| --- | --- | --- |
| p90917 is the first eligible 40-point class under the frozen v≥281 rule | None | Checked-Sage selector and independent Sage audit of the prescreen and class point data |
| Base-plus-direct rank 32 and full-source rank 35 over (F_{89}) | None | Independent Sage relation enumeration and finite-field matrix ranks; Lean matrix certificate remains open |
| All 40 source equations and 201 Hecke rows hold on the p90917 curve | None | Independent Sage curve-group replay; Lean concrete curve and source-map bridge remains open |
| Hecke support-size counts 1 at three and 200 at four | `DirectRankGate.support3_count`, `support4_count` | Exact audited support list; Lean kernel checked with no axioms |
| Residue-1 support counts 197 at two, three at zero, one at four | `DirectRankGate.mixed_residue_count`, `zero_residue_count`, `four_residue_count` | Exact audited supports and class residues; Lean kernel checked with no axioms |

The gate outcome is an empirical prospective validation on one class. To formalize the rank and group claims in Lean, the p90917 curve and 40 point constants, degree-13 source equations, 40-column relation matrices over (F_{89}), and checked row-echelon/rank certificates must be added. The feasible finite support composition has been formalized in `formal/DirectRankGate.lean`; the full curve and matrix bridge remains partial. Lean 4 `v4.35.0-rc4` is pinned in `formal/lean-toolchain`; `lake build` passes and `#print axioms` reports no axioms for the five declarations. `lean4checker --fresh` is unavailable here.
