# Gain-forest harvester k=3 beyond toy sizes: results

All numbers [pcc:unverified]. Protocol frozen before the ladder data: `PROTOCOL.md`. Raw: `data/` (82 JSON, one per
(p, arm, seed); `p<p>_<A|B>_s<seed>.json`), tables `analysis_frozen.txt`, `analysis_seeds1-4.txt`, `summary_*.json`,
code `analyze.py`, runner `run_cells.sh`. Code under test: cryptanalysis origin/main 20348aac (PR #1901 merged), example
`gaudry_cubic_bench`. Host: shared 4-CPU cloud VM, single-threaded runs, no isolation tier (wall indicative only; S is a count).

## What ran
Curves over F_{p^3}, n ~ p^3. p = 271, 523, 1039, 2083 (re-run: same code and seeds as PR #1901) and the extension
p = 4159, 8317, 16657 (n = 2^36.1, 2^39.1, 2^42.1). Arm A: eliminator `--max-lp 2`; arm B: harvester `--harvester cycles
--max-lp 3`. Seeds 1..6 everywhere except arm A at p = 16657 (seeds 1..2 under the frozen protocol, about 16.5 min each; seeds 3..4
were added afterwards, so seeds 1-4 are complete at all seven sizes). 82 of 82 cells solved, every logarithm group-checked
([d]G = Q, `correct` = true), no kill, no failure. Rho reference = plain r-adding `run_rho3` on the same instance (one run per
instance, so the denominator is noisy: S_rho per instance 0.7 to 2.9). `rho.negation` is an ecbench instrument and was not run here.

Reproduction check: the re-run original ladder gives the PR's numbers exactly: S_A = 4572 / 3836 / 3267 / 2969, S_B = 2602 / 1806 /
1239 / 908, exponents A 0.428, B 0.332, paired B - A -0.096 (bootstrap CI [-0.130, -0.067]; PR: -0.096 +- 0.018 SE).

## Per-size table (frozen cell set; means over seeds; ratio is paired per seed with bootstrap 95% CI)
| p | n bits | S_A | S_B | S_B/S_A | S_A / rho | S_B / rho |
|---:|---:|---:|---:|:---|---:|---:|
| 271 | 24.2 | 4572 | 2602 | 0.563 [0.488, 0.635] | 3113 | 1772 |
| 523 | 27.1 | 3836 | 1806 | 0.470 [0.444, 0.499] | 2949 | 1388 |
| 1039 | 30.1 | 3267 | 1239 | 0.383 [0.346, 0.417] | 2538 | 963 |
| 2083 | 33.1 | 2969 | 908 | 0.312 [0.278, 0.336] | 1800 | 551 |
| 4159 | 36.1 | 2432 | 823 | 0.338 [0.328, 0.351] | 1986 | 672 |
| 8317 | 39.1 | 2130 | 735 | 0.345 [0.332, 0.359] | 1421 | 490 |
| 16657 | 42.1 | 1815 (2 seeds; 4 seeds 1823) | 638 | 0.348 [0.342, 0.355] (2 seeds) | 900 | 317 |

Rho columns are ratio of the seed-mean S to the seed-mean rho S (mean rho S 1.47, 1.30, 1.29, 1.65, 1.22, 1.50, 2.02).
The gain stops improving: the ratio is 0.31 at 2083 and 0.34 to 0.35 at 4159 to 16657.

## Exponent of total ops on n (per-seed least squares over the sizes, then mean with bootstrap 95% CI over seeds)
| ladder | A | B | paired B - A |
|---|---|---|---|
| original 4 (271..2083), 6 seeds | 0.428 [0.402, 0.460] | 0.332 [0.304, 0.363] | -0.096 [-0.130, -0.067], B lower 6/6 |
| **extended 7 (271..16657), frozen cells** | 0.427 [0.419, 0.435] | **0.391 [0.381, 0.402]** | **-0.036 [-0.041, -0.031]**, 6/6 |
| extended 7, seeds 1-4 (all cells present) | 0.426 [0.419, 0.434] | 0.390 [0.381, 0.405] | -0.036 [-0.043, -0.029], 4/4 |
| top 3 sizes (4159..16657), seeds 1-4 | 0.431 [0.424, 0.438] | 0.445 [0.432, 0.457] | +0.014 [+0.004, +0.020] |
| top 4 sizes (2083..16657), seeds 1-4 | 0.418 [0.392, 0.436] | 0.439 [0.430, 0.448] | +0.022 [+0.005, +0.048] |

Local slopes (seeds 1-4): A 0.41, 0.41, 0.48, 0.38, 0.44, 0.43; B 0.34, 0.30, 0.38, 0.42, 0.46, 0.43 for 271-523 ... 8317-16657.
B's local slope climbs from about 0.30-0.35 to about 0.43-0.46, i.e. A's slope.

## Verdict on the 0.332 (pre-registered rule)
**It drifts back.** The B exponent over the extended ladder is 0.391, CI lower bound 0.381 above 0.332, and the paired B - A is -0.036,
above the -0.05 cut. Predictions P1 (ratio in 0.25-0.40: yes, 0.34-0.35), P2 (A in 0.39-0.45: 0.427; B in 0.34-0.40: 0.391; paired
-0.03 to -0.09: -0.036, at the edge) and P3 (harvest wall per charged op within 2x of the relation phase: 0.27-0.31x) held. The
four-point 0.332 was a statement about p <= 2083 (n <= 2^33): beyond it the harvester's gain is a constant factor of about 0.33-0.35
in S, not an exponent change, and over the top three sizes its exponent is not below the eliminator's. This is a ladder over seven
points, not an asymptotic claim.

## Why (from the JSON, seeds 1-4, exponents of the seed-mean over n)
| component | A all / top3 | B all / top3 |
|---|---|---|
| residuals (relation phase, about 99% of S) | 0.418 / 0.426 | 0.380 / 0.436 |
| LA ops (mod-n multiplications) | 0.497 / 0.491 | 0.745 / 0.718 |
| mean row weight | 0.084 / 0.050 | 0.276 / 0.244 |

B's residual saving settles at a constant factor (residuals B/A: 0.55, 0.47, 0.37, 0.30, 0.33, 0.34, 0.34), while its linear algebra grows
as n^0.72-0.75 (rows are root-to-root combinations, weight 13 -> 372 against 8.5 -> 24.7 for A). LA is still only 2.3% of B's total ops at
p = 16657 (0.04% for A), so S does not feel it yet, but the term is the one that will take over; a minimum-weight cycle basis (unbuilt) is the
remedy named in PR #1901.

## Goal 4: does S charge the harvesting work?
- Charged: every mod-n multiplication in `find`, `reduce`, `apply`, merges and the Wiedemann solve goes into `la_ops` (9 F_p-equivalents each
  in `total_ops`); discarded relations (more than `max_lp` large primes) are charged in the oracle. Harvest plus LA is 0.04% to 2.3% of B's
  `total_ops`; the merge part alone 0.00-0.13%.
- Not charged: hash-map lookups, buffer scans, pointer chasing, `cols.sort_unstable`, additions mod n. Test: wall time of the timed
  harvest+LA window per charged op is 0.27-0.72x of the relation phase's (B) and 0.47-1.2x (A), so no uncharged cost shows up in wall time, and
  the B/A wall ratio (343 s / 981 s = 0.35 at p = 16657) matches the B/A S ratio (0.348). Within this instrument S is not hiding harvest work.
  Wall is from a shared host and is indicative only. Not tested: memory traffic of a larger buffer (peak RSS not recorded here).

## Distance to rho
B at p = 16657 (n = 2^42.1): S about 638, i.e. about 317x the mean plain-rho S (2.02) of the same six instances, 501x by the per-instance ratio;
A is 900x (mean ratio) to 1735x. The distance shrinks only slowly: a naive extension of the fitted lines (S ~ n^(e - 0.5)) from 638 with the
top-three B exponent 0.445 would reach S = 1 near n ~ 2^211; with the extended-ladder 0.391, near 2^128. These are arithmetic on fitted
lines, not measurements, and the top-3 slope suggests the lower figure is optimistic. Against `rho.negation` (about sqrt 2 cheaper in steps on a
group with +-P symmetry) the distance would be larger still; that was not measured.

## Not done
- k = 4 (`gaudry_quartic_la`) not extended: 55 min for two seeds at p = 769 in PR #1901; the k=3 ladder used the whole budget.
- S3 checkpoint upload and `bench.record/v1`: no AWS profile, upload token or presigned link in this session; `scripts/checkpoint.sh push`
  failed ("cannot upload"), a RESUME snapshot is committed in this directory instead. A `benchrec` record could not be closed without a
  report PDF and S3 upload and was not committed. No isolab-eks run, no conductor claim.
- Arm A at p = 16657 has 2 seeds under the frozen protocol (4 with the post-protocol additions), not 6; no sizes above p = 16657 (the
  generator asserts p < 2^20; p = 33331 would take about 40 min per eliminator run).
- Matched `rho.negation` not run (different instrument, no F_{p^3} port). Rho here is one run per instance.
- The calibration run (p = 4159, seed 1) was made before the protocol; it is the same deterministic cell as in the ladder.
- No pcc `verify` standing: claim ids below are unverified records.
