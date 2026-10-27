# Short Hecke trace-sum counts match uniform group-sum controls in three frozen panels

The observed support-three cancellation counts at p=179, 223 and 317—**13, 20 and 76**—all lie inside the prespecified central 95% ranges from 4096 independent nonidentity-group panels per field. Their exact null means are approximately **19.88, 22.24 and 78.48**. This count comparison shows that the growing number of short cancellations in the 39-point conductor-four class does not, by itself, distinguish the Hecke source sums from ordinary small-group collision yield.

| Field p | Outside equations m | Group order N | Observed pair / null mean | Pair 95% range | Observed triple / null mean | Triple 95% range | Triple two-sided tail |
| ---: | ---: | ---: | ---: | --- | ---: | --- | ---: |
| 179 | 19 | 195 | 4 / 1.76 | 0–5 | 13 / 19.88 | 11–29 | 549/4097 ≈ 0.134 |
| 223 | 20 | 205 | 4 / 1.86 | 0–5 | 20 / 22.24 | 13–32 | 2670/4097 ≈ 0.652 |
| 317 | 34 | 305 | 4 / 3.69 | 1–8 | 76 / 78.48 | 62–96 | 3320/4097 ≈ 0.810 |

All observed support-one counts are zero, as specified by the nonidentity draw law. Pair-count two-sided tails are 400/4097, 466/4097 and 4097/4097 respectively. The exact means, interval order statistics, all **12,288 panel count rows**, and exact hash-bound observed counts are in [result.json](result.json). The null model draws auxiliary **group sums** independently with replacement from all nonidentity points of the same X_0(11)(F_p) group. It does not generate Hecke fibers or class rows, so the result evaluates cancellation *counts*, not the rank of the induced relation matrix.

For a finite group of order `N`, let `H=G\{0}`. With independent uniform draws from `H`, each fixed signed pair has one valid second value for every first value, giving probability `1/(N−1)`. For a fixed signed triple, the first two nonzero values have one group-law completion; it is disallowed only when the partial sum is zero, which occurs for exactly one second value per first value. Thus its probability is `(N−2)/(N−1)²`. Linearity of expectation gives:

```text
E[C_2] = 2·choose(m,2)/(N−1),
E[C_3] = 4·choose(m,3)·(N−2)/(N−1)².
```

These formulas require no independence between the overlapping support events. The pinned Lean [structural module](formal/NullCompletion.lean) proves existence and uniqueness of pair and triple completions in an abstract group and that a nonzero partial sum has a nonzero completion, without axioms. A finite-cardinality counting formalization of the displayed expectations remains open and is identified in the [proof map](formal/PROOF_MAP.json).

The [protocol](PROTOCOL.md) froze the three source receipts, 4096 panels per field, SHA-256 rejection-mapped draw stream, coefficient order, all-panel retention, exact expectation formulas, quantile indices and tail statistic before output. The pure-Python [producer](run.py) enumerated each actual finite-field group and saved every panel's support-one/two/three counts. The [independent checked-Sage replay](verify_sage.py) reconstructed all three groups with Sage's elliptic-curve implementation, regenerated every draw and used suffix-frequency counting instead of the producer's triple loop. It matched all 12,288 rows and every summary field; [validation.json](validation.json) records `PASS` and the checked [Sage runtime](sage-runtime-info.txt).

The group-sum control changes the next experiment: to test structure beyond ordinary collisions, a larger-class study should compare **independent rank gained per accepted row** and the cost of generating verified Hecke source equations against a matched generic relation source, using the same class points and resource accounting. The present null panels contain no class-row model, and the relation-stage receipts retain `candidate_id: null` and `target_online_ms: null`.

Reproduce from the repository root:

```sh
gtimeout 120 python3 experiments/hecke-trace-null-controls-20261027/run.py
./sage --runtime-info > experiments/hecke-trace-null-controls-20261027/sage-runtime-info.txt
gtimeout 180 ./sage -python experiments/hecke-trace-null-controls-20261027/verify_sage.py
cd experiments/hecke-trace-null-controls-20261027/formal
lake build NullCompletion
```
