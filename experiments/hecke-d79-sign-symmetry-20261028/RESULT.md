# Sign-symmetric D79 support-eight triple cache

Opposite-sign symmetry cut persistent signed-triple entries **exactly in half** in all nine audited classes. Across eight fresh paired classes, it reduced counted group additions from **49,121,207** to **48,976,287** (144,920 fewer, 0.295%) while preserving every relation row, query boundary, rank trajectory and anchored log. The maximum recorded shallow cache estimate fell from **12.22 MB** to **6.34 MB**. A second, separately frozen implementation reused the four derived negative triples within each later-four support, reducing counted negations by **17,631,248** against the first symmetric implementation with identical additions and persistent cache entries.

## Method and frozen comparisons

The full comparator from PR #1280 stores all eight sign choices for a prior triple `(a,b,c)`. The first candidate stores only the four choices with first sign `+1`, deriving the other four by the group identity `-(A+B+C)=(-A)+(-B)+(-C)` at each query. The second candidate computes those four negatives once per later-four support and places them in an ephemeral eight-value lookup. The source sequence, reverse-lexicographic sign sequence, current-source signed pair cache, relation verification, rank-39 stop and resource caps remain fixed. Cache construction and all derivation negations are counted.

The first protocol and source hashes were sealed before its nine-case replay. The second implementation and its own protocol were sealed before its replay, after the first known-control arm indicated a wall-time regression. Both pair arms alternate case order. The source journals include one known control at `p=2076797` and eight fresh classes; each has 40 class columns and the subgroup order `q` recorded in its case summary. These are relation-collection component comparisons, so `candidate_id` and `target_online_ms` are null.

## Fresh-class measurements

| `p` | `q` | Signed probes | Full / symmetric triple entries | Full / symmetric shallow MB | Full `add` | Symmetric `add` | Symmetric / micro `neg` |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 3280037 | 1483 | 12,064,156 | 57,120 / 28,560 | 12.22 / 6.34 | 12,768,961 | 12,740,401 | 18,419,472 / 13,895,412 |
| 3309077 | 277 | 2,589,014 | 23,400 / 11,700 | 5.35 / 2.75 | 2,661,084 | 2,649,384 | 3,907,169 / 2,936,285 |
| 3382237 | 97 | 6,444,321 | 39,680 / 19,840 | 8.04 / 4.14 | 6,748,339 | 6,728,499 | 9,798,337 / 7,381,720 |
| 3456197 | 6779 | 4,561,452 | 32,480 / 16,240 | 6.85 / 3.53 | 4,708,972 | 4,692,732 | 6,898,743 / 5,188,195 |
| 3500957 | 457 | 6,468,450 | 39,680 / 19,840 | 8.04 / 4.14 | 6,714,373 | 6,694,533 | 9,805,309 / 7,379,643 |
| 3530957 | 141161 | 2,591,338 | 23,400 / 11,700 | 5.35 / 2.75 | 2,666,874 | 2,655,174 | 3,912,428 / 2,940,674 |
| 3538477 | 32159 | 3,232,143 | 26,208 / 13,104 | 5.81 / 2.99 | 3,366,856 | 3,353,752 | 4,901,706 / 3,689,647 |
| 3760037 | 719 | 9,065,751 | 47,872 / 23,936 | 10.70 / 5.56 | 9,485,748 | 9,461,812 | 13,784,719 / 10,385,059 |
| **Total** | | | | | **49,121,207** | **48,976,287** | **71,427,883 / 53,796,635** |

The micro lookup performs the same 48,976,287 additions as the first symmetric implementation. In the first paired replay, summed component wall intervals were 130.23 s for full and 134.09 s for symmetric; in the second, they were 111.21 s for symmetric and 105.89 s for micro. The intervals include index append, cache construction and row checks, and exclude process launch, source lifting, lower-support row insertion and anchored replay. Local host timing is exploratory under the repository CPU tier contract. The two runs' symmetric intervals differ substantially, so wall results are interpreted only within each pair. Maximum paired-process RSS was 286,326,784 bytes in the first replay and 284,180,480 bytes in the second; neither figure isolates one arm's memory.

## Verification and next experiment

The two independent audits passed **9/9** cases each. They check pinned source and prior-audit hashes, lower-support and emitted support-eight row digests, exact probes and rank paths, addition and negation identities per source, cache insertion recurrences, complete case totals and anchored scalar replay. The post-run and post-audit seals retain producer, audit and result hashes; `verify.py` checks final custody and both aggregate results.

A Tier 1 paired run with fixed cloud allocation, alternating order, exposed topology and noise receipts would test the wall-time effect under a declared resource envelope. A separate implementation experiment could avoid the per-support ephemeral dictionary while retaining its four-negation reuse.
