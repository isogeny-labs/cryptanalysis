# Exact census of precommitted two-image lift candidates

The frozen 81-model grid contains **zero exact rational relations across all 22 public relation hits** in the selected-height experiment. This extends the earlier check of one height-minimizing lift per query to every rational model that the precommitted grid made available for those hits. The independent repeated-addition audit agrees on all 1,782 candidate and vector checks.

## Construction and measurement

`protocol.json` fixes the admission rule, source manifest digest, candidate policy, exact relation test, and failure treatment before the census. The input is the immutable `xedni-height-selected-two-image-20261116` run. Its query, vector, and 32 candidate ledgers are each checked against their compressed and uncompressed SHA-256 digests. All 22 rows with a public relation enter the census. Each has 81 rational candidate models from shifts in `{−1,0,1}^4`; the equal-x exceptional query in the source has no admitted public relation.

For each candidate, the runner reconstructs two rational points and the unique nonsingular short Weierstrass model through them, verifies the recorded coefficients and point equations, and calculates `a P1 + b P2` by exact rational group arithmetic. The coefficients `(a,b)` and public points are those of the frozen relation row. The outcome ledger retains one row per candidate and vector. Arithmetic or ledger failures have their own status and cannot be counted as nonidentity results.

| Field prime | Public relation rows | Candidate checks | Exact rational relations | Failures |
| ---: | ---: | ---: | ---: | ---: |
| 313 | 1 | 81 | 0 | 0 |
| 421 | 3 | 243 | 0 | 0 |
| 431 | 1 | 81 | 0 | 0 |
| 547 | 6 | 486 | 0 | 0 |
| 593 | 3 | 243 | 0 | 0 |
| 617 | 6 | 486 | 0 | 0 |
| 677 | 2 | 162 | 0 | 0 |
| **Total** | **22** | **1,782** | **0** | **0** |

The result is a finite-grid statement for the specified public queries, coefficient family, and 81 precommitted shifts. A relation-dependent construction in `xedni-known-relation-lifts-20261118` supplies rational lifts for known coefficients; this census shows those witnesses are outside this fixed finite grid on these 22 rows. The next test is a precommitted wider grid or a public-only selection invariant whose cost and branch rules are fixed before relation screening.

## Replay

From this repository worktree:

```sh
python3 experiments/xedni-precommit-candidate-census-20261118/run.py
python3 experiments/xedni-precommit-candidate-census-20261118/audit.py
python3 experiments/xedni-height-selected-two-image-20261116/audit.py
```

`run.py` writes `result.json` and `outcomes.jsonl`; `audit.py` independently recomputes all outcomes by repeated addition. The source audit checks all 41,392 candidate records and all 6,656 original vector tests. No Sage job is used. The census is an exact arithmetic correctness experiment, not a calibrated wall-time comparison.
