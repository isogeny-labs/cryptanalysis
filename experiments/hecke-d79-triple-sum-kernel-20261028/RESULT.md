# Exact-order signed triple-sum kernel for D79 support-eight collection

Caching signed triple sums and current-source signed pairs reduced counted elliptic-curve group additions by **46,725,801 across eight fresh paired classes**, from 95,847,008 for the pair-sum kernel to 49,121,207 (**48.75%**). Every arm emitted the same relation sequence, used the same signed-query boundary, stopped at rank 39 at the same source, and reproduced the same anchored logs. The independent audit passed all nine cases, including the separate p=2,076,797 known control.

## Method

For each prior source triple `(a,b,c)`, the candidate caches its eight signed group sums using the already cached signed pair `(a,b)` and source `c`. Before querying source `k`, it constructs four signed sums for every pair `(d,k)`. Each five-source query then combines one cached triple and one cached current-source pair with one `add` call. The comparator is the audited pair-sum kernel from PR #1279; it uses two query additions and builds its prior pair cache after each completed source. All cache construction calls are charged, including current-source pairs on the rank-stopping source. Query order, triple bucket lookup, row verification, modular rank insertion, source and resource caps are unchanged.

The audit checks each source's exact addition identity:

`pair_add_calls - triple_add_calls = step_probes + pair_baseline_insertions - triple_pair_insertions - triple_cache_insertions`.

The same eight fresh classes and separate known control from the independently audited query-order holdout supply fixed source entries, class points, subgroup orders and lower-support rows. The pair and triple arms alternate execution order by case. The checked Sage runtime receipt was frozen before replay. `candidate_id` and `target_online_ms` are null because this is a relation-collection kernel comparison.

## Fresh paired results

| p | q | Signed queries | Pair `add` | Triple `add` | Pair / triple | Triple cache entries | Triple cache shallow MB |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 3280037 | 1483 | 12,064,156 | 24,775,853 | 12,768,961 | 1.940 | 57,120 | 12.22 |
| 3309077 | 277 | 2,589,014 | 5,226,590 | 2,661,084 | 1.964 | 23,400 | 5.35 |
| 3382237 | 97 | 6,444,321 | 13,152,852 | 6,748,339 | 1.949 | 39,680 | 8.04 |
| 3456197 | 6779 | 4,561,452 | 9,237,824 | 4,708,972 | 1.962 | 32,480 | 6.85 |
| 3500957 | 457 | 6,468,450 | 13,143,015 | 6,714,373 | 1.957 | 39,680 | 8.04 |
| 3530957 | 141161 | 2,591,338 | 5,234,704 | 2,666,874 | 1.963 | 23,400 | 5.35 |
| 3538477 | 32159 | 3,232,143 | 6,572,679 | 3,366,856 | 1.952 | 26,208 | 5.81 |
| 3760037 | 719 | 9,065,751 | 18,503,491 | 9,485,748 | 1.951 | 47,872 | 10.70 |

The fresh-case totals are **95,847,008** pair-kernel additions and **49,121,207** triple-kernel additions, a 1.951× pair/triple ratio. The maximum recorded shallow cache estimate is **12.22 MB** for the triple arm and **0.44 MB** for the pair arm. These estimates count each cache dict, key tuple and value tuple once at the stopped prefix; they exclude allocator overhead and other index state. The maximum process peak RSS across fresh paired cases was **395,083,776 bytes**, covering both arms and Sage rather than attributing memory to one arm.

The summed component wall intervals were **230.41 s** for pair and **146.54 s** for triple (1.572× pair/triple) on this ordinary local host. They include cache construction and row verification inside index append. They exclude input loading, degree-13 source lift, lower-support row insertion, process launch and anchored replay. The timing is exploratory under the repository CPU tier contract; the pair baseline's summed interval differs materially from the earlier replay, so these seconds are not a stable deployment speedup estimate.

## Verification and next step

`audit.py` verifies pinned source and prior pair-audit identities, every lower-row and emitted support-eight row digest, exact query and rank trajectories, per-source cache insertion recurrences, the addition identity above, phase sums, cache counts and anchored log vectors. `post-run.json` and `post-audit.json` seal the results; `verify.py` checks final custody and aggregate totals.

A next experiment should compare these kernels on a Tier 1 isolated cloud instance with alternating pair order and exposed CPU, throttling, steal-time, memory and calibration receipts. That would test whether the operation-count reduction survives as a reproducible wall-time gain under a declared resource envelope.
