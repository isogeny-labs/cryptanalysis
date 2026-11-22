# Gain-forest cycle harvester, k = 3 large primes: results

All numbers `[pcc:unverified]`. Raw: `A.json` (eliminator, 11.11's "uncapped"), `B.json` (cycles, `--max-lp 3`),
`A2.json` (diagnostic: eliminator with `d` kept out of the large primes), all in this directory (each under 2 MB);
tables: `summary_ABA2.txt`, `summary_B_vs_A2.txt`, `harvest_stats_B.txt`; script `summarize_paired.py`.
Instrument: cryptanalysis branch `claude/gaudry-gain-forest-harvester` (code commit `7753ec67e`, base `6b64ee6c`).
Protocol and the verdict rule were frozen in `PROTOCOL.md` before any of these runs.

## What ran

`bench --protocol-la --groebner --sizes 271,523,1039,2083 --seeds 6 --lp-rule --lp-arm-only`
(`--lp-arm-only` skips the dense and plain-Wiedemann control arms, which do not depend on the harvester; the
large-prime arm is exactly the one `--protocol-la` ran before) with `--max-lp 2` (A), `--harvester cycles --max-lp 3` (B),
`--max-lp 2 --eliminator-d-small` (A2). 24 runs per arm, all six seeds at all four sizes (no reduction needed), every
recovered logarithm group-checked and equal to the planted one (the summarizer asserts it). Watchdog 4 GiB, no kill.
Wall: A and B ran concurrently, A finished in about 12 min and B in about 4 min; one A run at p = 2083 took 65 s.

## Verdict (pre-registered): PASS

Paired per seed, B minus A, mean of per-seed differences with standard error (sample sd / sqrt 6):

| p | S eliminator (A) | S cycles (B) | B - A, paired | diff / SE | B lower / higher |
|---:|---:|---:|---:|---:|:--:|
| 271 | 4572 | 2602 | -1970 +- 158 | -12.5 | 6 / 0 |
| 523 | 3836 | 1806 | -2030 +- 57 | -35.5 | 6 / 0 |
| 1039 | 3267 | 1239 | -2028 +- 163 | -12.4 | 6 / 0 |
| 2083 | 2969 | 908 | -2060 +- 220 | -9.4 | 6 / 0 |

End-to-end total-ops exponent (fit of log2 total ops on log2 n, per seed over the four sizes): A 0.428, B 0.332;
paired difference **-0.096 +- 0.018**, B lower on 6 of 6 seeds (worse/better 0/6).

Rule: S lower at >= 2 sizes by more than 2 SE (here 4 of 4) and exponent difference not above +0.05 (here -0.096): PASS.
This PASS is about the paired cost ledger of this module at these four sizes; it says nothing about rho (S at p = 2083 is still about 900, rho is
about 1 in the same unit) and nothing about sizes beyond 2^33.

## The prediction

The plan's "p = 523 from about 8 600 to about 3 700" was a model built on one seed-1 run measured with a different
configuration; the matched eliminator arm here is 3836 (not 8600). So the registered numbers do not compare directly.
Measured: 3836 -> 1806 (0.47x), residuals 3218 -> 1514 (2.1x fewer), the same sign and a larger relative effect than the model's
2.3x usable-partials factor, but the model and the measurement are different quantities.

## Where the saving comes from, and the cost

Per size means over six seeds (`summary_ABA2.txt`):

| p | residuals A / B | residuals per full row A / B | row weight A / B | LA ops A / B | merge ops A / B | rows mu fed B |
|---:|---:|---:|---:|---:|---:|---:|
| 271 | 1452 / 827 | 50.9 / 30.1 | 8.6 / 13.4 | 26 050 / 27 750 | 6 573 / 4 226 | 27 |
| 523 | 3218 / 1514 | 76.2 / 36.0 | 11.5 / 21.3 | 88 780 / 101 100 | 12 420 / 12 100 | 41 |
| 1039 | 7558 / 2863 | 96.0 / 42.9 | 15.0 / 43.3 | 239 500 / 477 900 | 36 500 / 44 680 | 66 |
| 2083 | 19 260 / 5874 | 152.8 / 51.2 | 16.6 / 73.5 | 638 100 / 2 533 000 | 66 700 / 141 100 | 103 |

- The relation phase is the saving: 2.1x to 3.3x fewer residuals to pin `d`, growing with p, because the 3-LP decompositions
  (49 to 56 percent of the generator output, discarded by the eliminator at `--max-lp 2`) now enter as 3-edges and mostly peel (at p = 2083: 713 accepted
  3-edges, 70 reduced on arrival, 642 peeled later, 1 left in the buffer).
- The cost is row weight and linear algebra. Harvested rows are denser (73.5 against 16.6 at p = 2083) and LA ops are 4.0x higher there.
  Mean distinct relations composed into a harvested row (the cycle-length analogue) is 36 / 80 / 188 / 418 at the four sizes: the forest
  roots every component at the sink and a row is a root-to-root combination, not a shortest cycle. LA is still 0.3 to 0.5 percent of total ops at
  these sizes, so S does not feel it yet, but the LA term grows faster than before and would be the first thing to bite later; a BFS or
  minimum-weight cycle basis (plan item 1) is the unbuilt remedy and is not measured here.
- Of the harvested rows nearly all (26.8 / 40 / 64.5 / 113.7 per run, see `harvest_stats_B.txt`) came from components already attached to the sink; balanced
  cycles in a free component gave 0.3 to 2 rows per run. At these sizes the 1-LP decompositions pin components early, so the sink is doing most of the work.
- Not part of the verdict: a quirk of the existing eliminator. It filters `c >= small`, which also catches the `d` column at index `small`, so `d` is reduced like a large prime. Keeping `d`
  out (A2, `--eliminator-d-small`) lowers S by only 24 to 236 (0.6 to 5 percent) and the exponent by 0.006 +- 0.013, so this is not what B's win rests on.
  B against A2: S lower by 1788 +- 120 / 2006 +- 62 / 1851 +- 76 / 1824 +- 51 (z = -14.9 / -32.5 / -24.4 / -36.0, 6 of 6 seeds each), exponent -0.090 +- 0.007.
  The harvester treats `d` as a small-base column (rows carry it), so A2 is the cleaner like-for-like and the conclusion is unchanged.

## Observations to keep with the numbers

- The S difference is nearly constant in p (-1970 to -2060), i.e. the ratio improves with p (0.57, 0.47, 0.38, 0.31) and the exponent falls; both A and B are
  exponents of a four-point fit with per-seed spread of 0.04 to 0.1, so the exponent figure is a statement about this ladder only.
- B's `mu` at stop (rows fed): 27 / 41 / 66 / 103 harvested rows (plus 0.7 to 1.7 direct 0-LP rows) against 26 / 41 / 64 / 106 base columns, i.e. the stop sits at mu about |F'|, as the plan states.
- Mean 3-edges left buffered at stop: 0, 0, 0.33, 1: the 2-core peeled almost everything.

## Tests (module `gaudry_cubic::tests`, `cargo test --release --lib gaudry_cubic::tests:: -- harvester eliminator_mode_report`, 3 new tests, 19 of 19 pass)

- `harvester_rows_hold_on_a_planted_system_and_the_count_balances`: 400 random relations with 0..3 large primes over a hidden solution; every released row holds, none inconsistent, and
  accepted large-prime equations = rows + joins + pins + null rows + buffered.
- `harvester_rows_hold_against_known_logs_on_a_planted_instance`: p = 67, every harvested row checked against brute-forced logs of all base points and the planted `d`; the full run recovers `d`.
- `eliminator_mode_report_is_unchanged`: golden report fields (p = 67, seed 1) taken from the unmodified code. Also, at p = 271 and 523 the full JSON of the default mode differs from the pre-change binary only in `wall_ms` and `linear_algebra_ms`.

## Not done / limits

- The k = 4 pipeline, the char-2 regime, a minimum-weight cycle basis, and any claim about rho or sizes above 2^33 were not touched.
- Harvester `lp_mean_merge_depth` in the JSON is the mean number of relations composed per row (a different quantity from the eliminator's merge depth).
- `lp_full_relations` for B counts harvested rows released before the stop; the summarizer's residuals-per-full-row column uses `lp_full_relations` plus 0-LP decompositions for both arms.

# k = 4 (item 5): large primes in `run_k4_la`, paired against the plain run

All numbers [pcc:unverified]. Raw: `k4/paired_a.json` (p = 269, 521), `k4/paired_b.json` (p = 769); summaries `k4/summary_k4.txt`, `k4/extra_k4.txt`; summarizer `summarize_k4_paired.py`. Original scratch copies: `/tmp/claude-0/-home-user-workspace/c8bb5f86-f825-52e5-8fb5-701f80d9a4ff/scratchpad/next/harvester-k4/`.

## What was built

`gaudry_quartic::run_k4_la_opts(p, seed, rho_runs, &K4LaOptions)`; `run_k4_la` is the default-options call (a unit test checks that `la_ops` and `residuals` are identical to the options form with defaults). Small base = `ceil(|F|^0.75)` (`small_exp`; also `small_frac`, `small_base`). Base points with index >= small are large primes: each verified MITM decomposition is kept if it has at most 3 of them (4 = all four large are discarded) and is fed to item 1's `GainForestHarvester` (used in place from `gaudry_cubic`, unchanged). Harvested rows and direct rows go to the same `square_core` + `wiedemann_u64` + `[d]G = Q` check as before. Harvester multiplications are counted in `la_ops` (split into `merge_ops` and `wiedemann_ops`). Example flags: `--arm plain|lp|paired --lp-exp 0.75 --lp-frac f --lp-small s --max-lp 3`. New test `k4_large_prime_arm_recovers_the_planted_logarithm` passes (3 of 3 k4 tests pass).

## Run

`--sizes 269,521,769 --seeds 2 --rho-runs 8 --arm paired`, run under `lead_sweep.py watch` (4 GiB; peak RSS 0.33 and 0.57 GiB; no kills or timeouts; wall 1459 s for 269+521 and 3307 s for 769, two processes at RAYON_NUM_THREADS = 2). Both arms of a (p, seed) share the curve, base, residual stream and the 8 rho runs. All 12 runs recovered the planted log, group-checked. **p = 1033 was not run**: the 769 pair alone took 55 min, so 1033 does not fit in the 90 min budget.

## Result (mean over 6 pairs; paired difference = mean of per-pair lp - plain, +- SE)

| quantity | plain | lp | paired lp - plain |
|---|---:|---:|---:|
| **r** (own rho, the registered statistic) | 0.532 +- 0.027 | **0.279 +- 0.032** | -0.254 +- 0.020 (z -13.0) |
| r (rho pooled over 48 runs, S = 1.320) | 0.524 +- 0.020 | 0.269 +- 0.016 | -0.255 +- 0.027 |
| LA ops, mod-n mults (merge + Wiedemann) | 1.27e6 | 7.2e5 | -5.6e5 +- 1.6e5 (z -3.6) |
| unknowns (core) | 236 | 65 | -171 +- 32 |
| rows fed to the filter | 264 | 66 | -198 +- 37 |
| row weight (core) | 5.00 | 41.1 | +36 +- 6.8 |
| residuals | 6 332 | 9 247 | +2 916 +- 771 (z 3.8) |
| residuals per row fed | 23.8 | 133 | +110 +- 14 |
| MITM relation-phase group ops | 1.27e9 | 1.91e9 | +6.4e8 +- 2.8e8 (z 2.3) |

Per curve, r plain / r lp: p = 269: 0.413/0.174, 0.544/0.235; p = 521: 0.560/0.322, 0.585/0.273; p = 769: 0.501/0.267, 0.591/0.401.

**Pre-registered report.** r_lp = 0.279 +- 0.032 (N = 6). 0.518 - r_lp = 0.239 = 7.6 SE (own rho) and 15.2 SE with pooled rho. So r falls below 0.518 by more than 2 standard errors, on these three sizes. The registered 0.518 was measured on a different seed set (2 per size at 4 sizes, 16 rho runs); the plain arm here gives 0.532 +- 0.027, consistent with it, and the paired difference is the cleaner comparison.

## What the numbers also say (read before quoting r)

- **r leaves out the relation phase, and the lp arm's relation phase is bigger.** It needs 1.46x the residuals and 1.5x the MITM group ops (z 2.3), because only 0.75-power of the base are unknowns and 4-large-prime decompositions (21-36 % of the verified decompositions, from `lp_histogram` vs `accepted` in `k4/extra_k4.txt`) are thrown away. The relation phase is 1 053-3 700 x rho (plain) and 1 449-5 708 x rho (lp) by this accounting, i.e. thousands of times the linear algebra. So the total cost (relation + LA) is higher in the lp arm; the claim is about the linear-algebra phase only, as r defines it.
- **The gap closes with p.** r_lp by size: 0.205, 0.298, 0.334 (own rho); plain: 0.479, 0.573, 0.546. The core row weight of the lp arm grows as n^0.22 +- 0.03 (22-24, 36-47, 52-64), and LA ops as n^0.558 +- 0.028 against 0.478 +- 0.022 for plain (the plain figure matches §11.19's 0.479). With three sizes and 6 pairs the exponents are rough, but at 0.56 the lp linear algebra would pass plain's cost on a longer ladder; the 0.5 scaling that gives r_inf is not what the lp arm shows.
- Cycle structure: all harvested rows came from the sink-attached component (pinned; balanced rows 0 or 1 per run), mean 31-110 relations composed per row (from `mean_cycle_len`), no inconsistent equations, no 3-edges left buffered. This is the same root-to-root combination item 1 found at k = 3, not a shortest cycle. Row weight 41 against 5 is the cost.
- 0-LP rows are 0-2 per run, so almost every row is harvested.

## Limits

3 sizes, 2 seeds each, 8 rho runs per curve; one small-base rule (|F|^0.75) and one cap (3) were tried; no fraction sweep. No minimum-weight cycle basis. Nothing here is an end-to-end S, a claim about rho at any size, or a deployment extrapolation. The `r_inf = 0.518` it is compared with is a statistic of the plain method's LA at these sizes. No push, PR or remote write was made.
