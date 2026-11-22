# Degree-two Hecke obstruction on the 84-point p1009 X011 fiber

Every degree-two neighbor-x cubic on the preselected 84-point, absolute-trace-20 fiber over `F_1009` has exactly one rational root and an irreducible quadratic factor. Consequently the complete three-neighbor rational multiset needed for the frozen Hecke row policy is unavailable at all 84 sources. Exhaustive signed direct group-law relations of support at most three give 568 verified rows, of rank 83 over `QQ` and 82 over `F_17`. Adding the eligible degree-two Hecke rows leaves those ranks unchanged.

This is a complete result for this frozen fiber and row family. It identifies a precise rationality obstruction to the degree-two Hecke construction at a trace class selected before the run. The next experiment is a preselected trace class or Hecke degree with complete rational neighbor multisets, using the same closure and rank gates.

## Frozen instance and procedure

`protocol.json` was written before execution. The curve is `11a1: y²+y=x³−x²−10x−20` over `F_1009`, with group order 1020 and largest prime factor 17. The fiber is the 84 regular points with absolute Frobenius trace 20 in the corrected X011 census, sorted by affine `(x,y)`; the ledger digest is pinned in the protocol. The archived regularized Hecke implementation is also pinned by SHA-256. The corrected census includes the regular value `j(16,60)=−121` established in the earlier D=−1407 analysis.

For each source, the producer constructs the degree-two neighbor-x cubic. A row requires the full three-point rational multiset, containment in the frozen fiber, a verified group sum, and finite-j modular-polynomial checks. The run retains the source status and factor degrees even when the row gate fails. The direct control exhausts distinct supports one through three, fixes the first sign to `+1`, and enumerates all remaining signs. Each accepted relation is replayed in Sage before its row enters the matrix.

| Recorded result | Value |
| --- | ---: |
| Fiber points / source cubics | 84 / 84 |
| Cubic factor pattern `(1)(2)` | 84 |
| Eligible complete-rational Hecke rows | 0 |
| Direct signed relations, support 1 / 2 / 3 | 0 / 6 / 562 |
| Direct rank over `QQ` / `F_17` | 83 / 82 |
| Hecke plus direct rank over `QQ` / `F_17` | 83 / 82 |

The independent `audit_sage.py` rebuilt the regularized functions, rechecked each source against the corrected ledger, recomputed all 84 factorizations and all 568 direct rows with Sage's group law, and recomputed both matrix ranks. Its `audit.json` status is `PASS` and binds the producer result by digest. The audit additionally exports each cubic, its unique linear root, quadratic factor, and quadratic discriminant to `polynomial-certificates.json`; each discriminant was checked against every square in `F_1009`.

The producer's unisolated stage timings (`0.141 s` function build, `0.004 s` Hecke row scan, `0.522 s` direct enumeration, `0.041 s` matrix ranks) are execution diagnostics for this finite census. `candidate_id` and `target_online_ms` remain null in the result record because this is a rank experiment, not a complete IC candidate measurement.

## Formal certificate

`generate_formal.py` verifies the audit's certificate digest and generates `formal/P1009Degree2.lean` with all 84 cubic coefficient tuples. `X011P1009.each_cubic_has_one_root` checks by kernel reduction that every listed cubic has exactly one root among residues `0,...,1008`; `X011P1009.certificate_size` checks the list length. Both theorem axiom audits report no axioms. The formal result is an exact finite root-count theorem for the listed polynomials. The identification of those polynomials with the modular Hecke neighbor construction and the Sage matrix-rank calculation remain in the independently replayed computational layer; they are not Lean theorems.

## Reproduction

From this worktree, with the archived regularized source and corrected census present:

```sh
/Volumes/SSD990/cryptanalysis/sage --runtime-info > experiments/hecke-x011-p1009-degree2-rank-20261119/runtime-info.json
/Volumes/SSD990/cryptanalysis/sage -python experiments/hecke-x011-p1009-degree2-rank-20261119/run_sage.py
/Volumes/SSD990/cryptanalysis/sage -python experiments/hecke-x011-p1009-degree2-rank-20261119/audit_sage.py
python3 experiments/hecke-x011-p1009-degree2-rank-20261119/generate_formal.py
cd experiments/hecke-x011-p1009-degree2-rank-20261119/formal
lean P1009Degree2.lean
```

The recorded run used the checked repository Sage launcher and saved runtime information before starting the workload. `formal/lean-toolchain` pins Lean `v4.34.1`; this certificate uses Lean core and no external package. `lean4checker --fresh` was unavailable on the host. Raw direct rows, producer result, frozen post-run digest, audit output, polynomial certificates, and Lean build output are retained here.
