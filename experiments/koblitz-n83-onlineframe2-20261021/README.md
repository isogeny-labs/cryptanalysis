---
title: "n = 83: the online frame loop in the current producer, exact change only (Tier 1 design)"
date: 2026-10-21
---

# n = 83: the online frame loop in the current producer, exact change only (Tier 1 design)

**Status (2026-10-21): run
[39527549698](https://github.com/aburan28/cryptanalysis/actions/runs/39527549698)
valid; verdict improvement, R = 1.0165 [1.0110, 1.0221] over 64 alternating
pairs ([Result](#result)).** The
[protocol](protocol.json) (SHA-256 `50e50718...`) and the
[schedule](schedule.json) (`6c84dfe5...`) were committed before any Tier 1
timing. Every number in the design sections (Why this run to Power and
runtime) that is not from an archived run is a design estimate or a local
correctness diagnostic from the shared cloud-agent VM, not timing evidence.
The result is in its own section, and the design text is unchanged.

## Why this run

The n = 83 a = 1 baseline row is the **round-2 index-build producer**:

- experiment [`koblitz-n83-indexbuild2-20261020`](../koblitz-n83-indexbuild2-20261020/README.md);
- PR #1009, run 39464544962;
- source `4008a47a...`, binary `ic_online_indexbuild2_r770`;
- Tier 1-qualified at 1.1169 [1.1110, 1.1231].

The row's rank stage already runs the **frame loop** (`PIPE_FRAME`: point
addition in the target's Frobenius frame), at 148 ns per probe in that run.
Its one-target **online** scan still runs the batched S3 solve
(`PIPE_COMPACT`), at 219.5 ns per probe. In the row's 36 pairs the online
interval was 332.4 ms of 11,537 ms end to end (2.9%).

[`koblitz-n83-onlineframe-20261019`](../koblitz-n83-onlineframe-20261019/README.md)
(PR #988) added `KIC_ONLINE_SOLVE=frame`, which runs the online scan on the
frame loop. It measured 1.5733 [1.5714, 1.5753] online on the older
rank-probe producer. That run used **one pair per point**, and its
qualification note
([`QUALIFICATION.md`](../../reviews/pr-988-onlineframe-qualification-20261019/QUALIFICATION.md))
records that it is therefore not a qualified Tier 1 speedup.

This experiment brings the change into the current producer, proves it
exact, and measures it **end to end over the current row** with repeated
alternating pairs.

## 1. Integration route: a counted derivation (no existing selector)

`KIC_ONLINE_SOLVE` is **not** in the current row's lineage:

- the row's chain is rank-probe (`d4394df3...`), then index-lift +
  closure (`1d328b2e...`), then index-build (`bc6a31c7...`), then round 2
  (`4008a47a...`);
- PR #988 branched off rank-probe, and no later producer imported it;
- the round-2 source has no `KIC_ONLINE_SOLVE`.

So the change needs code, and it is ported as a counted derivation:
[`make_onlineframe2_source.py`](make_onlineframe2_source.py). It does the
following:

1. It re-derives the row's producer with the parent's
   `make_indexbuild2_source.py` (verbatim). That script re-derives
   `bc6a31c7...` and `1d328b2e...` through their verbatim chains and runs
   its own inverse check.
2. It requires `4008a47a...`.
3. It applies **9 counted replacements**, each of which must occur exactly
   once:
   - one header comment;
   - the **seven wide-module replacements of PR #988, imported** (not
     re-typed) from [`make_onlineframe_source.py`](make_onlineframe_source.py).
     That file is PR #988's `make_online_source.py`, byte for byte. Its
     digest must equal the online-frame protocol's frozen
     `local_sha256.online_derivation` (`ca1de33b...`), and that protocol's
     own SHA-256 (`bd1d7fbb...`) is pinned in `restore.py`;
   - one appended test module (`onlineframe2_tests`).
4. `check_inverse()` undoes the replacements on every derivation and must
   get the parent's bytes back.

The derived source is **`f07bcb1e...`**
(`koblitz_orbit_dlp_fast_online_onlineframe2.rs`), and the binary is
`ic_online_onlineframe2_r770`. Both IC binaries are built by one
`cargo build` from the parent's lock file.

Every anchor string of PR #988's edits occurs exactly once in the round-2
text. None of them overlaps the closure, index-lift, index-build or round-2
edits. The inverse check proves that the composition is the parent plus
these replacements and nothing else.

**What the selector does** (read only by the online target scan):

| `KIC_ONLINE_SOLVE` | online probe loop |
| --- | --- |
| `s3` (default, also when unset) | the parent's `scan_state128_filtered::<CANON_LIFT, PIPE_COMPACT>`, unchanged |
| `frame` | `extract128::<CANON_LIFT, ORDER_FEISTEL, PIPE_FRAME>`: the same function and const parameters the row's rank stage runs under `KIC_RANK_SOLVE=frame`, on the same M38 closure index |
| `frame_s3plant` | planted control: on every state the scan reaches, the S3 loop is redone first and compared with the frame loop (a panic on any difference). The compared outputs are the relation, the probe counter, the root calls, the relation checks, and every candidate's key pair up to the pair order. The S3 result is discarded. |

Each target record gains `online_solve` and `online_counters`. The summary's
rank counters are read before the online scan, so they remain the rank
stage's own.

[`restore.py`](restore.py) checks the following on every build:

- the parent protocol (`5cee1a72...`) and the online-frame protocol
  (`bd1d7fbb...`);
- side A's producer equals the parent's frozen `4008a47a...`, and the two
  grandparents equal `bc6a31c7...` and `1d328b2e...`;
- both closure headers;
- the 28 files copied byte for byte from the parent (`VERBATIM`);
- every local pin in `protocol.json`.

## 2. Exactness

**Why the output is exact.** E is defined over F_2, so
φ(x, y) = (x², y²) is a group automorphism, and
T ± φ^s(R) = φ^s(φ^(−s)(T) ± R). The two roots of S3(x(φ^s R), x(T), X)
are exactly x(T + φ^s R) and x(T − φ^s R).

The frame loop computes those two field elements by point addition from the
stored root's (x, y), with one batched inversion per state. It then applies
φ^s as a rotation of the normal-basis word. Each candidate's partner words,
keys and shifts are therefore the S3 loop's, possibly in the other order, at
the same probe positions.

- Exceptional inputs go to the S3 solver.
- At a hit, the frame loop solves that candidate's S3 input and evaluates
  the pair in the S3 order.

So the first lifted relation, its probe count, the root calls and the
relation checks are the S3 loop's. Setup, the root index, the self-test and
the rank stage are the parent's bytes, so the layout digests, the rank
tables and the rank-seed identities are the parent's.

**Crate tests.** `cargo test --release --bins` on the derived binary:
**35 passed, 0 failed**
([`smoke/cargo-test-online-onlineframe2.txt`](smoke/cargo-test-online-onlineframe2.txt)).
They are:

- the row's 32 tests, including the round-2 `indexbuild2_tests` and the
  rank-probe frame tests;
- PR #988's two `onlineframe_tests`;
- the new `onlineframe2_tests`.

The comparisons against the parent run through `extract128`:

- `PIPE_FRAME` and `PIPE_FRAME_S3PLANT` must return the parent's
  `PIPE_COMPACT` online loop's relation, probe count, root calls and
  relation checks;
- on planted four-point targets;
- on the selected-keyed folded index (PR #988's test) and on the lift-keyed
  folded index of the arms (new; 7 and 12 columns, built by this producer's
  round-2 index build).

**Local runner smoke (correctness only).** The frozen design's segments O1
and P1 (32 processes) were run through `run_schedule.py` and `arm.py` with
the frozen binaries on the VM. `verify_receipt.py --correctness-only` passed
every gate ([`smoke/correctness_O1_P1.json`](smoke/correctness_O1_P1.json));
[`inputs/local_exactness.json`](inputs/local_exactness.json) is written by
[`summarize_exactness.py`](summarize_exactness.py).

| Check | Observed |
| --- | --- |
| rows | 32 of 32 valid (O1 7, P1 25) |
| Q0, K600 (cPIC, cPOF) | B's archived identity, 1,987,852 probes, same root calls (994,008) and relation checks |
| Q0, M10 (cM10IC, cM10OF) | the frozen identity, 2,130,165 probes |
| Q0, M38 (cM38IC, cM38OF, cM38OFX) | the frozen identity, 1,612,533 probes, 806,428 root calls |
| point s000, M38: 24 IC processes over both binaries and all three solves | **one** identity: relation, x codes, intermediates, probes (1,274,704), root calls (637,440), relation checks, scalar |
| layout digests (K600, M38, M10) | equal to the frozen ones on both binaries |
| rank stage, 9 processes on 4 seeds | identical relation digests, probe vectors, root calls and counters across kM38IC, kM38OF and kM38OFaa; tables equal the verified table |
| planted `frame_s3plant` | 8,698 states and 1,443,868 candidates compared with the S3 loop, no difference |
| hit orientation | Q0 in S3 order (0 swapped); s000 swapped (every candidate pair reversed, then resolved at the hit) |
| online counters | row binary: none; `s3` (cM38OS): all 0; `frame`: one frame, one resolved hit, 0 fallback states |

Both orientations of the hit resolution are exercised. Before timing, the
runner re-checks B's table and both closure bases and rejects the planted
corruptions ([`smoke/log-table-check.json`](smoke/log-table-check.json):
PASS).

## 3. Frozen design (Tier 1, repeated alternating pairs)

![Design (from the frozen protocol and schedule; not a result). Source
[figures/design.tex](figures/design.tex), vector
[figures/design.pdf](figures/design.pdf).](figures/design.png)

The design is the parent's, itself the Tier 1 template's:

- one GitHub `ubuntu-24.04` runner;
- a fresh process for every run, pinned to one CPU with a clean
  environment;
- `run_schedule.py` (verbatim), which records the CPU, placement,
  scheduling counters, cgroup, steal and fault counters, and applies the
  time guard;
- the two-stage paired bootstrap;
- the A/A band;
- the hardened fail-closed verifier.

**Sides and pairs.**

| side | processes, in order | binary |
| --- | --- | --- |
| **A** | kM38IC (rank stage, 16 attempts, the pair's seed, then the point), then cM38IC (verified table, the point) | the row, `ic_online_indexbuild2_r770` (the parent's arms, verbatim) |
| **B** | kM38OF (same seed), then cM38OF; `KIC_ONLINE_SOLVE=frame` | `ic_online_onlineframe2_r770` |
| **Baa** | kM38OFaa, then cM38OFaa | A/A copy of B |

- **Primary pairs: 16 points x 4 pairs = 64.** Each point's eight sides
  strictly alternate, ABAB... or BABA..., from a seeded start. The rank seed
  of pair *j* at point *i* is 2300 + 4*i* + *j* (2301-2364, new).
- **A/A:** 1 pair per point (B against Baa), with the seed of primary pair 1.
- **Planted:** 1 cold pair per point, cM38OF against cM38OFX
  (`frame_s3plant`).
- **Layout (new, descriptive):** 1 cold pair per point, cM38OS against
  cM38OF. cM38OS is the online-frame *binary* with `s3`, so this pair gives
  the online ratio within one binary. The parent's run saw small offsets
  between its two binaries on stages whose code was unchanged (rank 1.0046,
  online 1.0082). This pair separates the algorithm from any such
  binary-layout offset.
- **rho:** one rT per point, with seed 1060000 + point seed.
- **O1:** Q0 on cPIC, cPOF, cM10IC, cM10OF, cM38IC, cM38OF and cM38OFX.
  This checks exactness only.
- In total, **407 processes**. The sub-block order and the starts come from
  `random.Random(2026102170 + i)`.

**Primary (pre-registered): end to end over the current row.**

- E2E(side) = `timing_ms.rank_stage` (rank process) + `cold_in_process_ms`
  (cold process).
- R = sum E2E(A) / sum E2E(B) over the 64 pairs.
- 95% two-stage paired bootstrap: points, then pairs within points, with A
  and B of a pair kept together; 10,000 draws, `random.Random(20261060)`.
- **Improvement iff the lower bound > 1**: a qualified Tier 1 pipeline
  speedup over the row. Regression iff the upper bound < 1. Otherwise not
  separated; the online stage ratio is then reported only as a labelled
  stage result.
- **Invalid** if any gate is false or unknown, if any control fails, or if
  any row is missing (including time-guard skips).

**Why end to end, not the stage, is the primary.** Online is about 2.9% of
E2E, so the expected end-to-end effect is small (about 1.009). The power
check below shows that 64 pairs resolve it, so the primary stays end to end,
as asked.

**Stage secondary (labelled):** the online ratio cM38IC / cM38OF in the
primary pairs (same bootstrap), with the same-binary layout ratio
cM38OS / cM38OF beside it.

**Other secondaries (descriptive):**

- the geometric mean of the pair ratios;
- cold, setup, index build, self-test and rank stage (each expected
  about 1);
- online in the rank processes, and online ns per probe per arm;
- CPU time, wall, peak RSS and faults;
- per point, by pair position and by side order;
- the online counters and the probe law;
- S, and the E2E and online gaps to rT.

**Controls.**

- **A/A:** E2E(B)/E2E(Baa) and cold cM38OF/cM38OFaa, each inside
  [0.97, 1.03] over 16 pairs.
- **Planted timing:** online cM38OFX/cM38OF, with a 95% lower bound > 1
  over 16 pairs. PR #988 measured 2.71.
- **Planted exactness:**
  - `frame_s3plant`'s in-process comparison in every cM38OFX process,
    including Q0;
  - the closure corruptions rejected before timing;
  - the crate tests.

**Gates** (fail closed; an unknown gate counts as a failure). The parent's
gates apply, plus the following:

- **per point and base, across every IC process of both binaries and all
  three online solves:**
  - one relation (point indices, x codes, pinned intermediates);
  - one probe count;
  - **one root-call count and one relation-check count**;
- per process, the arm's online solve and counters:
  - the row binary reports none;
  - `s3` all zero;
  - `frame` exactly one frame and no planted check;
  - `frame_s3plant` one frame and at least one compared state and
    candidate;
- one scalar per point (oracle replay);
- one index and layout digest set per base (K600, M38, M10), equal to the
  frozen one;
- Q0;
- the rank tables;
- per rank seed (64 seeds), identical relation digests, probe vectors, root
  calls and counters across kM38IC, kM38OF and kM38OFaa;
- the probe law of kM38IC (1,024 attempts) inside [0.80, 1.20];
- every row on its arm's binary (by name and digest);
- placement, CPU identity, schedule identity and order.

**Panel and seeds.** The panel is 16 new public points: role
`onlineframe2-cold-v1`, seeds 0..15 ([`make_targets.py`](make_targets.py)).
They are checked against every earlier role of the law, including the
parent's `indexbuild2-cold-v1`. A role-agnostic x/y scan
([`inputs/panel_disjointness.json`](inputs/panel_disjointness.json)) found
**0 hits** in all of these:

- origin/main;
- 861 origin branches (1,646,556 files);
- the six other scratch worktrees, including the three sibling leads'
  (`n83-rankfinder`, `n83-l3`, `n19-loop`).

The rank seeds 2301-2364 are new
([`inputs/seed_disjointness.json`](inputs/seed_disjointness.json): 86 refs
plus the worktrees). The scan's positive control finds the parent's
1501-1536.

## 4. Power and runtime

![Design-stage power, the prior's end-to-end composition, and runtime (not a
result), from `analysis/power.json` by [`make_figures.py`](make_figures.py)
([svg](figures/power.svg), [pdf](figures/power.pdf)).](figures/power.png)

**The prior** is the parent's archived run 39464544962
([`make_power_prior.py`](make_power_prior.py), with the `runs.jsonl` digest
`c0d09af5...` pinned). It contains:

- the row's 36 primary pairs (the kM38IC rank stage; the cM38IC cold time
  and online time);
- its 24 A/A ratios, used as per-process noise factors. This is
  conservative by about sqrt(2).

**The model.** Side B is side A minus (1 − f) x online. The modelled f is
the row's own rank-stage frame cost over its online S3 cost on that host:
147.96 / 219.46 ns per probe = 0.674, or 1.483x online. The rank stage also
carries per-attempt work, so this f is if anything too large. In the effect
cells, f is set to hit each effect. There are 400 simulations per cell, with
500 draws each.

| true end-to-end effect | P(lower bound > 1) | median interval hi/lo |
| --- | ---: | ---: |
| 1.0000 (no gain; type I) | 0.0075 | 1.0047 |
| 1.0025 | 0.49 | 1.0050 |
| **1.0050 (minimal effect of interest)** | **0.91** | 1.0058 |
| 1.0075 | 0.995 | 1.0073 |
| **modelled, about 1.0095** (online 1.48x) | **0.9975** | 1.0083 |
| PR #988's online ratio 1.573 applied here, about 1.0106 | 1.00 | 1.0092 |

An earlier sizing with 12 points x 3 pairs (the parent's design) gave 0.83
at 1.005 and about 0.95 at the modelled effect. The design was therefore
enlarged to 16 x 4 before freezing, and the A/A was cut to one pair per
point to stay inside the time budget.

At the parent run's means, the model predicts the following. These are
estimates for sizing the design, not claims:

- end to end about **1.0095** (−108 ms of 11,537 ms);
- cold about 1.015;
- online about 1.48.

The controls behave as follows in simulation:

- the A/A point estimates are inside the band in 100% of simulations;
- the planted lower bound exceeds 1 in 100%, modelled at 1.5x;
- the probe-law gate (1,024 attempts) passes in 100% at the archived law
  and rejects a law 1.5x worse in 100%.

**Runtime.** The parent run's process walls give:

- about 260 s per point segment;
- a **70 min** schedule;
- a **job of about 89 min**, with 17 min fixed before and 2 min after;
- **133 min** on a host 1.5x slower.

The time guard is **165 min** and the job limit is **180 min**, so one job
fits within the 3 h budget. Any time-guard skip makes the run invalid.

**Threats named before the run:**

1. **Binary layout.** The two sides run different binaries. An offset of
   the size seen in the parent run (about 0.5% on unchanged stages) would
   be a sizeable fraction of a 1% effect. The layout pair and the
   unchanged-stage ratios (setup, index build, self-test, rank stage) are
   reported so that a reader can see it. They do not change the verdict.
2. **Host class.** The effect is a per-probe saving whose size depends on
   the host. The prior's host was an Intel Xeon 8370C, and PR #988's an AMD
   EPYC 7763.
3. **Ratchet.** Three sibling leads (the rank-stage run finder, the L3
   orbit/M retune, the n = 19 native relation loop) run against the same
   row. If one of them replaces the row first, this result still measures
   an improvement over the row it ran against (this one), under the ratchet
   rule. It is not re-based.

## Run

A `workflow_dispatch` call (ref `claude/n83-onlineframe2`) was refused:

- `gh workflow run`: 404, because the workflow is not on the default branch;
- the GitHub integration: **403** ("Resource not accessible by
  integration").

The workflow therefore also has the owner-approved push trigger. It is
restricted to branch `claude/n83-onlineframe2` and to this experiment's
non-receipt paths, as in the parent's `n83-indexbuild2.yml`. The push that
added it starts the run at the frozen protocol (`50e50718...`) and schedule
(`6c84dfe5...`). The push of commit `3b66377d` started run
[39527549698](https://github.com/aburan28/cryptanalysis/actions/runs/39527549698)
(queued 2026-10-21 01:28 UTC).

## Result

Run [39527549698](https://github.com/aburan28/cryptanalysis/actions/runs/39527549698)
(workflow `n83-onlineframe2.yml`, push trigger, frozen commit `3b66377d`,
attempt 1, conclusion success) on one GitHub-hosted `ubuntu-24.04` runner
(`GitHub Actions 1000369729`, image 20261018.339.1, kernel 7.0.0-1017-azure,
**AMD EPYC 7763**, 2 vCPUs = 1 core x 2 threads, execution CPU 0). The run
queued for 43 min (created 01:28, started 02:11 UTC); the job ended 03:55 UTC
(104 min); the runner's schedule took 82.3 min against the 165-minute guard.
The receipt is archived in [`run_github_39527549698/`](run_github_39527549698/).

**All gates pass; the run is valid.** All 407 scheduled rows ran
(`schedule-exit.txt`: 0): 407 valid, 0 invalid, **0 skipped by the time
guard**, guard not tripped; all 64 primary pairs, 16 A/A pairs, 16 planted
pairs and 16 layout pairs complete; 17 units seen (16 points and Q0).

- Before timing: tables and both closure bases re-verified by the pinned
  oracle (`log-table-check.json`); the verifier's 33 unit tests and the crate
  tests ran in the job and passed (`verifier-tests.txt`,
  `cargo-test-*.txt`).
- One scalar per point across every IC process and rT, replayed in the oracle.
  One relation, one probe count, **one root-call count and one
  relation-check count** per point and base across both binaries and all
  three online solves (0 failures in each).
- One index and layout digest set per base (K600, M38, M10), equal to the
  frozen one; Q0 equal to the archived and frozen identities; rank tables
  equal to the frozen verified tables.
- Per rank seed (64 seeds, 2301-2364): identical relation digests, probe
  vectors, root calls and counters across kM38IC, kM38OF and kM38OFaa (0
  rank-seed failures, 0 rows without gain).
- Probe law of kM38IC: 1.0236 [0.9383, 1.1083] over 1,024 attempts (64
  blocks), inside the frozen band [0.80, 1.20] (pass). kM38OF reads the same
  mean, because the arms share rank seeds.
- Runner identity equals the frozen files (protocol `50e50718...`, schedule
  `6c84dfe5...`); binaries unchanged; CPU identity unchanged start to end;
  every process on CPU 0 (407/407); no contention flags; no problems.
- Online counters: the row binary reports none, `frame` arms exactly one
  frame and one resolved hit with 0 fallback states, and the Q0
  `frame_s3plant` process compared 4,858 states and 806,428 candidates with
  the S3 loop with no difference.

`verify_receipt.py` re-run on a **copy of the whole receipt directory**
(with the gitignored `snapshots/r770` oracle as restored in the worktree;
`restore.py --crypto-repo /home/user/crypto` was not needed) reproduces
`panel/result.json` and `panel/result_table.md` **byte for byte** (`cmp`)
and the same stdout.

![Frozen ratios with 95% bootstrap intervals, all from result.json. Vector
figures/result.pdf, SVG figures/result.svg; script
figures/make_result_figure.py.](figures/result.png)

### Primary and controls (frozen rule)

Improvement iff the 95% lower bound of R = sum E2E(A) / sum E2E(B) over the
64 alternating pairs exceeds 1 (two-stage paired bootstrap, 10,000 draws),
the A/A ratios lie in [0.97, 1.03], and the planted online lower bound
exceeds 1. A = kM38IC + cM38IC (the current n = 83 row), B = kM38OF +
cM38OF (the online-frame producer).

| Statistic | Estimate [95%] | Reading |
| --- | --- | --- |
| **R = E2E(A) / E2E(B)** (64 pairs, 16 points) | **1.0165 [1.0110, 1.0221]** | **improvement** (lower bound above 1) |
| geometric mean of the 64 pair ratios | 1.0162 [1.0110, 1.0221] | reported |
| A/A E2E B / Baa (16 pairs) | 1.0009 [0.9962, 1.0063] | pass (inside [0.97, 1.03]) |
| A/A cold cM38OF / cM38OFaa (16 pairs) | 1.0006 [0.9971, 1.0050] | pass (inside [0.97, 1.03]) |
| planted online cM38OFX / cM38OF (16 pairs) | 2.6404 [2.6137, 2.6625] | pass (lower bound above 1; PR #988 read 2.71) |
| planted exactness corruptions | rejected before timing | pass |

Mean E2E per side: A 13,105.5 ms (4,447.2 rank stage + 8,658.3 cold), B
12,893.2 ms (4,431.7 + 8,461.5), a saving of 212.3 ms per target. Of it,
179.4 ms (84.5%) is the online interval (503.2 -> 323.8 ms), 17.4 ms the
setup and 15.5 ms the rank stage. Setup and rank stage run the same source in
both arms (see the layout check). The ratio 1.0165 is above the minimal
effect of interest (1.005) and above the design's modelled 1.0095: the online
interval is 3.84% of A's E2E on this host (503.2 of 13,105.5 ms; the model's
2.9% came from the Xeon prior), at 250 ns per probe against the prior's 219.5.

### Secondaries (none changes the verdict)

**Online stage ratio (a stage result, not the primary).** Online A / B
(cM38IC / cM38OF in the 64 primary pairs) is **1.5541 [1.5324, 1.5766]**, from
250.13 to 160.17 ns per probe; in the rank processes' own online scan
1.5585 [1.5426, 1.5728]. PR #988 read 1.5733 on the older producer. This is a
stage improvement of the online scan only, and it moves the end-to-end cost by
the 1.65% above because the online interval is 3.8% of the end-to-end cost.

**Layout pair cM38OS / cM38OF (the binary-offset check, 16 pairs, descriptive).**
Both arms run the online-frame binary; only `KIC_ONLINE_SOLVE` differs (`s3`
against `frame`).

| Quantity | cross-binary A / B (64 pairs) | same binary cM38OS / cM38OF (16 pairs) |
| --- | --- | --- |
| online | 1.5541 [1.5324, 1.5766] | 1.5794 [1.5456, 1.6130] |
| cold | 1.0233 [1.0167, 1.0304] | 1.0217 [1.0124, 1.0306] |

The same-binary online ratio (1.5794) is not below the cross-binary one
(1.5541), and the two cold ratios differ by 0.16% (1.0233 against 1.0217,
intervals overlapping). The binary-layout offset therefore does not create the
online effect. The size of the offset on **unchanged** code is read from the
stages that run the same source in both arms:

| Unchanged stage | A / B [95%] |
| --- | --- |
| rank stage (ms) | 1.0035 [0.9964, 1.0115] |
| setup (ms) | 1.0021 [0.9999, 1.0044] |
| index build (ms) | 1.0030 [1.0007, 1.0055] |
| scan self-test (ms) | 0.9984 [0.9937, 1.0029] |
| index build in the rank process (ms) | 1.0043 [1.0016, 1.0075] |

These are 0.2-0.4%, in total 32.9 ms of the 212.3 ms saving (15.5 ms rank
stage, 17.4 ms setup). **The E2E effect (1.65%, 212.3 ms) is larger than the
layout offset on unchanged stages (about 0.25% of E2E, 32.9 ms).** If the
unchanged stages were set to equal times, R would be 1.0139 (a descriptive
figure with no interval, not the frozen rule): the lower bound of the frozen
rule does not rest on the offset, but about 15% of the point estimate may.
The parent run saw 1.0046 on the rank stage and 1.0082 on online with
unchanged code; those offsets are of the same order as the ones here.

**Stage table** (means over the 64 primary pairs; A over B, above 1 = B
faster):

| Phase | A (kM38IC + cM38IC) | B (kM38OF + cM38OF) | A / B [95%] |
| --- | ---: | ---: | :--- |
| end to end (ms) | 13,105.5 | 12,893.2 | **1.0165 [1.0110, 1.0221]** |
| rank stage (ms) | 4,447.2 | 4,431.7 | 1.0035 [0.9964, 1.0115] |
| cold = setup + online (ms) | 8,658.3 | 8,461.5 | 1.0233 [1.0167, 1.0304] |
| setup (ms) | 8,155.2 | 8,137.8 | 1.0021 [0.9999, 1.0044] |
| index build (ms) | 6,438.7 | 6,419.3 | 1.0030 [1.0007, 1.0055] |
| scan self-test (ms) | 1,336.6 | 1,338.8 | 0.9984 [0.9937, 1.0029] |
| online (ms) | 503.15 | 323.75 | **1.5541 [1.5324, 1.5766]** (stage result) |
| process CPU time (ms) | 26,005.5 | 25,621.7 | 1.0150 [1.0099, 1.0204] |
| process wall (ms) | 26,011.6 | 25,628.0 | 1.0150 [1.0097, 1.0204] |
| cold minor faults | 730,115 | 730,120 | 1.0000 [1.0000, 1.0000] |
| peak RSS (bytes) | 1,895,574,464 | 1,895,633,088 | 1.0000 [1.0000, 1.0000] |

The rank-stage per-probe cost is 159.72 ns (kM38IC), 159.28 ns (kM38OF) and
159.46 ns (kM38OFaa): the rank stage runs the frame loop in all three arms.
Rank-stage share of E2E: A 33.9%, B 34.4%.

**S** (cost over this run's measured rT770 step, 284.787 ns, per sqrt(r);
one unit is 26,363.6 ms):

| Quantity | S(A) | S(B) | delta S |
| --- | ---: | ---: | ---: |
| end-to-end cold | 0.49711 | 0.48905 | -0.00805 |
| rank stage | 0.16869 | 0.16810 | -0.00059 |
| setup without the rank stage | 0.30933 | 0.30867 | -0.00066 |
| setup with the rank stage | 0.47802 | 0.47677 | -0.00125 |
| cold without the rank stage | 0.32842 | 0.32095 | -0.00747 |
| online | 0.019085 | 0.012280 | -0.006805 |

The tuned rho's own S: cold 0.09154 (mean rT770 cold 2,413.4 ms), online
0.08240 (2,172.4 ms).

**Gap to tuned rho rT770** (IC time over rT time, point estimates from
`result.json`; no interval is computed for the gaps; distance remaining, not
a gate):

| Arm | End-to-end cold | Online |
| --- | ---: | ---: |
| A = kM38IC + cM38IC (current row) | 5.4304 | 0.2316 (503.15 / 2,172.39 ms) |
| B = kM38OF + cM38OF (candidate) | 5.3424 | 0.1490 (323.75 / 2,172.39 ms) |

B is 5.34 times the tuned rho end to end, and no arm beats it. **Cross-run
rho-gap artifact:** the row this run would replace read 4.4164 over its own
run's rT770 (275.04 ns step, Intel Xeon Platinum 8370C). Here the same
producer reads 5.4304 over this run's rT770 (284.79 ns step, AMD EPYC 7763),
and the new producer's 5.3424 is numerically larger than the landed 4.4164
although it is paired-faster (5.4304 to 5.3424). The runs differ in host
class, rank seeds and rT770 step (rho cold 2,413.4 ms here, 2,612.4 ms there;
the IC's A side 13,105.5 ms here, 12,886.3 ms there), so only the paired
within-run gap is a delta; the absolute gaps and S are not comparable across
runs.

**Per-pair ratio spread** (64 pairs): minimum 0.9917, median 1.0145, mean
1.0163, maximum 1.0590, standard deviation 0.0139, quartile positions (16th
and 48th of 64 sorted) 1.0052 and 1.0244. Per point (16 points): 1.0019 to
1.0394, all above 1. By pair position within the point: 1.0162, 1.0213,
1.0150, 1.0137 (first to fourth). By order: A first 1.0173, B first 1.0154,
an order effect of 0.19% (the start was drawn per point), inside the
interval's distance from 1 (lower bound 1.0110).

**Probe law** (mean probes per relation over the law value, 1,024 attempts):
kM38IC 1.0236 [0.9383, 1.1083] (gate, band [0.80, 1.20]: pass), kM38OF
1.0236 [0.9340, 1.1156] (same mean, shared rank seeds).

### Host and isolation records

From `host-cpu.json`, `allocation.json`, `panel/runner_start.json`,
`panel/runner_end.json` and the 407 per-row records in `panel/runs.jsonl`:

| Record | Observed |
| --- | --- |
| provider, instance | GitHub Actions, run 39527549698 attempt 1, instance id `gh-39527549698-1-onlineframe2`, runner `GitHub Actions 1000369729`, advertised 4 vCPU / 16 GB (observed 2 vCPUs, 8.1 GB), image 20261018.339.1; allocation receipt `allocation.json` |
| CPU | AMD EPYC 7763 (family 25, model 1, stepping 1), no AVX-512 flags, 2 vCPUs = 1 core x 2 threads, 1 socket, 1 NUMA node; Microsoft hypervisor; L1d 32 KiB and L2 512 KiB shared by vCPUs 0-1, L3 32 MiB |
| microcode | `0xffffffff` (not readable inside the guest), uniform across CPUs, same at start and end; `lscpu` lists spec-rstack-overflow and TSA as "Vulnerable: no microcode" |
| frequency | not recorded: `frequency_khz` is empty in every row; nominal `cpu_mhz` 3246.4 at start |
| placement | every process on CPU 0 (`Cpus_allowed_list` 0), 407/407 |
| cgroup | `/system.slice/hosted-compute-agent.service`, no CPU quota |
| steal | 0 ticks in every row (`/proc/stat`), total 0 |
| throttling | `nr_throttled` 0 in every row |
| memory failures | `memory.events` max and oom_kill deltas 0; 0 major faults |
| scheduling | 57,284 involuntary and 3,990 voluntary context switches over 407 processes (at most 405 involuntary in one process) |
| CPU pressure | `cpu.pressure` some-delta per row 553 to 89,848 us |
| contention flags | none |
| transparent hugepages | `enabled` madvise, `defrag` madvise |

### AGENTS.md Tier 1 assessment

AGENTS.md Tier 1 (cloud instance) requires: a frozen provider allocation
receipt and instance ID; both variants on the same pinned exposed CPU with the
same workload and limits; code and workload hashes, paired order, raw
failures, correctness, process CPU time, memory, cgroup throttling and memory
failures, steal time and scheduling counters; repeated alternating pairs and a
95% paired interval whose lower bound exceeds 1.

**Met:** the allocation record and instance ID; one pinned CPU for all 407
processes with the same workload, binaries and no CPU quota; code and workload
hashes (protocol, schedule, arm wrapper, runner, binaries, log tables,
`frozen.sha256`); paired alternating order from the frozen schedule; raw
failures (0) and correctness (every gate above); process CPU time, peak RSS,
cgroup throttling (0), memory events (0), steal (0) and scheduler counters per
row; 64 alternating pairs and a lower bound of 1.0110.

**Gaps (named; none changes the verdict, all limit the claim):**

1. No host-wide exclusivity. CPU affinity records placement inside the VM; the
   cgroup is the runner agent's service, and the other vCPU, the agent and the
   hypervisor's other tenants are not controlled. Steal of 0 in the guest does
   not prove an unshared physical core.
2. The SMT sibling is not excluded. CPU 0 shares its core and its L1/L2 with
   vCPU 1 (cache `shared_cpu_list` 0-1), which is the only other vCPU and
   carries the runner agent; it was not offlined or shown idle.
3. Microcode is unreadable (`0xffffffff`), so the CPU identity rests on the
   model name, flags and the unchanged record, not on a microcode revision.
4. The frequency is neither fixed, controlled nor observed: no per-row reading
   exists (the parent's run at least recorded one). The pairs are adjacent in
   time and alternate, which balances a slow drift but not a fast one.
5. No IRQ routing control, no `isolcpus` / `nohz_full`, no NUMA memory policy
   beyond the single node.
6. One instance only (instance scope). This host class (AMD EPYC 7763, no
   AVX-512, 2 vCPUs) differs from the row's run (Intel Xeon Platinum 8370C),
   so absolute times, the rT770 step and the gaps are not comparable across
   runs, only the paired ratios. The effect is a per-probe saving whose size
   depends on the host (online share 3.84% of E2E here, 2.9% in the prior) and
   has not been replayed on another host class.
7. Binary layout. A and B are different binaries; the unchanged stages differ
   by 0.2-0.4% (see the layout check), the same order as the effect's
   uncertainty, so a small part of the 1.65% may be layout. The same-binary
   layout pair is descriptive, 16 pairs.

The result is a **Tier 1, instance-scoped** paired wall-time comparison, not
host-isolated (Tier 2).

### Limits of this result

- Tier 1, instance scope: one runner, 16 cold points, 4 alternating pairs per
  point, one fresh process per arm per pair. The interval covers points and
  pairs; it does not cover another host class.
- Wall time on one host class. The saving is the online scan (179.4 of
  212.3 ms); the self-test, setup, index build and rank stage are the parent's
  code. The effect is small: 1.0165, 1.65% of the end-to-end cost, with an
  online interval that is 3.8% of A's E2E.
- **Factor-base construction is charged to no arm** (the n = 83 convention),
  so 1.0165 is an upper bound on the every-phase ratio and the cold S a lower
  bound. At the construction time measured on another host class (X = 427.5
  ms, run 39007026856, illustrative, mixes hosts) the every-phase figures are R
  1.0159 and cold S(B) 0.50527.
- The gap to rT770 is a point estimate from one run with no interval, and
  differs across runs (cross-run artifact above).
- The section 5a band is not computable (the IC arms emit no group-operation
  counts). Not replayed on another host class.

## Files

| File | Role |
| --- | --- |
| `protocol.json`, `make_protocol.py`, `schedule.json`, `make_schedule.py` | frozen protocol, its builder, frozen run order (with the layout sub-block) |
| `make_onlineframe2_source.py`, `make_onlineframe_source.py` | side B's derivation; PR #988's derivation, verbatim (seven edits imported) |
| `make_indexbuild2_source.py`, `make_indexbuild_source.py`, `make_online_source.py`, `make_indexlift_source.py`, `make_closure_source.py`, `make_rankprobe_source.py`, `make_rankcut_source.py`, `make_stacked_source.py`, `make_tablefilter_source.py`, `make_probepipe_source.py`, `make_combined_source.py`, `online/`, `lift2/` | the row's verbatim derivation chain; the online crate (both IC binaries and the tuned rho); the two-limb canonicalizer crate |
| `restore.py`, `check_log_table.py`, `make_closure_base.py`, `verify_closure.py` | restore and digest-check crypto 770f6a69, every parent pin and local source; table and closure checks |
| `arm.py`, `run_schedule.py` | one arm per pinned process (with `KIC_ONLINE_SOLVE` and its gates); the schedule runner (template, verbatim) |
| `verify_receipt.py`, `test_verify_receipt.py` | fail-closed gates, statistics, decision rule (33 unit tests) |
| `make_targets.py`, `check_panel_disjoint.py`, `check_seed_disjoint.py`, `inputs/` | the new panel, disjointness records, local exactness record |
| `make_power_prior.py`, `power_check.py`, `analysis/power.json` | power prior (run 39464544962), simulation, result |
| `summarize_exactness.py`, `smoke/` | local correctness smoke (O1, P1), crate test log, table check |
| `make_figures.py`, `figures/` | design diagram (TikZ), power figure; `figures/make_result_figure.py`, `figures/result.*`: result figure (TikZ source, PDF, SVG, PNG) drawn from `result.json` |
| `run_github_39527549698/` | the archived receipt: `panel/result.json`, `panel/result_table.md`, `verify-stdout.json`, host and allocation records, 407 per-row records |
| `README.pdf` | this report: `pandoc README.md -o README.pdf --pdf-engine=pdflatex -H report_header.tex --lua-filter report_filter.lua -V geometry:margin=2cm -V fontsize=10pt -V colorlinks=true` |
