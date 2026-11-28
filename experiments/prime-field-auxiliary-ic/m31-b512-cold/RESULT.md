# Frozen public M31 B512 cold comparison

The protocol was committed and opened as draft PR #2012 before this
validation run. All 45 cold fresh-process arms across five previously
published public targets and three seeds returned a verified answer. The
independent `audit.py` reopened each stdout by its CSV digest, verified all
45 public answers, and checked all 7,190 IC relation equations plus their
weighted factor-base cancellation and scalar equation. Raw CSV SHA256:
`817a34919bdf5c585a84231be6dca6ef37ce92870d87c598dc024b1ffba05c46`.

| Arm | Charged wall median | Charged CPU median | Solved |
|---|---:|---:|---:|
| B384 indexed m=2 | 29.234 ms | 28.762 ms | 15/15 |
| B512 indexed m=2 | 29.305 ms | 28.834 ms | 15/15 |
| Archived C++ rho | 14.892 ms | 10.745 ms | 15/15 |

The median paired B384/B512 ratio was 0.9976 wall and 0.9975 CPU; B512
won only 7/15 paired wall comparisons and 7/15 CPU comparisons. The
predeclared B512 selection gate (at least 12/15 wins and 1.15 median gain
on both clocks) fails. B512 beat rho in only 1/15 wall comparisons and
zero CPU comparisons, so the separate breakthrough gate also fails. Rho's
maximum observed wall time was 166.10 ms, far above its CPU time; all such
host-scheduling observations remain in the table. Per-target median wall
times, target order 0..4, were B384
[30.464, 28.756, 33.007, 28.110, 31.927] ms; B512
[29.142, 25.063, 31.061, 31.300, 30.020] ms; rho
[11.176, 9.671, 16.660, 15.121, 17.085] ms.

B512 used fewer target queries in all 15 matched blocks; median queries
fell from 1,483,386 to 1,180,389 and the median paired B384/B512 query
ratio was 1.3244. However, median pair-index construction rose from
3.064 to 5.405 ms as entries rose from about 147,450 to 262,102.
Median online time fell from 21.611 to 19.075 ms, almost exactly offsetting
the additional setup. Median internal main-entry-to-report was 25.135 ms
at B384 and 25.113 ms at B512. External charged timings additionally
include process startup, parsing and public verification. This is a
size-only change to an existing collector; it does not alter relation
construction, graph recovery or asymptotic work.

The seed-0 five-target pilot was exploratory and is excluded from the
validation table. The observed tradeoff suggests that further B expansion
needs a cheaper exact pair table or a higher-yield relation family to change
cold single-target cost. No Lean timing theorem is asserted: this decision
comes from empirical paired measurements and exact certificate replay.
