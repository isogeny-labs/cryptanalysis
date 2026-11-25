# Degree-three Hecke rows complete the rational rank on the p1009 X011 fiber

On the frozen 84-point absolute-trace-20 X011 fiber over `F_1009`, degree-three Hecke construction produces 28 complete, rational, class-closed four-neighbor rows. Together with the 568 independently replayed signed direct relations of support at most three, these rows raise the rational matrix rank from 83 to **84**, the full 84 columns. Over `F_17` they raise rank from 82 to **83**. The remaining one-dimensional mod-17 null direction is the explicit order-17 subgroup projection of the points.

This experiment changes only the Hecke degree from the preceding degree-two result. The earlier 84 degree-two cubics had factor pattern `(1)(2)` and supplied no complete-rational rows. Here 28 quartics split as `(1)(1)(1)(1)` and their reconstructed neighbor multisets are wholly inside the frozen fiber; 56 factor as `(1)(3)` and retain `INCOMPLETE_RATIONAL_NEIGHBORS` status. The contrast identifies degree three as a usable relation source for this exact trace class.

## Frozen instance and method

`protocol.json` and its digest in `pre-run.json` were saved before execution. They pin the 11a1 curve `y²+y=x³−x²−10x−20`, `p=1009`, group order 1020, the 84 ordered regular points with absolute trace 20, the corrected census digest, the archived regularized Hecke source digest, the degree-three row rule, and the previous direct-row artifact digest. The largest prime factor of the group order is 17. `candidate_id` and `target_online_ms` remain null because this is an exact relation-rank experiment.

For each source, `run_sage.py` records all five quartic coefficients, factor degrees, rational-root count, and row status. A row enters the matrix only after unique reconstruction of all four rational neighbors, frozen-fiber membership, the Hecke group sum, and finite-j modular-polynomial checks. It reloads all 568 direct rows from the preceding experiment, checks their digest and point order, and replays each group-law identity. `result.json` and the row archive were frozen by digest before the independent audit.

| Row family | Count | Rank over `QQ` | Rank over `F_17` |
| --- | ---: | ---: | ---: |
| Signed direct, support 1–3 | 568 | 83 | 82 |
| Eligible degree-three Hecke | 28 | 28 | 28 |
| Combined | 596 | **84** | **83** |

The independent `audit_sage.py` rebuilds the Hecke functions and computes each quartic from closed-form Newton identities rather than calling the producer's recursive polynomial routine. For every complete-rational source it rechecks all x and xy moments, group sum, modular polynomial, fiber membership, and row coefficients. It recomputes the three ranks over both fields; `audit.json` records `PASS` and binds the producer result by SHA-256.

The audit also records two concrete rank witnesses. `rank-witness.json` contains the direct matrix's one-dimensional rational null vector, with 0/1 entries. Every direct row annihilates it, while the degree-three row at source index 2 has dot product 5, explaining the rational rank gain. `projection.json` contains the nonzero vector `v_i = log_S(60 P_i) mod 17`, where `S` is a recorded point of order 17. Every combined relation annihilates this vector, giving the upper bound 83 over `F_17`; the independently recomputed rank attains it.

The unisolated function-build, degree-three scan, and matrix-rank times in `result.json` are diagnostics for this finite census. They do not enter a single-target IC timing comparison.

## Formal checks and proof boundary

`formal/Degree3RootCounts.lean` pins the 84 quartics and proves each exact finite-field root count by kernel reduction: 56 have one rational root and 28 have four. `formal/ProjectionKernel.lean` pins all 596 sparse rows and checks the mod-17 projection null vector, the rational direct-row null vector, and the degree-three witness dot product 5. The pinned Lean build succeeds; `#print axioms` reports no axioms for the root-count declarations and only standard `propext` for the list-wide row checks.

The Hecke implementation-to-coefficient bridge, point-group projection, and matrix-rank computations are independently checked in Sage. The Lean modules certify the finite arithmetic statements recorded in the [proof map](formal/PROOF_MAP.md); a formal rank theorem over the actual elliptic-curve points remains a separate proof step.

## Reproduction

From this worktree, with the archived Hecke source and corrected census available:

```sh
/Volumes/SSD990/cryptanalysis/sage --runtime-info > experiments/hecke-x011-p1009-degree3-rank-20261119/runtime-info.json
/Volumes/SSD990/cryptanalysis/sage -python experiments/hecke-x011-p1009-degree3-rank-20261119/run_sage.py
/Volumes/SSD990/cryptanalysis/sage -python experiments/hecke-x011-p1009-degree3-rank-20261119/audit_sage.py
python3 experiments/hecke-x011-p1009-degree3-rank-20261119/generate_formal.py
python3 experiments/hecke-x011-p1009-degree3-rank-20261119/generate_projection_formal.py
cd experiments/hecke-x011-p1009-degree3-rank-20261119/formal
lean Degree3RootCounts.lean
lean ProjectionKernel.lean
```

The run saved checked-Sage runtime information before its workload. `formal/lean-toolchain` pins Lean `v4.34.1` with no external dependency. `lean4checker --fresh` was unavailable on this host. The protocol, runtime, complete source statuses, row archive, audit, rank witnesses, Lean sources, and build outputs are retained in this directory.
