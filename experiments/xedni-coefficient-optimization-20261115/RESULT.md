# Calibration-selected vectors improve early public coverage per abstract add

A target-independent 13-vector family selected on subgroup orders `751, 883, 983, 1103` covers **3,071** nonzero target scalars by query 35 across eight newly selected prime-order fields. The equal-size baseline from the earlier frozen family covers **2,144**. The selected family performs **58,111,478** abstract group-add calls across all target trials versus **47,710,392** for the baseline, giving **52.85 versus 44.94 hits per million charged add calls**, a **17.6%** group-only yield improvement. Both arms use the same public query schedule, target support, cap, and abstract accounting.

| Field `p` | Order `q` | Baseline hits | Selected hits | Baseline add calls | Selected add calls |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1531 | 1481 | 268 | 383 | 4,111,734 | 4,938,706 |
| 1669 | 1693 | 268 | 384 | 4,760,454 | 5,753,048 |
| 1811 | 1811 | 268 | 384 | 5,121,534 | 6,206,404 |
| 1877 | 1949 | 268 | 384 | 5,543,814 | 6,736,600 |
| 1979 | 1951 | 268 | 384 | 5,549,934 | 6,744,284 |
| 2339 | 2333 | 268 | 384 | 6,718,854 | 8,211,928 |
| 2693 | 2753 | 268 | 384 | 8,004,054 | 9,825,568 |
| 2711 | 2719 | 268 | 384 | 7,900,014 | 9,694,940 |

## Frozen selection and validation

`protocol.json` fixes the 45 primitive candidate vectors with `1≤a≤6`, `−6≤b≤6`, nonzero `b` and `a+b`, the greedy 13-round union-coverage objective at offsets `1..34`, four calibration orders, and lexicographic tie breaking. The selected test order is:

`(1,-6)`, `(2,-1)`, `(6,5)`, `(5,4)`, `(6,1)`, `(5,3)`, `(4,-5)`, `(6,-1)`, `(5,-1)`, `(6,-5)`, `(1,5)`, `(4,-1)`, `(4,1)`.

The field selector scanned prime `p` from 1501 upward and retained the first eight for which `E/F_p: y²=x³−x−2` has prime order and `G=(2,2)` generates it. It checked **156 prime candidates** to select eight fields. Selection finished from calibration orders before the field selector ran; the selected vectors, source digests, all checked primes, and selected fields are retained. Every nonzero scalar `d∈{1,…,q−1}` in each field is a target trial. The public search uses `Q=dG` as a fixture point, tests the first lexicographic row through query 35, and records hit or cap for both arms.

The producer retains one raw record per target and arm, including first hit, tested vectors, and abstract add-call count. It charges each lazy `Q−tG` advance and all calls inside both coefficient multiplications and combination; fixture construction and independent scalar replay are separate. The checked Sage audit reconstructs the greedy selection and the full prime scan, checks every target record against an independent inverse-map formula and cost calculation, and replays every hit as an elliptic-curve group relation. All eight field rows and all target records pass. The selected vectors have larger coefficients, so the extra coverage carries a larger per-test add cost.

The imported checked `FiniteFamilyCoverage` theorem still bounds either fixed 13-vector family by `13×34=442` target scalars at this cap; the selected arm reaches 383–384 per field, the baseline 268. The new Lean module checks the selected integer family has 13 distinct effective vectors and proves that reduction into any field yields at most 13 vectors, hence target coverage at most 13 times the number of offsets. `PROOF_MAP.md` records the exact implication and its checked Sage bridge. The pinned build completed 3,139 jobs, and all four new `#print axioms` outputs use only standard Lean foundations.

This is an algorithmic gain in a group-only control, conditional on target-independent vectors. Rational-lift discovery, curve selection, rank, and matched same-target rho were not part of these charged abstract operations. The next decisive test must attempt rational realization for the selected vectors and charge every failed lift and curve candidate before any end-to-end comparison.

Reproduce with `python3 experiments/xedni-coefficient-optimization-20261115/select_family.py`, `./sage --runtime-info`, `./sage -python experiments/xedni-coefficient-optimization-20261115/select_fields.py`, `python3 experiments/xedni-coefficient-optimization-20261115/run.py`, `./sage -python experiments/xedni-coefficient-optimization-20261115/audit.py`, `(cd experiments/xedni-coefficient-optimization-20261115/formal && lake build CoefficientOptimization)`, and `python3 experiments/xedni-coefficient-optimization-20261115/verify.py`.
