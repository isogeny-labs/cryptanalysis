# Exact-order signed pair-sum kernel for D79 support-eight collection

Caching the four signed sums of each prior source pair reduced counted elliptic-curve group additions by **141,035,083 across eight fresh paired classes**, from 236,882,091 to 95,847,008 (**59.54%**). The kernel combines two cached signed pair sums and the signed current source, preserving the frozen reverse-lexicographic support and sign order. Each arm emitted the identical relation sequence, stopped at the identical probe and rank-39 boundary, and passed anchored log replay. The independent audit passed all nine cases, including the separate p=2,076,797 known control.

## Method and frozen inputs

The baseline forms each signed five-source group sum with five `add` calls. The candidate precomputes four signed pair sums for every prior source pair after that source's completed query phase, then forms each five-source query with two `add` calls. Its pair-cache setup is charged. The query stream, triple index, group law, row verification, immediate rank insertion, and caps are the same. Per completed source `k`, the audit checks the exact identity `baseline_add_calls - pair_add_calls = 3 × step_probes - 4k`; on the rank-stopping source no pair cache update is made. Negations are counted separately.

The source entries, class points, subgroup orders, lower-support rows, and previous independent audit are pinned to the nine-case prospective query-order holdout in PR #1278. The accepted local Sage launcher and runtime receipt were frozen before the replay. Baseline and candidate execution order alternates by case index. `candidate_id` and `target_online_ms` remain null because this is a relation-collection kernel comparison.

## Fresh paired results

| p | q | Signed queries | Baseline `add` | Pair-sum `add` | Baseline / pair-sum | Baseline seconds | Pair-sum seconds |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 3280037 | 1483 | 12,064,156 | 60,965,801 | 24,775,853 | 2.461 | 58.49 | 29.11 |
| 3309077 | 277 | 2,589,014 | 12,992,228 | 5,226,590 | 2.486 | 13.28 | 6.32 |
| 3382237 | 97 | 6,444,321 | 32,483,831 | 13,152,852 | 2.470 | 30.73 | 17.54 |
| 3456197 | 6779 | 4,561,452 | 22,920,440 | 9,237,824 | 2.481 | 25.77 | 10.80 |
| 3500957 | 457 | 6,468,450 | 32,546,381 | 13,143,015 | 2.476 | 29.99 | 15.45 |
| 3530957 | 141161 | 2,591,338 | 13,007,314 | 5,234,704 | 2.485 | 12.87 | 8.95 |
| 3538477 | 32159 | 3,232,143 | 16,267,596 | 6,572,679 | 2.475 | 14.16 | 6.05 |
| 3760037 | 719 | 9,065,751 | 45,698,500 | 18,503,491 | 2.470 | 43.12 | 19.44 |

The fresh-case totals are **236,882,091** baseline additions and **95,847,008** pair-sum additions (2.471× baseline/pair-sum). Negation calls total 165,460,909 and 47,919,539 respectively. The summed component wall intervals are 228.41 s and 113.66 s; those local timings are exploratory under the repository CPU tier contract. They include pair-cache construction and row verification inside each index append, and exclude source lift, input loading, baseline row insertion, process startup, and anchored replay. They are not a one-target online comparison.

## Verification and custody

`audit.py` verifies the sealed source and run hashes, every source's lower-row and emitted support-eight row digests against the previously audited producer, identical probe/status/rank trajectories, the exact per-source group-addition difference above, phase sums, and all anchored log vectors. `post-run.json` and `post-audit.json` retain SHA-256 identities; `verify.py` checks the final custody and totals.

The original replay process ended after seven complete cases; the seven-case index, stdout, and partial eighth journal are retained under `interrupted-run/`. `pre-resume.json` pins them and the versioned resume source. A host restart removed the temporary target of the repository Sage launcher symlink; the first resume invocation failed before experiment work. Its stderr is retained, the temporary directory was restored, and `resume-runtime-info.txt` matches the original runtime receipt exactly. The remaining two cases were then replayed from their first source.

The next implementation experiment is to cache signed triple sums across the later-four supports while preserving the same query order, and compare its additional memory and setup cost with this pair-sum kernel on a fresh frozen replay panel.
