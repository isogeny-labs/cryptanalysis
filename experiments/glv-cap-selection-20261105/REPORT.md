# GLV table cap by bit length: selection round, 38-42 bits (seed 20261105)

Status: **selection round, exploratory** (protocol frozen in PR #1339 before any row existed; `PROTOCOL.md`, `PROTOCOL.sha256`). It chooses a candidate; it confirms nothing. Operation counts only, no wall time.

## Observation

Ratio of summed `curve_solve` group operations, arm over main (r = 32), same curves and targets, 700 curves per family and size (one target each), 95% bootstrap intervals over curves (10,000 draws), both families pooled by geometric mean:

| bits | r64 / main | r128 / main |
|---|---|---|
| 38 | 0.994 [0.959, 1.028] | 1.008 [0.976, 1.042] |
| 39 | 1.016 [0.981, 1.053] | 0.999 [0.965, 1.032] |
| 40 | 0.974 [0.941, 1.008] | 0.982 [0.948, 1.017] |
| 41 | 0.972 [0.938, 1.007] | 0.970 [0.936, 1.005] |
| 42 | 0.954 [0.922, 0.988] | 0.969 [0.938, 1.003] |

Per family and cell (descriptive) are in `results.md`; every r128 per-cell interval contains 1 (the pooled 42-bit upper bound is 1.003); r64 excludes 1 in j1728 40 bits (0.931 [0.887, 0.976]), j0 42 bits (0.944 [0.899, 0.990]) and pooled 42 bits. These are 20 cell intervals read at 95% without adjustment, so a couple of exclusions are expected by chance.

Controls: the identity control (forced r = 32, 160 rows at 38 and 42 bits) matches main's `group_ops` exactly on every row. The positive control (r = 8 against main, 42 bits, both families) is 1.133 [1.018, 1.259], passes. Every answer is correct in every arm.

## Selection rule applied (frozen in PROTOCOL.md)

| arm | fitted ratio at 38 / 39 / 40 / 41 / 42 | slope per bit | T | suffix geomean | one-sided 90% upper bound | robust |
|---|---|---|---|---|---|---|
| r64 | 1.007 / 0.994 / 0.982 / 0.970 / 0.958 | -1.25% | 39 | 0.9788 (39-42) | 0.9898 | yes |
| r128 | 1.007 / 0.996 / 0.986 / 0.975 / 0.964 | -1.09% | 40 | 0.9737 (40-42) | 0.9863 | yes |

No size from T up is wholly worse for either arm. Both arms pass the gate; r128 has the lower suffix mean by 0.53% in log ratio, just above the 0.5% tie width, so by the frozen rule **r128 is chosen, T = 40**:

```
cap(lg) = 32 for lg < 40;  cap(lg) = 128 for lg >= 40
```

The bootstrap distribution of T for r128 (descriptive): 38: 18%, 39: 26%, 40: 45%, 41: 9%, 42: 1%, none: 1%. For r64: 38: 20%, 39: 34%, 40: 41%, 41: 4%. The threshold is therefore located only to about +/-1 bit, as the protocol's power section said.

## Interpretation (kept apart)

- The data are consistent with a saving that grows by about 1.1-1.3% per bit from nothing at 38 bits to about 3-4% at 42 bits, in both table sizes. The 42-bit r128 point (0.969) is a little lower than #1332's 0.989 on other curves; the two intervals overlap.
- The choice of 128 over 64 rests on a 0.03-percentage-point margin over the tie width and on the 46-bit saving in #1332 (0.968 for 128; 64 not confirmed). Nothing here separates the two tables: their per-size intervals overlap everywhere.
- The selection is a noisy pick (winner's curse): the suffix mean 0.974 is selected on the same data and will be optimistic. The held-out round measures the candidate.
- The rule is compatible with #1338: that round forced the table to 128 at 34-40 bits and found 38 bits neutral (1.003) and 40 bits 0.992.

## Above 46 bits and below 38

Not measured here. The default in the protocol keeps cap = 128 for all lg >= 40 (including above 46, where #1332 measured 128 only to 46 bits); that extends the claim beyond measurements and is flagged in the code PR. Below 38 bits the cap stays at main's 32, where #1338 found the bigger table worse at 34-36 bits.

## Distance to matched rho (descriptive, raw group ops, not priced)

No rho reference was run in this round (the confirmation round, PR #1340, ran it on 60 targets per cell at 40-43 bits: GLV main used about 0.72 (j = 1728) and 0.60 (j = 0) of rho's raw group operations on the same targets, rho S = group_ops / sqrt(n) about 1.0). Main's mean S = group_ops / sqrt(n/m) here is 1.45-1.52 in every cell (`results.md`). Native work is not priced (AGENTS.md 5a band not computed) and no ranking is claimed. An earlier version of this paragraph used 1.58 sqrt(n) for rho from the task brief; the measured negation-map rho in #1340 is about 1.0 sqrt(n), so the ratio quoted before was wrong and is replaced here.

## Limits

Power was stated in advance: pooled per-size half-width about 3.5%, threshold located to about +/-2 bits; false-GO probability about 13% under no effect. Single seed, 38-42 bits only, two families, one target per curve, independent walks, group operations only (no wall time; Tier 1 is the user's decision). T is held fixed in the bootstrap upper bound, which is optimistic.

## Reproduce

`run_all.sh p1 j1728` and `run_all.sh p2 j0` with builds of main 1ee4f47 (+ `force-r.patch` for the forced arms), then `gzip rows_*.jsonl`, `analyze.py`, `chart.py`. About 0.95 CPU-hours (two processes, 28 minutes each). Raw rows (`rows_*.jsonl.gz`) and `REPORT.pdf` are not in Git (artifact-store policy; this session has no store credentials); their sha256 are in `SHA256SUMS`.
