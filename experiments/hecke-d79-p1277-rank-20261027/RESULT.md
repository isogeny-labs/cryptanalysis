# An order-five coset obstruction removes direct triples while Hecke traces fill the p1277 F53 relation kernel

At the frozen (D_K=-79, f=4, p=1277) holdout, the **40 class points** produce **zero signed three-point relations** and only **two signed pair relations**. Their rank with the 20 base rows is **22 over F53**. The degree-13 Hecke source has **40 outside-class trace equations**; short signed combinations yield **2 pair and 27 triple relations**, raising the *same* base system to **rank 39 over F53** and **40 over Q**. The independently audited curve group is cyclic of order (1325=5²\cdot53), so rank 39 is the full F53 relation-kernel dimension for its nonzero class-point 53-coordinate map.

| Frozen p1277 source | Verified support-1 / pair / triple rows | Rank F53 alone | Rank F53 with 20 base rows | Rank Q with base | Greedy rows added |
| --- | ---: | ---: | ---: | ---: | ---: |
| Direct class-point sums | 0 / 2 / 0 | 2 | 22 | 22 | 2 |
| Hecke outside-trace cancellations | 0 / 2 / 27 | — | 39 | 40 | 19 |
| Both sources | 31 total short rows | — | 39 | 40 | — |

All **40** rational class points and the predicted degree-13 factor pattern `(1)(1)(6)(6)` matched the [frozen protocol](PROTOCOL.md). The conductor (f=1,2,4) strata contribute **10, 10, 20** rational points. Every degree-13 equation has outside-class traces: **8** have one trace and **32** have two. There are no class-closed rows or equal-trace pairs. [result.json](result.json) retains every fiber, orbit, trace, modular-polynomial/cusp check and base row; [analysis.json](analysis.json) retains every short candidate and rank path.

## Why direct triples vanish

The independent Sage audit multiplies each class point by (265=1325/5), projecting the cyclic group onto its order-five quotient. With (T=265P_0=(5,5)), **20** class points project to (T) and **20** to (-T=4T). Any signed term from this class still projects to (\pm T). A sum of three such terms projects to one of (\pm T,\pm3T), all nonzero because (T) has order five. Therefore a signed three-point identity among these class points is structurally impossible, regardless of the 41,120 candidate sign patterns enumerated.

The aggregate outside Hecke trace sums project to (T,2T,3T,4T) with counts **4, 16, 16, 4**. Their (\pm2T) terms allow three-source projection cancellations such as (2T-T-T=0); exact point addition independently verifies the 27 observed triple relations. The frozen uniform-nonidentity group-sum mean for 40 sources was `3267810/109561` (about **29.83**) support-three cancellations. The direct zero is explained by the class's order-five coset structure, so that iid count model is unsuitable for these class points.

The pinned Lean [projection theorem](formal/ProjectionP1277.lean) proves the structural implication for any map into `Fin 5` preserving addition: three terms whose images are 1 or 4 cannot sum to zero. The [matrix certificate](formal/RankP1277.lean) checks an invertible 22×22 direct-row minor modulo 53; for the Hecke system it checks a nonzero F53 right-kernel vector, an invertible 39×39 minor modulo 53, and an invertible 40×40 minor modulo 3. The written rank argument follows: the direct matrix has exactly 22 rows and rank at least 22; the Hecke kernel bounds rank by 39 and its minor attains 39; its mod-3 minor has nonzero integer determinant, giving rank 40 over Q. `#print axioms` reports only standard `propext` where used. The [proof map](formal/PROOF_MAP.json) identifies the remaining Lean bridge from audited curve points to the numerical matrices and the generic matrix-rank implications.

## Stage costs and verification

The checked-Sage producer's measured interval begins after source-digest verification and excludes launcher startup. Its exploratory local-host phase times were **36.929 s** source/function build and curve-order setup, **0.0568 s** class walk, **0.0403 s** base rows, **1.204 s** degree-13 fibers and **0.000845 s** pair rows: **38.231 s** total, with **1,350.55 MiB** peak RSS. Five alternating-order ready-input Python searches recorded direct enumeration at **68.65–78.84 ms** (median **72.98 ms**) and Hecke trace-combination enumeration at **273.18–315.28 ms** (median **290.57 ms**). The arms differ in source preparation and per-source trace count; the [local envelope](environment.json) has no exclusive affinity or locked frequency. These are exploratory stage costs, not a qualified online timing comparison.

The [independent checked-Sage audit](audit_sage.py) scanned all 1,325 curve points for the trace-selected class, checked the conductor strata, refactored all 40 degree-13 polynomials, verified every base and outside-trace equation, re-enumerated every direct and Hecke short candidate, and recomputed all ranks. It records `PASS` and exact order-five projection counts in [audit.json](audit.json). The [Sage runtime](sage-runtime-info.txt), raw producer and analysis logs, pinned source hashes and Lean build output remain in this directory. `candidate_id` and `target_online_ms` remain null: the result is relation-stage geometry, with no target-dependent interval measured.

The next experiment should test whether an order-five coset obstruction is predictable from the class construction across more primes and conductors, then measure complete source-generation cost and useful rank on a dedicated benchmark allocation.

Reproduce from the repository root:

```sh
./sage --runtime-info > experiments/hecke-d79-p1277-rank-20261027/sage-runtime-info.txt
gtimeout 900 ./sage -python experiments/hecke-d79-p1277-rank-20261027/run.py
gtimeout 120 python3 experiments/hecke-d79-p1277-rank-20261027/analyze.py
gtimeout 240 ./sage -python experiments/hecke-d79-p1277-rank-20261027/audit_sage.py
python3 experiments/hecke-d79-p1277-rank-20261027/formal/generate.py
cd experiments/hecke-d79-p1277-rank-20261027/formal
lake build ProjectionP1277 RankP1277
```
