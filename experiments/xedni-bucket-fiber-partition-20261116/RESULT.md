# Exact visible-prefix bucket mass

The actual live and first-hit sets of a finite label-adaptive add/sub
program now have checked Lean cardinality formulas. At any stage `k ≥ 2`,
`execution_live_card_eq_bucket_mass` partitions live scalar-and-encoding
executions by their visible length-`k` label tuple and counts the exact
encoding fiber for each eligible scalar. For `k < m`,
`execution_hit_card_eq_bucket_mass` gives the corresponding first-hit count
using eligible next-candidate scalars and the same visible prefix bucket.

The key causal lemma states that the affine form created at position `i`
depends only on labels before `i`. Consequently the next form used in the
first-hit predicate is fixed by the old visible bucket, regardless of its
unseen suffix labels. The counting lemma partitions each accepted execution
uniquely by `(bucket, scalar)` and counts its encoding fiber. These are
structural identities for every finite typed program under the stated
field, group, encoding-finiteness, and generator-injectivity hypotheses.

The frozen `Z/7Z` control enumerated all seven scalars, all 5,040 bijective
encodings, and every proposed label tuple at prefix lengths 2 through 5.
It checked 137,200 `(prefix length, scalar, tuple)` cells: 8,617 positive
fibers and 128,583 zero fibers. Direct execution counts matched the
eligible-fiber and eligible-next-candidate-fiber predictions in every cell.

| Prefix length | Total encoding mass | Live mass | First-hit mass |
| ---: | ---: | ---: | ---: |
| 2 | 35,280 | 30,240 | 7,560 |
| 3 | 35,280 | 22,680 | 2,520 |
| 4 | 35,280 | 20,160 | 0 |
| 5 | 35,280 | 20,160 | 7,560 |

`bucketMass` counts encodings of group elements. The next proof step is a
group-fiber version of the weighted next-candidate inequality, followed by
its substitution into the existing aggregate stage bound. A coordinate-led
construction still needs a separate operation and information model.

Reproduce the finite control with `python3 run.py`; build the proof from
`formal/` with `lake build BucketFiberPartition`. The census is an
algorithmic check, not a CPU timing comparison.
