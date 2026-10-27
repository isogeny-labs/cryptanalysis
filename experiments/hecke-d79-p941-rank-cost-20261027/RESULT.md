# Direct triples and Hecke traces both fill the p941 F5 relation kernel

At the frozen (D_K=-79, f=4, p=941) holdout, **55 verified direct three-point relations** and **30 verified short Hecke trace cancellations** each raise their respective base-row systems to **rank 38 over F5**. Both complete systems have rank **40 over Q**. The independent Sage audit found (E_{11a1}(mathbb F_{941})\cong\mathbb Z/5\times\mathbb Z/180); two independent class-point F5 coordinate constraints and explicit invertible 38×38 minors show that rank 38 fills the available F5 relation kernel for this 40-point class.

The frozen class-size prediction was **39**. The producer and independent exhaustive audit found **40** rational class points: conductor strata (f=1,2,4) contribute **10, 10, 20** points, compared with the earlier p317 strata **10, 9, 20**. All **40** degree-13 neighbor polynomials had the predicted simple factor pattern `(1)(1)(12)`. The p941 ambient group order is **900**, and the largest prime factor is **5**, changing the subgroup geometry from p317's order 305 and q=61. The class-size discrepancy and changed modulus are part of this holdout result.

| p941 row source | Candidate rows | Rank over F5 alone | Rank over F5 with base | Rank over Q with base | Greedy rows added |
| --- | ---: | ---: | ---: | ---: | ---: |
| Direct signed class-point support ≤3 | 55, all support 3 | 37 | 38 from base 20 | 40 | 18 |
| Hecke: 4 class-closed plus 30 short cancellations | 4 + 30; cancellation counts 3 pairs, 27 triples | — | 38 from base 20 | 40 | 4 closed + 14 short |
| Both sources together | 89 | — | 38 | 40 | — |

The [analysis receipt](analysis.json) retains every candidate, exact signed row, selected indices and rank path. Its uniform nonidentity-group expectation is `35488960/808201` (about 43.91) direct triples and `25646880/808201` (about 31.73) Hecke outside-trace triples. Those are count baselines; no tail test was frozen for this new prime.

## Exploratory phase costs

The checked-Sage Hecke producer's measured interval begins after source-digest verification and excludes launcher startup. It records **37.932 s** for Hecke function/source construction and curve-order setup, **0.0348 s** for the class walk, **0.0284 s** for base rows, **1.152 s** for degree-13 fibers and **0.00173 s** for equal-trace pairs: **39.149 s** in total, with **1,398.75 MiB** peak RSS. The [raw producer receipt](result.json) contains nanosecond phase values and every fiber status.

With the completed class and outside-trace sources supplied as ready inputs, five alternating-order local Python enumerations measured direct search at **56.85–65.14 ms** (median **59.62 ms**) and Hecke short-cancellation search at **115.64–144.94 ms** (median **126.07 ms**). Each arm retained all signed trials and verified rows in [analysis.json](analysis.json). Direct search used 41,120 trial sign patterns; Hecke search used 29,856. The source preparation needed to obtain those ready inputs differs between arms, and this [local envelope](environment.json) has neither exclusive CPU affinity nor locked frequency. These are exploratory stage costs, with verification and rank analysis timed separately, rather than a qualified end-to-end speed comparison.

The original analysis attempt failed from a local name shadowing error before writing a result. Its [stderr](analysis-attempt1-stderr.txt) is retained; the corrected producer completed, and all five repetitions yielded identical candidate lists.

## Verification and proof boundary

The [protocol](PROTOCOL.md) froze the prime, class-size prediction, factor pattern, source digest, cap, phase boundaries and relation ordering before producer output. The [postproducer input](post_inputs.json) pins the completed class receipt before relation search. The [independent checked-Sage audit](audit_sage.py) exhaustively scanned all 900 curve points for the trace-selected class, checked the three conductor strata, refactored all 40 degree-13 neighbor polynomials, verified every base/class/trace row by point addition, re-enumerated all 55 direct and 30 Hecke rows, and recomputed every reported matrix rank. It records `PASS` in [audit.json](audit.json), with the checked [Sage runtime](sage-runtime-info.txt).

For either complete 40-column matrix, the [pinned Lean certificate](formal/RankP941.lean) checks two independent F5 right-kernel vectors and an explicit 38×38 inverse modulo 5. Thus its F5 rank is at most and at least 38. An explicit 40×40 inverse modulo 7 gives a nonzero integer determinant and rank 40 over Q. The module checks the finite arithmetic with no research axioms; `#print axioms` reports only standard `propext` for the finite list equality and inverse facts. The abstract rank implications and the bridge from the Sage point identities to the generated matrices remain open in the [proof map](formal/PROOF_MAP.json), with the written argument here.

This is a relation-stage result with `candidate_id: null` and `target_online_ms: null`. The next discriminating run should use a prime and class with a larger q-primary subgroup, frozen before output, and measure source construction, verified useful rank and target handling under an auditable benchmark tier.

Reproduce from the repository root:

```sh
./sage --runtime-info > experiments/hecke-d79-p941-rank-cost-20261027/sage-runtime-info.txt
gtimeout 900 ./sage -python experiments/hecke-d79-p941-rank-cost-20261027/run.py
gtimeout 120 python3 experiments/hecke-d79-p941-rank-cost-20261027/analyze.py
gtimeout 240 ./sage -python experiments/hecke-d79-p941-rank-cost-20261027/audit_sage.py
python3 experiments/hecke-d79-p941-rank-cost-20261027/formal/generate.py
cd experiments/hecke-d79-p941-rank-cost-20261027/formal
lake build RankP941
```
