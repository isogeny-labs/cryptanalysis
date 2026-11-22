# Vector-aware leading-defect selection deepens ten fresh residuals

On a frozen fresh-target panel, selecting a rational lift by the *known public relation vector's* first-order cancellation changed 10 of 11 model choices and made all 10 exact residuals deeper. The remaining hit had no cancellation candidate in the 625-model family, so the policy retained the baseline model. The exact rational relation check found 20 depth-two candidates among 6,875 lifts; the vector-aware policy selected a depth-two candidate on each hit where one existed. [Independent modular-Jacobian and exact-rational replay](audit.py) passed every row. Search and validation costs are recorded separately.

## Frozen selection and measurements

The [protocol](protocol.json) pins the earlier field/subgroup and query construction, then uses a new target seed label `xedni-vector-aware-v1|p|j` for 32 targets. There are 512 public queries and 6,656 predeclared short-vector tests. Eleven public relation hits each enter a 625-model centered coordinate-shift family. No equal-x exception occurred.

For each public-hit vector `(a,b)`, the producer constructs all candidate models and computes `[q]P1`, `[q]P2` over `Qp(p, prec=8)`. Let `ci` be the leading residue of their formal parameters divided by `p`. The policy selects the smallest model among those satisfying `a*c1+b*c2=0 mod p`, with lexicographic tie breaking; if no such candidate exists, it selects the minimum-model baseline. It evaluates exact rational residuals only after these choices are fixed. A coefficient-independent family-wide policy from the preceding experiment is replayed on the same frozen hits as a secondary comparator.

| Recorded item | Result |
| --- | ---: |
| Fresh targets / public queries / vector tests | 32 / 512 / 6,656 |
| Public hits / candidate models | 11 / 6,875 |
| Candidate / q-multiple / rational checks | 6,875 / 13,750 / 6,875 passed |
| Candidate or leading-prediction failures | 0 |
| Exact residual depth one / two | 6,855 / 20 candidates |
| Minimum-model selected depth two | 0 / 11 hits |
| Family-wide selected depth two | 1 / 11 hits |
| Vector-aware selected depth two | 10 / 11 hits |
| Vector-aware choices changed / improved / worsened | 10 / 10 / 0 hits |
| Hits without a cancellation candidate | 1 / 11 |
| Exact rational relations | 0 |

The independent audit reconstructs all 32 targets, every query and finite relation, each rational curve and point, q-multiple leading residue modulo `p^8`, and every exact rational residual using Python `Fraction` arithmetic. It confirms all 6,875 cancellation predictions and the selection rule; its [receipt](audit.json) is `PASS`. The [result manifest](run-result.json) indexes all compressed raw rows, including the 20 predicted depth-two candidates and all attempts.

The checked-Sage script took 17.46 seconds on an ordinary host. Exclusive stage timers record 0.128 seconds for candidate construction, 9.777 seconds for the 6,875 q-multiple proxy evaluations, and 6.769 seconds for *all* rational diagnostic checks. Within the last stage, selected-point checks sum to 0.0056 seconds and baseline checks to 0.0075 seconds; these are subsets of the diagnostic stage and are not added to it. Search cost dominates a selected check. The [runtime receipt](sage-runtime.json) was saved before the run. These component timings are not a same-target online IC/rho comparison.

## Proof map and next step

The selection rule uses the first graded additive law of the elliptic formal group. The parent [Lean proof](../xedni-leading-defect-selector-20261116/formal/LeadingDefect.lean) checks the linear-combination and kernel-cancellation consequences for an explicitly assumed additive leading map over arbitrary integer coefficients. Its build and axiom audit are in the parent experiment. The construction of that map from the elliptic reduction-kernel filtration remains open in Lean. This experiment adds an algorithm and new measurements; it does not revise the mathematical theorem.

The next test should enlarge or adapt the lift family on the one hit with no cancellation candidate, while charging that extra search and independently checking the rational residual. An end-to-end IC comparison would additionally require a complete target-recovery pipeline and matched same-point rho under a frozen resource envelope. Run `python3 verify.py` to check the seal and replay the audit. Local Sage reruns use `/Volumes/SSD990/cryptanalysis/sage --runtime-info` before `/Volumes/SSD990/cryptanalysis/sage -python /absolute/path/to/run.py`.
