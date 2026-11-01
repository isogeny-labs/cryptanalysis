# Held-out confirmation of the size-dependent GLV table cap (cap 128 from 40 bits), seed 20261106

Protocol frozen in PR #1340 before any row existed (`PROTOCOL.md`, `PROTOCOL.sha256`). Candidate: branch `glv-table-cap-by-size`, commit e71ebec (PR #1341), built unpatched, against main 1ee4f47. Operation counts only; no wall time.

## Observation

Ratio of summed `curve_solve` group operations, candidate over main, same curves and targets, 1600 curves per family and size (one target each), independent walks. Bootstrap over curves, 10,000 draws.

**Primary (8 cells, geometric mean, 97.5% interval): 0.9849 [0.9725, 0.9978], half-width 1.28%. The upper bound is below 1: H1 is confirmed.** (95% interval [0.9738, 0.9963].)

**No-worse check per size** (both families, Bonferroni 98.75% intervals): passes, no size is wholly above 1.

| bits | cand / main, both families | 98.75% interval | 95% interval |
|---|---|---|---|
| 40 | 0.9914 | [0.9633, 1.0206] | [0.9689, 1.0143] |
| 41 | 0.9890 | [0.9608, 1.0186] | [0.9670, 1.0118] |
| 42 | 0.9821 | [0.9539, 1.0106] | [0.9602, 1.0046] |
| 43 | 0.9773 | [0.9496, 1.0071] | [0.9553, 1.0002] |

Per family (sizes 40-43 pooled, 95%, descriptive): **j = 1728 0.9682 [0.9530, 0.9836]; j = 0 1.0020 [0.9860, 1.0187]**.

Cells (95%, descriptive; S = group_ops / sqrt(n/m)):

| family | bits | main S | cand S | cand / main |
|---|---|---|---|---|
| j1728 | 40 | 1.483 | 1.432 | 0.967 [0.936, 0.999] |
| j1728 | 41 | 1.454 | 1.439 | 0.988 [0.957, 1.020] |
| j1728 | 42 | 1.471 | 1.426 | 0.970 [0.941, 1.000] |
| j1728 | 43 | 1.474 | 1.397 | 0.948 [0.918, 0.979] |
| j0 | 40 | 1.463 | 1.488 | 1.016 [0.985, 1.049] |
| j0 | 41 | 1.442 | 1.430 | 0.990 [0.959, 1.024] |
| j0 | 42 | 1.442 | 1.439 | 0.995 [0.962, 1.029] |
| j0 | 43 | 1.440 | 1.450 | 1.007 [0.975, 1.040] |

**Identity cells** (38 and 39 bits, 320 rows): the candidate's `group_ops` equal main's on every row. All answers are correct in both builds; the rule picks 32 everywhere for main and 128 for every curve at 40-43 bits in the candidate (recomputed in `analyze.py`).

## Interpretation (kept apart)

- The pooled saving is 1.5% with a confirmation margin of 0.2 percentage points on the upper bound: the result is confirmed, but only just, and the expected power at this effect was about 0.6 (PROTOCOL.md). A repeat could fall on either side.
- The saving is carried by j = 1728 (3.2%); j = 0 shows none here (1.002, interval spans 1). The earlier confirmed round (#1332) pooled both families at 42-46 bits (0.980). The family split here is descriptive and unregistered; it does not break the pooled confirmation but it says the benefit is not established for j = 0 at 40-43 bits, and that the candidate does no harm there (no j0 cell interval above 1).
- The selection round's 40-42 bit estimate (0.974) was optimistic as expected (winner's curse): held-out 40-42 bits gives 0.988 pooled over sizes 40-42.
- Size-wise the trend is a saving growing with size (0.991, 0.989, 0.982, 0.977), compatible with #1332's 0.989 / 0.984 / 0.968 at 42 / 44 / 46. No size is shown to be better individually at the Bonferroni level; 43 bits, new here, has the lowest ratio.

## What this does and does not support

Supports: in group operations the candidate saves about 1.5% (pooled, 40-43 bits) and is identical to main below 40 bits. Does not support: a wall-time claim (Tier 1 run needed; #1337 saw no per-operation cost rise for 128 at 42-46 bits, not at 40-41), anything above 46 bits (cap 128 there is an extrapolation, kept for monotonicity and flagged in #1341), a j = 0-specific benefit, a preference between 64 and 128.

## Distance to matched rho (descriptive, raw group ops, not priced)

Negation-map rho on main's rows for curves 0-59 of each cell (60 targets per cell, so about +/-7% per cell): rho S = group_ops / sqrt(n) is 0.93-1.09. Mean of the cell ratios (operations over rho's on the same targets): j = 1728 main 0.72, candidate 0.67; j = 0 main 0.60, candidate 0.59. The remaining distance to rho is therefore a GLV walk that already uses about 0.6-0.7 of rho's raw group operations at 40-43 bits (native work not priced; AGENTS.md 5a band not computed; no ranking claimed). The candidate moves that ratio by 0.05 (j1728) and 0.01 (j0).

## Limits

Single seed; two families; 40-43 bits; one target per curve. Power at the realized pooled effect was about 0.6. The family asymmetry is unregistered. Group operations only. About 1.7 CPU-hours; with the selection round about 2.6 of the 3 CPU-hours.

## Reproduce

`run_all.sh p1 j1728`, `run_all.sh p2 j0` with builds of main 1ee4f47 (`b-main`) and e71ebec (`b-cand`), then `gzip rows_*.jsonl`, `analyze.py`, `chart.py`. Raw rows and `REPORT.pdf` are not in Git (artifact-store policy; no store credentials here); sha256 in `SHA256SUMS`.
