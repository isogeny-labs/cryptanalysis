---
title: "n = 83: Z[τ] closure + index lift, against the index-lift row, end-to-end cold"
date: 2026-10-19
---

# n = 83: Z[τ] closure + index lift, against the index-lift row, end-to-end cold

**Status (2026-10-20): Tier 1 [run 39335956567](https://github.com/aburan28/cryptanalysis/actions/runs/39335956567) finished; verdict improvement.**
The [protocol](protocol.json) and the [schedule](schedule.json) were
committed before any Tier 1 timing (the run started on commit `9fc17f76c`),
and the run is archived in [`run_github_39335956567/`](run_github_39335956567/).
The frozen primary is R = E2E(kPI, cPI) / E2E(kM38I, cM38I) =
**7.6558 [7.2192, 8.1103]**. See "Result". Every number outside "Result" that
is not from the parents' archived Tier 1 runs is either from the frozen
protocol or from the cloud-agent VM, where it is a **local diagnostic**, not
timing evidence.

## Question

The n = 83 a = 1 baseline row is the **index-lift producer**
(`koblitz-n83-indexlift-20261019`, PR #981, run 39290913632): the rank-probe
producer with `KIC_INDEX_CANON=lift`. End-to-end cold is 165.2 s (shared rank
stage 148.4 s + cold 16.8 s), `S` 6.37, gap to the tuned rho rT770 62.9.

The Z[τ]-multiplier closure (`koblitz-n83-closure-20261019`, branch
`claude/n83-closure`, frozen commit 3761fd260, run 39305259093) measured
6.444 [6.099, 6.785] end to end. That comparison was against the
**rank-probe** producer, not the current row, so it cannot replace the row:
docs/ic/BASELINES.md asks for an improvement over the row on the same
instances.

The two changes act on different stages. The closure cuts the rank stage's
columns from 600 to 16. Index lift speeds up the root-index build, which every
cold and rank process pays. They should stack. This run asks: does the
closure, built on top of the index-lift producer, lower the **end-to-end
cold** cost of the index-lift row on new targets and new rank seeds? Every
relation must be checked in the group, every column log and scalar verified,
the probe law kept, and the index-lift layout reproduced byte for byte. It is
an iteration under AGENTS.md "Success criterion". A promoted result becomes
the new n = 83 row.

![Design (from the frozen protocol; not a result). Source:
[figures/design.tex](figures/design.tex), vector:
[figures/design.pdf](figures/design.pdf).](figures/design.png)

## The producer: was a code change needed?

`KIC_INDEX_CANON=lift` is a runtime selector of the **rank-probe** producer
(`INDEX_CANON_LIFT`, parsed from the environment). Both the closure producer
and the index-lift producer derive from that producer, so the closure
producer with `KIC_INDEX_CANON=lift` already builds the candidate's index.
But the index-lift row's own producer adds two layout digests
(`stored_states_blake3`, `table_slots_blake3`), `lift_plant` and
`KIC_SCAN_SELFTEST`. The closure producer lacks the layout digests, so it
cannot carry index-lift's layout gate, and it is not the row's binary.

So the producer is a **composition with no new code**.
[`make_online_source.py`](make_online_source.py) applies the closure's four
counted replacements (`closure_edits`, imported from
[`make_closure_source.py`](make_closure_source.py), not re-typed) to the
index-lift producer's text, plus one header comment. Both parents' derivations
are verbatim files here, and each derivation's digest is checked on every
build:

| text | derivation | frozen sha256 |
| --- | --- | --- |
| rank-probe producer | `make_rankprobe_source.py` + five parents | `d4394df3...` (PR #980) |
| index-lift producer (the row) | `make_indexlift_source.py` (PR #981 verbatim) | `7df72603...` |
| closure producer | `make_closure_source.py` (3761fd260 verbatim) | `8916e034...` |
| **this producer** | `make_online_source.py` | **`1d328b2e...`** (`protocol.json`) |

The derivation also checks that the two edit sets commute, up to the header
comments. Applying index-lift's nine edits to the closure text gives the same
program. The diff from the index-lift producer is the closure's four
replacements (59 diff lines). One binary, `ic_online_closure_indexlift_r770`,
runs every IC arm, so the baseline and the candidate share the per-probe code.

## Exactness checks (before freezing; local, cloud-agent VM)

**Same layout as index-lift on B's header, and the closure's frozen
identities on its bases**
([`inputs/local_layout_test.json`](inputs/local_layout_test.json),
`smoke/exactness_local.py cold`). Q0 ran with each base's verified table and
both index canonicalizers, six processes:

| base | logical-state blake3 / map digests / root entries | layout digests (stored states / table slots) | Q0 relation, scalar, probes |
| --- | --- | --- | --- |
| K600, selected and lift | B's `baf46d5a...`, 29,878,182 | **`d8cfe443...` / `5f53764e...` = index-lift's frozen values**, both canonicalizers | B's archived, 1,987,852 |
| M38, selected and lift | closure protocol's `09251580...`, 30,366,551 | `f7a8d6b8...` / `6c08c6c2...`, one pair for both canonicalizers | closure's frozen, 1,612,533 |
| M10, selected and lift | closure protocol's `ebf4f41e...`, 29,821,794 | `c90b501b...` / `4973cfe5...`, one pair | closure's frozen, 2,130,165 |

The M38 and M10 layout pairs are frozen into `protocol.json`
(`online.bases.*.layout_digest`). On every base, lift_scan builds the same
slot array as the selected canonicalizer. This is index-lift's argument,
which now holds on the closure bases as well.

**Archived Tier 1 rank processes reproduced exactly with
`KIC_INDEX_CANON=lift`**
([`smoke/exactness_rank_local.json`](smoke/exactness_rank_local.json)):

- **kPI of the index-lift run** (block K1, seed 401, point s000 of
  `indexlift-cold-v1`, B's header). The relation digest, all 600 per-attempt
  probe counts, root calls, point-addition and frame counters, index and
  layout digests, target relation, scalar and probes are equal. The written
  table equals B's.
- **kM38 of the closure run** (block K1, seed 801, point s000 of
  `closure-cold-v1`, M38 header). This archived process used the selected
  index build. The relation digest, all 16 per-attempt probe counts, root
  calls, counters, index digests, target relation, scalar and probes are
  equal. The written table equals the frozen verified M38 table.

So the derived producer reproduces index-lift on B's header (cold and rank)
and the closure on M38 (cold and rank), field for field.

**Tests** ([`smoke/cargo-test-online.txt`](smoke/cargo-test-online.txt)):
all 21 producer tests pass, including the closure's
`closure_multiplier_is_its_label` and index-lift's two layout tests, plus the
4 tuned-rho tests. The 11 verifier unit tests (`test_verify_receipt.py`)
pass. The workflow runs both before any timing.

## Frozen Tier 1 design

One GitHub `ubuntu-24.04` runner, one pinned CPU, Tier 1 counters, one fresh
process per run. Every IC arm runs `ic_online_closure_indexlift_r770` with:

- `KIC_INDEX_CANON=lift`;
- the full scan self-test;
- lift_scan target keys, the Feistel order and the prefetch pipeline;
- the 16-byte compact table over the folded index;
- the frame rank loop.

| Arm | Kind | Base | Role |
| --- | --- | --- | --- |
| `cPI` | cold | K600 + B's table | **baseline** cold (the index-lift row's cPI) |
| `kPI` | rank | K600 | **baseline** rank stage (the row's kPI; 600 attempts), blocks K1, K5, K9, K13 |
| `cM38I` | cold | M38 + its verified table | **primary candidate** cold |
| `kM38I` | rank | M38 | **primary candidate** rank stage (16 attempts), all 16 blocks |
| `cM38Iaa`, `kM38Iaa` | cold, rank | M38 | A/A of the primary |
| `kM38IX` | rank | M38 | planted positive control (`frame_plant`, about 1.8x per attempt in run 39305259093), blocks K1, K5, K9, K13 |
| `cM10I`, `kM10I` | cold, rank | M10 | pre-registered secondary (60 attempts), the 8 odd blocks; never decides |
| `rT` | rho | — | tuned rho rT770 (Fold/64/DP6), seed 1010000 + point seed |

- **Cold panel.** 20 new public points (`inputs/cold_targets.json`, role
  `closureindexlift-cold-v1`, [`make_targets.py`](make_targets.py)). They are
  disjoint from:
  - every earlier n = 83 panel of the law (Q0, B's panel, scan-order,
    combined, probe-pipeline, state-fold, table-filter, stacked, rank-cut,
    rank-probe, index-lift, the 64 n131 `eval` points);
  - the panels of the lanes n83-rotkey, n83-k899, n83-onlineframe,
    n83-closure, n83-knownlog and n83-blrp (`rotkey-cold-v1`, `k899-cold-v1`,
    `onlineframe-v1`, `closure-cold-v1`, `knownlog-cold-v1`,
    `blrankprobe-cold-v1`).

  Every panel was regenerated and checked equal to the file committed in its
  worktree. A role-agnostic scan of 211 input files in those worktrees
  (13,731 points) found no shared point. No x-coordinate of the panel occurs
  in origin/main's `experiments/` or `research/`. No scalar is known.
- **Rank blocks.** K1–K16 use the new seeds 1101–1116. Already used on
  n = 83: 7, 101–102, 201–204, 301–309, 401–404, 501–504, 701, 801–816,
  901–904.
- **Order.** O1 (Q0 on cPI, cM38I and cM10I), then C1 K1 … C16 K16 C17 … C20.
  The order within each segment is shuffled with new seeds. 151 runs; time
  guard 300 minutes.

**Primary (pre-registered).**

- R = E2E(kPI, cPI) / E2E(kM38I, cM38I), where E2E(k, c) = the mean rank
  stage of k over its blocks plus the mean cold time (setup + one-target
  online) of c over the 20 points.
- Bootstrap: 10,000 draws, seed 20261219. Each rank arm's blocks are
  resampled, then its attempts within each drawn block, independently for the
  two arms. The points are resampled, paired across cPI and cM38I.
- **Improvement** iff the 95% lower bound > 1; regression iff the upper
  bound < 1; otherwise not separated.
- **Invalid** if any gate is false *or unknown*, any control fails, or any
  scheduled row is missing.

**Controls.**

- A/A: E2E kM38I+cM38I / kM38Iaa+cM38Iaa and cold cM38I / cM38Iaa must both
  be inside [0.97, 1.03].
- Planted timing control: the per-attempt ratio kM38IX / kM38I must have its
  lower bound above 1.
- Planted exactness control: the three closure corruptions (a label, a
  duplicated orbit, a log) must be rejected by `verify_closure.py` on both
  closure bases before timing.

**Gates.** These are the closure experiment's gates plus index-lift's layout
gate:

1. Before timing (`check_log_table.py`):
   - B's table re-verified in the pinned oracle;
   - each closure header regenerated to its frozen SHA-256 and passed by
     `verify_closure.py`, with the planted corruptions rejected;
   - each closure table checked: [L_c]G = R_c for every column and
     [w·L_c]G = α(R_c) for every orbit;
   - the closure logs equal B's archived logs of the same R_c.
2. Every IC process:
   - `KIC_INDEX_CANON=lift` recorded, 0 roots checked against the selected
     canonicalizer, and the full scan self-test;
   - its base's frozen base hash, columns, orbits, states, slots, root
     entries, logical-state and table-map digests;
   - **its base's frozen layout digests.** For the baseline arms these are
     index-lift's `d8cfe443...` / `5f53764e...`.
3. Per point: one scalar across every IC process (all three bases) and rT,
   replayed in the oracle. One relation and one probe count per point and
   base. One index and layout digest set per base, equal to the frozen one.
4. Q0: cPI gives B's archived identity (1,987,852 probes). cM38I and cM10I
   give the closure protocol's frozen Q0 identities.
5. Rank arms:
   - full rank, 0 failures, one frame per attempt;
   - the written table equal to the base's frozen verified table, log for
     log;
   - per block, identical relation digests, probe vectors, root calls and
     counters across kM38I, kM38Iaa and kM38IX.
6. Probe law: kM38I's pooled probes per relation over r / (166 E) must lie in
   [0.80, 1.20] over 256 attempts. kM10I's band is reported only.
7. Receipt integrity, fail closed (index-lift's hardened verifier on main):
   - every raw record decodes;
   - its SHA-256 equals the wrapper's `raw_result_sha256`;
   - its arm, kind, panel, point and seed equal the schedule's;
   - an unknown gate is a failure.

## Power

The power check is [`power_check.py`](power_check.py), with results in
[`analysis/power.json`](analysis/power.json). Its prior,
`inputs/power_prior.json`, is built by `make_power_prior.py` from the
parents' archived Tier 1 runs:

- **Closure run 39305259093:** the kP blocks (600 attempts), the kM38 /
  kM38aa blocks (16 attempts; their ratios are the process factors), the kM10
  blocks, and the cP / cM38 / cM10 cold times.
- **Index-lift run 39290913632:** the cold factor L = mean cPI / mean cP =
  0.7476, applied to every cold arm here, since all of them build with
  lift_scan.

There were 200 simulations per cell, each with 300 bootstrap draws.

| end-to-end effect | M38 (16 blocks) | M10 (8 blocks) |
| --- | ---: | ---: |
| 1.00 (no gain; type I) | 0.005 | 0.02 |
| 1.10 | 0.15 | 0.275 |
| **1.50 (minimal effect of interest)** | **0.995** | **1.00** |
| 2.00 | 1.00 | 1.00 |
| 4.00 | 1.00 | 1.00 |
| modelled (both changes as measured) | 1.00 (median R 7.98) | 1.00 (median R 5.13) |

**Expected effect.** At the parents' archived means the model gives
(108.0 + 12.0) / (2.75 + 12.3) s = **about 8.0** for M38 and 5.1 for M10.
This is an estimate, not a claim. It is higher than the closure's 6.4
because index lift shrinks the cold path, which is most of the candidate's
remaining cost, and it uses the closure run's faster runner. The probe-law
gate passes at the true law with probability 0.9955. It rejects a law 1.5x
worse with probability 0.9965 (256 attempts; archived kM38 ratio 0.962).

**Runtime estimate.** About 1.1 hours: build and tests 15 min, cold segment
about 55 s, rank block about 190 s with kPI and about 45 s without.

## Local runner smoke (correctness only)

[`smoke/README.md`](smoke/README.md) and
[`smoke/correctness_smoke.json`](smoke/correctness_smoke.json): segments
O1, C1 and K1 through `run_schedule.py` and `arm.py`, then
`verify_receipt.py --correctness-only`.

- `check_log_table.py` passes for K600, M38 and M10, and the planted
  corruptions are caught.
- All 13 rows are valid, covering every arm.
- Every correctness check passes on them:
  - one scalar per point across all three bases and rT, replayed in the
    oracle;
  - Q0 equal to the archived and frozen identities on all three bases;
  - one index and layout digest set per base, equal to the frozen one;
  - identical rank digests and probe vectors across kM38I, kM38Iaa and
    kM38IX;
  - every rank table equal to its frozen verified table.
- The one exception is the probe-law band on this single block (kM38I 1.566
  over 16 attempts). The frozen gate pools 256 attempts. The closure's
  per-block ratios ranged from 0.58 to 1.35, and its run pooled 0.963.
- The protocol was frozen before this smoke and was not changed after it.
  The smoke used the frozen block K1. Its probe counts are deterministic and
  will recur in Tier 1.

## Result

The run was started by the workflow's path-filtered push trigger (a
`workflow_dispatch` call returned 403 for the integration that launched it),
at the frozen commit, on one `ubuntu-24.04` runner (`runnervm8k3b6`, 4 vCPUs,
kernel 6.17.0-1022-azure, one pinned CPU; `host-probe.json`). The run
executed the 151 scheduled rows (`schedule-exit.txt`: 0).

**All gates pass; the run is valid.** All 151 scheduled rows are present and
valid (151 valid, 0 invalid, 0 skipped by the time guard; the guard did not
trip; 20/20 points, 4/4 kPI blocks, 16/16 kM38I blocks, 8/8 kM10I blocks):

- Before timing: B's table and both closure headers and tables re-verified in
  the pinned oracle (`log-table-check.json`: K600, M38 and M10 all PASS), and
  the planted closure corruptions rejected.
- One scalar per point across every IC process (all three bases) and the
  tuned rho, replayed in the oracle; one relation and one probe count per
  point and base.
- One index and layout digest set per base (K600, M38, M10), each equal to the
  frozen one, so the index-lift layout (`stored_states_blake3`,
  `table_slots_blake3`) is reproduced in every IC process.
- Q0 equal to the archived identity (cPI) and to the closure protocol's frozen
  identities (cM38I, cM10I).
- Every rank table equal to its frozen verified table; identical relation
  digests, probe vectors, root calls, point-addition and frame counters across
  kM38I, kM38Iaa and kM38IX in every block (0 fallback states, 0 irregular
  inputs, 0 rows without gain).
- **Probe law:** kM38I pooled 1.0304 [0.8728, 1.1825] over 256 attempts, inside
  the frozen band [0.80, 1.20] (pass).
- Receipt integrity (fail-closed verifier), `receipt_matches_schedule`, no
  contention flags, no problems.

`verify_receipt.py` re-run on a **copy of the whole receipt directory** (with
`result.json`, `result_table.md` and `verify-stdout.json` removed first, and
the gitignored `snapshots/r770` oracle present) reproduces
`panel/result.json`, `panel/result_table.md` and the verifier's stdout byte
for byte.

![Frozen ratios with 95% bootstrap intervals, all from `result.json`
([source](figures/result.tex), [vector](figures/result.pdf), rendered by
[`make_figures.py`](make_figures.py)).](figures/result.png)

### Primary (frozen rule)

Improvement iff the 95% lower bound of R = E2E(kPI, cPI) / E2E(kM38I, cM38I)
exceeds 1.

| Statistic | Estimate [95%] | Reading |
| --- | --- | --- |
| **R = E2E(kPI,cPI) / E2E(kM38I,cM38I)** (20 points; 4 and 16 rank blocks) | **7.6558 [7.2192, 8.1103]** | **improvement** (lower bound above 1) |
| A/A E2E kM38I+cM38I / kM38Iaa+cM38Iaa | 1.0001 [0.9979, 1.0023] | pass (inside [0.97, 1.03]) |
| A/A cold cM38I / cM38Iaa | 1.0006 [0.9979, 1.0032] | pass (inside [0.97, 1.03]) |
| A/A rank per attempt kM38I / kM38Iaa (n=256) | 0.9981 [0.9948, 1.0014] | reported |
| planted rank per attempt kM38IX / kM38I (n=64) | 1.9607 [1.9470, 1.9747] | pass (lower bound above 1) |
| planted exactness corruptions (label, duplicated orbit, log) | rejected on both closure bases before timing | pass |

End-to-end cold means: kPI + cPI = 143.68 + 16.84 = 160.52 s;
kM38I + cM38I = 4.01 + 16.96 = 20.97 s. The expected effect from the power
check was about 8.0 (an estimate, not an input); the measured 7.66 is close.
The saving is the rank stage (35.83x, 16 columns instead of 600); the cold path
is unchanged.

### Secondaries (none changes the verdict)

**M10I** (60 columns, 8 odd blocks; never decides):

| Quantity | Estimate [95%] |
| --- | --- |
| E2E kPI+cPI / kM10I+cM10I | 4.9504 [4.5846, 5.3402] |
| E2E kM10I+cM10I / kM38I+cM38I | 1.5465 [1.4482, 1.6520] |
| cold without rank cPI / cM10I | 1.0063 [0.9880, 1.0242] |
| setup cPI / cM10I | 1.0074 [1.0038, 1.0114] |
| index build cPI / cM10I | 1.0025 [0.9996, 1.0054] |
| online cPI / cM10I | 0.9638 [0.5122, 1.9636] |
| peak RSS cPI / cM10I | 0.9998 [0.9997, 1.0000] |
| rank stage kPI / kM10I | 9.1570 |
| rank stage kM10I / kM38I | 3.9124 |

**Per-phase breakdown** (means over 20 points; ratio is cPI over the candidate
arm, below 1 = the candidate is slower):

| Phase | cPI | cM38I | cM10I | cPI / cM38I [95%] |
| --- | ---: | ---: | ---: | :--- |
| cold without rank (ms) | 16,839.6 | 16,956.7 | 16,734.6 | 0.9931 [0.9837, 1.0035] |
| setup (ms) | 16,415.5 | 16,698.9 | 16,294.7 | 0.9830 [0.9806, 0.9855] |
| index build (ms) | 14,060.7 | 14,416.6 | 14,025.1 | 0.9753 [0.9731, 0.9776] |
| online (ms) | 424.04 | 257.85 | 439.96 | 1.6445 [1.0217, 2.7261] |
| peak RSS (MiB) | 1,788.3 | 1,809.3 | 1,788.6 | 0.9884 [0.9883, 0.9885] |
| online probes (mean) | 1,900,251 | 1,150,602 | 1,978,465 | |
| rank stage, mean per arm (ms) | 143,681.3 (kPI, 4 blocks x 600) | 4,010.5 (kM38I, 16 x 16) | 15,690.9 (kM10I, 8 x 60) | 35.83x |

The cold path is not improved by the closure: setup is 1.7% and the index
build 2.5% slower at M38 (the same direction as the closure run's 0.976 cold
without rank). The online phase is 1.64x faster at M38 (fewer mean probes,
1,150,602 against 1,900,251), but the interval is wide ([1.02, 2.73]) and it
does not move the verdict.

**Rank-stage share of E2E cold:** kPI 89.5%, kM38I 19.1%, kM10I 48.4%.
Rank-stage time per probe: 142.55 (kPI), 143.08 (kM38I), 143.36 (kM38Iaa),
280.63 (kM38IX), 142.45 (kM10I) ns, so the per-probe code is the same across
arms and the planted arm costs 1.96x per attempt.

**Probe law** (pooled mean probes per relation over r / (166 E)):

| Arm | Estimate [95%] | Attempts | Role |
| --- | --- | ---: | --- |
| kM38I | 1.0304 [0.8728, 1.1825] | 256 | gate, band [0.80, 1.20]: pass |
| kPI | 0.9715 [0.9176, 1.0230] | 2400 | reported |
| kM10I | 1.0605 [0.9475, 1.1930] | 480 | reported; the upper bound is above the 1.15 end of its 0.85-1.15 band |

**S** (cost over this run's measured rT770 step, 281.09 ns, per sqrt(r); one
unit is 26,021.1 ms):

| Arm | E2E cold | cold without rank | online | rank stage |
| --- | ---: | ---: | ---: | ---: |
| kPI + cPI | 6.1689 | 0.6472 | 0.016296 | 5.5217 |
| kM38I + cM38I | 0.8058 | 0.6517 | 0.009909 | 0.1541 |
| kM10I + cM10I | 1.2461 | 0.6431 | 0.016908 | 0.6030 |
| cM38Iaa | | 0.6512 | 0.009869 | |

Delta S end-to-end cold, kPI + cPI to kM38I + cM38I = -5.3631. The tuned
rho's own `S` in this run: cold 0.11753, online 0.10717 (mean rT770 cold
3,058.2 ms, online 2,788.7 ms).

**Gap to tuned rho rT770** (IC / rho; 20 points; distance remaining, not a
gate):

| Arm | End-to-end cold [95%] | Online [95%] |
| --- | :--- | :--- |
| kPI + cPI (baseline) | 52.49 [43.95, 63.53] | 0.1521 [0.0980, 0.2158] |
| kM38I + cM38I (candidate) | **6.856 [5.799, 8.193]** | 0.0925 [0.0594, 0.1352] |
| kM10I + cM10I | 10.60 [8.886, 12.83] | 0.1578 [0.0790, 0.2707] |

**Host class.** `ubuntu-24.04` GitHub runner `runnervm8k3b6` (Microsoft
virtualization, x86_64, 4 online CPUs, affinity 0-3, one pinned execution CPU
0, kernel 6.17.0-1022-azure). The same host name as the index-lift and closure
runs, but the runner state is a different instance, so cross-run absolute times
differ.

### Limits of this result

- Tier 1, instance scope: one runner, 20 cold points, 4, 16 and 8 rank blocks,
  one fresh process per arm per point. The primary's interval is over points,
  blocks and attempts; it does not cover another host class. This run was not
  replayed.
- Wall time on one host class. The saving is the number of rank attempts (16
  or 60 against 600), not the per-probe cost (142.55 ns for kPI against 143.08
  for kM38I).
- **Factor-base construction is charged to no arm** (the n = 83 convention).
  The closure header costs two small scalar multiplications per added
  orbit; the omission is common to both arms, so R > 1 holds for any X >= 0,
  but 7.6558 is an upper bound on the every-phase ratio.
- The kM38I probe law is a 256-attempt pooled estimate with a wide interval
  ([0.8728, 1.1825]); it passes its band but is not tight.
- This run's baseline arm (160.5 s, S 6.17) differs from the index-lift run's
  (165.2 s, S 6.37): a different run, instance set, rank seeds and runner
  state. The paired ratio R is within this run.
- The closure's earlier 6.4444 [6.0993, 6.7853] was over the rank-probe
  producer; this paired result over the index-lift row supersedes it as the
  comparison against the current row.

## Not included

- Factor-base construction is charged to no arm, the convention of every
  n = 83 row. A closure header holds B's first K' orbits plus (M − 1)·K'
  images α(R_c), each costing two small scalar multiplications.
- index-lift's secondary cPIT (sampled scan self-test) and its planted
  `lift_plant` are not arms. Here every arm runs the full self-test, and the
  layout gate checks the index-lift change on every process.

## Files

| File | Role |
| --- | --- |
| `protocol.json`, `make_protocol.py`, `schedule.json`, `make_schedule.py` | frozen protocol, its builder, frozen run order |
| `make_online_source.py` | the composition: closure edits on the index-lift text; checks all three parent digests and that the edits commute |
| `make_indexlift_source.py`, `make_closure_source.py`, `make_rankprobe_source.py` + five parents, `online/`, `lift2/` | the parents' derivations, verbatim; the crate; the two-limb canonicalizer |
| `make_closure_base.py`, `verify_closure.py`, `inputs/factor_logs_n83_closure_*.json`, `inputs/local_decisive_test.json`, `inputs/parent_closure_protocol.json` | the closure experiment's header builder, verifier, verified tables, local record and frozen protocol (commit 3761fd260), verbatim |
| `inputs/local_layout_test.json`, `smoke/exactness_local.py`, `smoke/exactness_rank_local.json` | the exactness checks above |
| `restore.py`, `check_log_table.py` | restore and digest-check crypto 770f6a69, the closure headers and every local file; verify every table and closure before timing |
| `make_targets.py`, `inputs/cold_targets.json` | the new cold panel |
| `make_power_prior.py`, `inputs/power_prior.json`, `power_check.py`, `analysis/power.json` | power prior (runs 39305259093 and 39290913632), simulation, result |
| `arm.py`, `run_schedule.py` | one arm per pinned process; the schedule runner |
| `verify_receipt.py`, `test_verify_receipt.py` | gates, statistics, fail-closed decision rule; its tests |
| `figures/design.*`, `make_figures.py`, `figures/result.*` | design diagram; result figure (TikZ source, PDF, PNG) |
| `run_github_39335956567/` | the archived artifact: allocation, builds, raw runs, `panel/result.json`, `panel/result_table.md` |
| `README.pdf` | this report: `pandoc README.md -o README.pdf --pdf-engine=pdflatex -H report_header.tex --lua-filter report_filter.lua -V geometry:margin=2cm -V fontsize=10pt -V colorlinks=true` |
