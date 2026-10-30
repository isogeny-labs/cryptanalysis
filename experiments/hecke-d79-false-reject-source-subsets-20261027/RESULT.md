# Twelve retained source lifts certify rank 39 at p103357

The p103357 false-reject trace contains a 12-source subset whose four independently verified Hecke rows raise the degree-2/5 plus direct relation matrix from rank 35 to rank 39 over F_197. The subset is inclusion-minimal under single-source deletion: removing any one of its 12 sources lowers the rank below 39. This gives a compact, replayable certificate for the rank gain that invalidated the pre-lift rank-37 skip rule.

| Replayed source policy | Sources | Hecke rows available | Rank over F_197 | Retained lift-time sum |
| --- | ---: | ---: | ---: | ---: |
| No degree-13 sources | 0 | 0 | 35 | 0 |
| Ascending prefix, first rank-39 point | 35 | 120 | 39 | 1.538 s |
| Descending-deletion certificate | 12 | 4 | 39 | 0.547 s |
| Full retained trace | 40 | 218 | 39 | 1.756 s |

The ascending prefix gained one rank at source counts 24, 27, 30, and 35. The 12 certificate sources are `1, 4, 5, 8, 12, 15, 19, 21, 25, 26, 29, 34`; the four exact signed class rows and their source supports are in `result.json`. An independent Sage pair-index reconstruction checked all 40 source equations and each emitted row on the recorded curve, then rebuilt every prefix and deletion rank. The parent four-class audit separately verified the anchored 40-point class-log replay.

This is a retrospective subset of already measured lifts. The 0.547 s is the sum of their original source intervals, not a measured online run or a prospective source-order cost. Descending deletion proves inclusion minimality for this trace; it does not establish a globally smallest source set. The method suggested by the certificate is to update rank after each verified source relation and prioritize sources with complementary support. A prospective scheduler must freeze its order before seeing new source outputs and test it on fresh classes. `candidate_id` and `target_online_ms` remain null.

The ranks and curve equations are checked by Sage, while the corresponding full Lean matrix/curve bridge remains open as described in the parent series `PROOF_MAP.md`. The pinned launcher receipt is `sage-runtime-info.txt`.
