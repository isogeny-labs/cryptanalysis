# Degree-two Hecke rows complete rational rank on the p941 trace-18 fiber

The preselected largest regular X011 fiber over `F_941` has 112 points at absolute trace 18. Degree-two Hecke construction gives **56 complete, rational, class-closed rows**. Added to 1,529 exhaustive signed direct relations of support at most three, they raise rational matrix rank from 111 to **112**, the full column count. Degree three gives no complete rational neighbor multiset on this fiber. This reverses the useful degree in the p1009 trace-20 experiment, where degree three supplied the rank-gaining rows.

The exact polynomial split determines the opportunity: 56 degree-two cubics split as `(1)(1)(1)` and their reconstructed neighbors stay within the frozen fiber; the other 56 split as `(1)(2)`. Every degree-three quartic splits as `(1)(1)(2)`, with two rational roots and an irreducible quadratic factor. The row rule therefore retains all 112 degree-three sources as `INCOMPLETE_RATIONAL_NEIGHBORS`.

## Frozen inputs and checks

`protocol.json` and `pre-run.json` fixed the p941 field, 11a1 model `y²+y=x³−x²−10x−20`, curve group order 900, the census-selected 112-point trace-18 fiber, corrected ledger and regularized Hecke source digests, degrees two and three, row acceptance gates, direct signed-control enumeration, rank fields, and the resource cap before execution. The points are ordered by affine `(x,y)`. This is a rank experiment, so the result records `candidate_id: null` and `target_online_ms: null`.

| Row family | Rows | Rank `QQ` | Rank `F_2` | Rank `F_3` | Rank `F_5` |
| --- | ---: | ---: | ---: | ---: | ---: |
| Signed direct, support 1–3 | 1,529 | 111 | 110 | 110 | 110 |
| Degree-two Hecke | 56 | 56 | 56 | 56 | 56 |
| Degree-three Hecke | 0 | 0 | 0 | 0 | 0 |
| Degree-two plus direct | 1,585 | **112** | **111** | **111** | **110** |

The producer retains all polynomial coefficients, factor patterns, root counts, and source statuses. It accepts a Hecke row only when it uniquely reconstructs the full rational neighbor multiset, checks the Hecke group sum and finite-j modular polynomial, confirms frozen-fiber membership, and replays the resulting point-group identity. It exhausts distinct signed direct supports one through three, with the first sign fixed `+1` and every remaining sign enumerated; the saved counts are 0, 9, and 1,520 respectively.

The independently run `audit_sage.py` rebuilt the functions, reconstructed every cubic and quartic from closed-form Newton identities, rechecked the complete neighbor x and xy moments and row gates, and re-enumerated direct relations using a Sage point-pair lookup rather than the producer's triple loop. It reproduced every saved row and all ranks; `audit.json` reports `PASS` and binds the frozen producer result by digest.

## Formal root certificate

`formal/Degree2Roots.lean` proves the exact root count of each of the 112 listed cubics over all residues modulo 941: 56 have one root and 56 have three. `formal/Degree3Roots.lean` proves each of the 112 listed quartics has exactly two roots. Both pinned builds pass and `#print axioms` reports no axioms. The Lean finite-root statements are bound to the audited coefficient lists through `generate_formal.py`. The modular Hecke construction-to-coefficient bridge and exact matrix ranks remain in the independent Sage replay; the proof map names those open formal obligations.

The unisolated function-build, source-scan, direct-enumeration, and matrix-rank times in `result.json` are finite-census diagnostics. The next experiment is a separately frozen integer-lattice index confirmation, prompted by a read-only Smith diagnostic on these fixed rows.

## Reproduction

From this worktree, with the corrected census and archived regularized Hecke source present:

```sh
/Volumes/SSD990/cryptanalysis/sage --runtime-info > experiments/hecke-x011-p941-trace18-hecke-rank-20261119/runtime-info.json
/Volumes/SSD990/cryptanalysis/sage -python experiments/hecke-x011-p941-trace18-hecke-rank-20261119/run_sage.py
/Volumes/SSD990/cryptanalysis/sage -python experiments/hecke-x011-p941-trace18-hecke-rank-20261119/audit_sage.py
python3 experiments/hecke-x011-p941-trace18-hecke-rank-20261119/generate_formal.py
cd experiments/hecke-x011-p941-trace18-hecke-rank-20261119/formal
lean Degree2Roots.lean
lean Degree3Roots.lean
```

The checked Sage runtime receipt was saved before the workload. `formal/lean-toolchain` pins Lean `v4.34.1` and the modules use no external package. `lean4checker --fresh` was unavailable on the host. The protocol, full source records, row archives, independent replay, Lean modules, and build outputs are retained here.
