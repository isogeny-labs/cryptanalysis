---
title: "n = 83: a faster root-index build for the closure + index-lift row (Tier 1 design)"
date: 2026-10-20
---

# n = 83: a faster root-index build for the closure + index-lift row (Tier 1 design)

**Status (2026-10-20): result in. Verdict: improvement; every gate passes and
the run is valid.** R = E2E(A) / E2E(B) = **1.7406 [1.7129, 1.7676]** over 36
alternating pairs (12 points x 3 pairs), run 39383739494, Tier 1, instance
scope. The design sections below are the frozen text, unchanged; the profile
and the candidate savings in them come from the shared cloud-agent VM and are
local diagnostics, used only to rank the candidates and size the design. The
[Result](#result) section was added with the archived receipt.

## Why this run

The n = 83 a = 1 baseline row (`docs/ic/BASELINES.md`, `baselines.json`)
is the closure + index-lift M38I producer:

- the experiment is
  [`koblitz-n83-closure-indexlift-20261019`](../koblitz-n83-closure-indexlift-20261019/README.md)
  (PR #997);
- the derived producer's SHA-256 is `1d328b2e...`;
- its Tier 1 qualification is
  [`koblitz-n83-closure-indexlift-rep-20261020`](../koblitz-n83-closure-indexlift-rep-20261020/README.md)
  (PR #1002, run 39359922687), which measured R = 7.4133 [7.1999, 7.6362]
  over 30 alternating pairs.

In that run the row spends its 21.74 s end-to-end cold time as follows:

| Stage | Time (s) | Share |
| --- | ---: | ---: |
| root-index build | 15.63 | 72% |
| full scan-order self-test | 1.70 | |
| rank stage | 3.74 | 17% |
| online | 0.35 | |

The index build is now the dominant cost.

This experiment profiles that build, ranks the candidate speedups, and
implements the mechanical ones. Each implemented change leaves the output
byte for byte the same: the same stored states, table slots, relations,
probes and self-test verdict. A Tier 1 protocol with repeated alternating
pairs then measures the new producer against the row.

## 1. Profile of the index build (local diagnostic)

![LOCAL DIAGNOSTIC: component medians of three profile processes on the M38
closure header, and the candidates ranked by modelled saving. Rendered from
`inputs/local_profile.json` by `make_figures.py`
([svg](figures/profile.svg), [pdf](figures/profile.pdf)).](figures/profile.png)

**Method.** [`profile/profile_patch.py`](profile/profile_patch.py) patches a
*scratch copy* of the row's producer. That copy is never committed as a
producer. It adds `KIC_INDEX_PROFILE` instrumentation (`Instant` timers and
`getrusage` fault counters), which does the following:

- builds the parent's index in place;
- times each component alone (S3 prepare, field inversion, finish,
  `to_normal`, push, `lift_scan`, insert);
- times each candidate variant;
- asserts that every variant reproduces the parent's states and slot words.

`perf` is not installed on the VM (`perf_event_paranoid` 2), so the profile
uses these counters instead.

There were three processes on the M38 header (608 orbits, 15,341,360 stored
states, 30,682,720 roots, 30,366,551 entries, 2^26 slots of 16 B = 1 GiB),
each pinned with `taskset -c 2`, built with rustc 1.97 (the workflow pins
1.99). [`profile/summarize.py`](profile/summarize.py) writes
[`inputs/local_profile.json`](inputs/local_profile.json).

| Component of the row's index build (M38) | Median (ms) | What it is |
| --- | ---: | --- |
| **state loop** | **9,389** | 15.3 M `S3Solver128::roots` calls and pushes |
| &nbsp;&nbsp;field inversion | 6,464 | one Itoh-Tsujii inversion per state (about 420 ns each) |
| &nbsp;&nbsp;S3 prepare | 780 | squares and products before the inversion |
| &nbsp;&nbsp;S3 finish | 1,579 | half-trace, products, trace test |
| &nbsp;&nbsp;`to_normal` of both roots | 437 | 2 x 11 byte-table lookups |
| &nbsp;&nbsp;push and first touch | 434 | 736 MB of states, 179,782 minor faults (`Vec` grows by doubling) |
| **table insert loop** | **7,223** | 30.7 M `index_canonical128` + `insert_if_absent` |
| &nbsp;&nbsp;`lift_scan` canonicalization | 1,961 | about 64 ns per root |
| &nbsp;&nbsp;insert: cache and TLB misses, first touch | 5,263 | random slots in a 1 GiB table; 524,288 minor faults (2 per 4 KiB page: a read maps the zero page, then the write copies it) |
| table allocation | 0.02 | `calloc`, lazily zeroed |
| **index build total** | **16,921** | `timing_ms.index_build` |
| scan self-test, 2 keys (outside `index_build`, inside setup) | 2,125 | 2 x 2^26 Feistel evaluations plus a 3.8 MB bitmap |
| inverse self-test, 2 keys | 2 | 65,536 samples each |

There is no I/O in the build: the base header is read before it, in
`base_load`, about 0.37 s.

The index digests are computed after the target, outside every timed
interval. Index memory layout: `State128` is 48 B (two `u128` roots plus
three `u16`), and the compact table has one `u128` word per slot.

## 2. Candidates, ranked by modelled saving

Every saving below is the local median per M38 cold process. Unless noted,
the output is byte-identical.

| # | Candidate | Modelled saving | Output | Status |
| --- | --- | ---: | --- | --- |
| C1 | One field inversion per `(left, right)` row of states (`RootBatch128`, Montgomery's trick), with the states vector allocated once | **5.5 s** (9.39 to 3.93) | identical: the inverse is unique | **implemented** |
| C2 | Canonicalize root i+32 ahead and prefetch its home slot while inserting root i | **3.0 s** (insert 5.26 to 2.20) | identical: same inserts, same order | **implemented** |
| S1 | The same exhaustive self-test, computing 8 Feistel images before their 8 checks | **0.7 s** (2.06 to 1.40) | identical verdict, same domain | **implemented** |
| C1' | Batches of 4 or 16 rows instead of 1 | 0.0 to 0.3 s more | identical | not taken (within noise) |
| C6 | Bucketed or radix-ordered insert (sort the inserts by home slot) | at most about 1 s (the remaining insert minus faults) | linear probing with first-wins is order-dependent; clusters that cross a bucket boundary need an extra proof | not implemented |
| C7 | A cheaper canonicalizer than `lift_scan` | at most about 1 s (1.96 s total) | needs a new exhaustive equivalence proof | not implemented |
| C3 | `MADV_HUGEPAGE` on the table | 1.0 s in the insert-only microbenchmark, but **1.9 s slower** in the full build (2 MiB zeroing and compaction under `defrag=madvise`) | identical | rejected (host-dependent, slower) |
| C4 | Prefault the table by sequential writes | -0.2 s (the 0.46 s prefault equals the double faults it saves) | identical | rejected |
| **S2** | **Evidence-changing:** run the full self-test once per binary and base before timing, and only a sampled check per process | 1.4 s more (all of S1's remaining cost) | **changes what each process proves** | **listed separately, not used** |

Implemented together (C1 + C2 + S1), these cut the local index build from
16.4 s to 8.2 s and the self-test from 2.06 s to 1.40 s. The local cold
process went from 19.1 s to 10.2 s, both on point s000 of the template panel
(`profile/raw/cold_*_s000.stdout.txt`).

Applied to the template run's means, the model predicts the following. These
are estimates for sizing the design, not results:

- index build about **2.0x**;
- cold about **1.87x**;
- **end to end about 1.63x** (21.74 s to about 13.36 s).

**What the self-test protects, and why S2 is not used.** The self-test checks
that the Feistel scan order (`ScanPermutation`) visits every logical state
index exactly once, for the process's own state count and two fixed keys.
Its verdict is a deterministic function of the code and of `len`, so
repeating it per process adds no new information about the data. What it
does give is per-process, in-receipt evidence that the code that ran had a
bijective scan order on the state count it scanned. The crate tests cover
small lengths and the K600 count, and the sampled inverse check covers random
points.

S2 would move the exhaustive check to one pre-timing process per binary and
base, and leave the timed processes with the sampled check. Both checks
target the same predicate. But S2 changes the evidence: a timed receipt would
no longer show the exhaustive check for itself, and the template's arms,
gates and planted control all assume `scan_selftest=full`. So S2 is listed
here and not used. S1 keeps the exhaustive check in every process.

## 3. What is implemented: a counted derivation

[`make_indexbuild_source.py`](make_indexbuild_source.py) follows the same
pattern as the parents' `make_*_source.py` files:

1. It re-derives the row's producer with the parent's
   `make_online_source.py` (verbatim), which checks rank-probe `d4394df3...`,
   index-lift `7df72603...`, closure `8916e034...` and the composition.
2. It requires that output to be `1d328b2e...`.
3. It applies **7 counted replacements**, each of which must occur exactly
   once:
   - the header comment;
   - one constant;
   - the state loop (C1);
   - the compact insert loop (C2);
   - the self-test (S1);
   - one summary field (`index_build_pipeline`);
   - one appended test module.
4. `check_inverse()` undoes the replacements on every derivation and must get
   the parent's bytes back.

The derived source is `bc6a31c7...`
(`koblitz_orbit_dlp_fast_online_indexbuild.rs`), and the binary is
`ic_online_indexbuild_r770`. Both IC binaries are built by one `cargo build`
from the parent's lock file. `online/Cargo.toml` has one added `[[bin]]`.

[`restore.py`](restore.py) checks the following on every build, and the
workflow runs it before building:

- the parent protocol `ff5b4cbf...`;
- side A's producer equals the parent's frozen `1d328b2e...`;
- both closure headers;
- the 23 files copied from the parent (`VERBATIM`);
- the 2 files copied from the template (`TEMPLATE`: `run_schedule.py` and
  `check_panel_disjoint.py`, the same bytes as on main after #1002);
- every local pin in `protocol.json`.

`arm.py` is the parent's with two marked gates added:

- `index_build_pipeline` must equal the arm's value (none on side A);
- the planted `lift_plant` arm must check exactly 2 x stored states roots,
  and every other arm 0.

**Exactness argument** (also in `protocol.json`, `exactness_argument.indexbuild`):

1. *State loop.* `roots` computes prepare, one inversion of the denominator
   `a*ps` (a zero denominator takes the scalar fallback) and finish.
   `RootBatch128::solve` runs the same prepare. It then inverts the product
   of the row's non-zero denominators once and recovers each inverse as
   (prefix product) x (inverse of the running product). That is the
   denominator's field inverse, because inverses in GF(2^83) are unique.
   Finish then returns the same roots in the same order. The states are
   pushed in the parent's order.
2. *Insert loop.* `index_canonical128` is a pure function of the root (plus
   the planted counter, which is called once per root, in order). Computing
   it 32 roots early changes no key or shift. The prefetch is a hint without
   architectural effect. `insert_if_absent` receives the same `(key, value)`
   sequence, so every slot word is the parent's.
3. *Self-test.* The parent returns false iff some image of `[0, domain)` is
   at least `domain` or an in-range image repeats, and otherwise returns
   `visited == len`. The lanes loop evaluates the same `apply` on the same
   indices and the same checks in index order, so it returns the same
   boolean.

## 4. Exactness checks before freezing (cloud-agent VM, correctness only)

- **Crate tests** (`indexbuild_tests`, 4 tests, in the online crate's
  `cargo test --bins`, which the workflow runs before timing). The parent's
  state loop, insert loop and self-test are kept there verbatim as
  references. The tests check:
  - widths 1, 2, 9 and 17;
  - every index canonicalizer (selected, lift, lift_plant), folded and
    planted fold modes, compact and base tables;
  - that the states, slot words, entries and planted-check counts equal the
    parent's;
  - that the self-test verdict equals the parent's for every length 1..1500
    with 5 keys, for planted non-bijections (a collision, an out-of-domain
    image, a dropped image, shorter vectors), and for the frozen M38/M10
    (30,682,112) and K600 (29,880,000) counts with both keys.

  All 25 tests of the derived binary pass, including the parent's 21.
- **Per-base output equality**
  ([`inputs/local_exactness.json`](inputs/local_exactness.json), from
  `profile/raw/exactness/` by `profile/summarize_exactness.py`). Run through
  the wrapper with the full gate set, the derived producer:
  - reproduced the frozen **layout digests** (`stored_states_blake3`,
    `table_slots_blake3`), logical-state digests and table-map digests on
    **K600** (`d8cfe443...`/`5f53764e...`), **M38**
    (`f7a8d6b8...`/`6c08c6c2...`) and **M10** (`c90b501b...`/`4973cfe5...`);
  - reproduced the **Q0 identities** on all three bases (1,987,852,
    1,612,533 and 2,130,165 probes, the frozen relations, scalar
    3141592653589793);
  - wrote rank tables equal to the frozen verified tables on M38 (seed 1201)
    and M10 (seed 301);
  - on M38 seed 1201, gave the **same rank relation digest, per-attempt
    probe vector, root calls, frame and point-addition counters** as the
    row's producer.
- **Smoke of the frozen schedule** (O1 and P1, after freezing; see
  [`smoke/README.md`](smoke/README.md)).

## 5. Frozen design (Tier 1, repeated alternating pairs)

![Design (from the frozen protocol and schedule; not a result). Source
[figures/design.tex](figures/design.tex), vector
[figures/design.pdf](figures/design.pdf).](figures/design.png)

The design follows the Tier 1 template
(`koblitz-n83-closure-indexlift-rep-20261020`): one GitHub `ubuntu-24.04`
runner, and a fresh process for every run, pinned to one CPU with a clean
environment. It keeps the template's:

- `run_schedule.py` (verbatim): CPU record, placement, scheduling counters,
  cgroup, steal and fault counters, time guard;
- two-stage paired bootstrap;
- A/A band;
- fail-closed verifier, extended with two gates.

**Sides and pairs.**

| side | processes, in order | binary |
| --- | --- | --- |
| **A** | kM38I (rank stage, 16 attempts on M38, pair's seed, then the point), then cM38I (verified table, the point) | the row, `ic_online_closure_indexlift_r770` |
| **B** | kM38IB (same seed), then cM38IB | derived, `ic_online_indexbuild_r770` |
| **Baa** | kM38IBaa, then cM38IBaa | A/A copy of B |

- **Primary:** 12 points x **3 pairs = 36 primary pairs**. Each point's six
  sides strictly alternate, ABABAB or BABABA; 7 points start with A and 5
  with B. Seed of pair *j* at point *i*: 1400 + 3*i* + *j*.
- **A/A:** 2 pairs per point (B against Baa), with the seeds of primary
  pairs 1 and 2.
- **Planted:** 1 cold pair per point, cM38IB against cM38IBX. In cM38IBX,
  `KIC_INDEX_CANON=lift_plant` also runs the selected canonicalizer on every
  root and asserts that it equals `lift_scan`. That is slower (locally
  1.8-2.2x on the index build), and the layout is the same.
- **rho:** one rT per point, seed 1030000 + point seed.
- **O1:** Q0 on cPI, cPIB, cM10I, cM10IB, cM38I and cM38IB, so both binaries
  run on all three bases. This is exactness only.
- In total, **282 processes**. Sub-block order and starts come from
  `random.Random(2026102050 + i)`.

**Rank stage: the same seed per pair, not a shared rank stage.** Each side
runs its own rank process on its own binary. The change touches only how the
index is computed, so the rank stage's work is identical. This is gated per
seed across kM38I, kM38IB and kM38IBaa: identical relation digests, probe
vectors, root calls and counters. Timing the rank stage on both sides keeps
any code-layout effect of the new binary on the rank loop inside E2E, rather
than assuming it is zero. A shared-rank design would have to assume that.
This costs about 15 s of process time per pair.

**Primary (pre-registered).**

- E2E(side) = `timing_ms.rank_stage` (rank process) + `cold_in_process_ms`
  (cold process).
- R = sum E2E(A) / sum E2E(B) over the 36 pairs.
- 95% two-stage paired bootstrap: points, then pairs within points, with A
  and B of a pair kept together; 10,000 draws, `random.Random(20261030)`.
- **Improvement iff the lower bound > 1.** Regression iff the upper bound
  < 1. Otherwise not separated.
- **Invalid** if any gate is false or unknown, if any control fails, or if
  any row is missing (including time-guard skips).

**Stage secondary (labelled):** the index-build ratio, cM38I / cM38IB
`timing_ms.index_build`, with the same bootstrap. The run also reports the
index build in the rank processes.

**Other secondaries (descriptive):**

- geometric mean of the pair ratios;
- cold, setup, scan self-test, online, rank stage (expected about 1), CPU
  time, wall time, peak RSS and cold minor faults;
- per point, by pair position and by side order;
- probe law of kM38I and kM38IB;
- S and the gap to rT.

**Controls.**

- **A/A:** E2E(B)/E2E(Baa) and cold cM38IB/cM38IBaa, each inside
  [0.97, 1.03] over 24 pairs.
- **Planted timing:** index build cM38IBX/cM38IB, lower 95% bound > 1 over
  12 pairs.
- **Planted exactness:**
  - the three closure corruptions rejected before timing
    (`check_log_table.py`);
  - the planted non-bijections rejected in the crate tests;
  - every cM38IBX checks 2 x 15,341,360 roots and keeps the frozen layout.

**Gates.** All gates are fail closed; an unknown gate counts as a failure.
They are the template's gates plus the following:

- every row ran **its arm's binary**, by name and by the digest that
  `runner_start.json` lists;
- one index and layout digest set per base on **K600, M38 and M10**, across
  both binaries, equal to the frozen one;
- Q0 identities on all six O1 arms;
- the probe-law band for kM38I over 36 seeds (576 attempts).

**Panel and seeds.** The panel is 12 new public points, role
`indexbuild-cold-v1`, seeds 0..11 ([`make_targets.py`](make_targets.py)).
They are checked against every role of the law named in `EARLIER_ROLES`,
including the template's `closureindexlift-rep-cold-v1`.

A role-agnostic x/y scan
([`inputs/panel_disjointness.json`](inputs/panel_disjointness.json)) found
**0 hits** in all of these:

- origin/main at `5332b222`;
- 853 other origin branches (1,632,523 changed files);
- the scratch worktrees `n83-blrp`, `n83-cli`, `n83-cli-rep`,
  `n83-closure`, `n83-indexlift`, `n83-k899`, `n83-knownlog`,
  `n83-onlineframe` and `n83-rotkey`.

A `git grep` of the new main (`9de0ed9f0`, after #1002 merged) also finds
none. As a positive control, the same grep finds a template panel coordinate
in the template's `cold_targets.json`, `schedule.json` and `runs.jsonl`.

The rank seeds 1401-1436 are new
([`inputs/seed_disjointness.json`](inputs/seed_disjointness.json)). That scan
searched every n83 schedule and protocol on origin/main, on 83 n83 branches
and in the worktrees. Its positive control finds the template's 1201-1230.

## 6. Power and runtime

![Design-stage power and runtime (not a result), from `analysis/power.json`
by [`make_figures.py`](make_figures.py) ([svg](figures/power.svg),
[pdf](figures/power.pdf)).](figures/power.png)

The prior is the template's archived run 39359922687
([`make_power_prior.py`](make_power_prior.py), pinned `runs.jsonl` digest):

- side A's 30 primary pairs (kM38I rank stage; cM38I cold, index build and
  self-test);
- its 20 A/A ratios, used as per-process noise factors. This is conservative
  by about sqrt(2).

Side B is modelled as A minus (1 - f) x index build and self-test. f comes
from the local profile (0.499 and 0.681) in the `modelled` cell, or is set
to hit each effect cell. There are 400 simulations per cell and 500 draws
each.

| true end-to-end effect | P(lower bound > 1) |
| --- | ---: |
| 1.00 (no gain; type I) | 0.005 |
| 1.02 | 1.00 |
| 1.05 | 1.00 |
| **1.10 (minimal effect of interest)** | **1.00** |
| 1.25 | 1.00 |
| **modelled, about 1.63** | **1.00** (median R 1.627, median interval hi/lo 1.028) |

The controls behave as follows in simulation:

- the A/A point estimates are inside the band in 100% of simulations;
- the probe-law gate (576 attempts) passes at the archived law in 100% and
  rejects a law 1.5x worse in 100%;
- the planted lower bound exceeds 1 in 100%, modelled conservatively at
  1.5x.

**Runtime.** The process walls are the template's, with side B's reduced by
the modelled saving, giving:

- about 350 s per point segment;
- a **71.5 min** schedule;
- a **job of about 89 min** with 16 min fixed before (restore, build of
  three binaries, both crates' tests, table checks) and 2 min after;
- **133 min** on a host 1.5x slower.

The time guard is **165 min** and the job limit is **180 min**, so one job
fits within the 3 h budget. Any time-guard skip makes the run invalid.

## Trigger

The run is the workflow
[`.github/workflows/n83-indexbuild.yml`](../../.github/workflows/n83-indexbuild.yml)
(`workflow_dispatch`, plus a push trigger restricted to branch
`claude/n83-indexbuild` and to this experiment's non-receipt paths). The
trigger outcome and the run URL are recorded in [Run](#run).

## Run

A `workflow_dispatch` call (ref `claude/n83-indexbuild`) returned **403**
("Resource not accessible by integration"). The workflow therefore also has a
push trigger. It is restricted to this branch and to the experiment's
non-receipt paths, as in `n83-closure-indexlift-rep.yml`, and the push that
added it started the run at the frozen protocol (`3073d0c5...`) and schedule
(`5b1db827...`). The run is
[39383739494](https://github.com/aburan28/cryptanalysis/actions/runs/39383739494);
the result is in its own [section](#result), leaving the design text above
unchanged.

## Result

Run [39383739494](https://github.com/aburan28/cryptanalysis/actions/runs/39383739494)
(workflow `n83-indexbuild.yml`, push trigger, frozen commit `290fb65a`, attempt
1, conclusion success) on one GitHub-hosted `ubuntu-24.04` runner
(`runnervm8k3b6`, image 20261012.334.1, 4 vCPUs, AMD EPYC 9V74, kernel
6.17.0-1022-azure, execution CPU 0). The run queued for 17 min (created 07:00,
started 07:17 UTC); the job ran 07:17 to 08:50 UTC (1 h 33 min); the runner's
schedule took 77.9 min against the 165-minute guard. The receipt is archived in
[`run_github_39383739494/`](run_github_39383739494/).

**All gates pass; the run is valid.** The runner executed all 282 scheduled
rows (`schedule-exit.txt`: 0): 282 valid, 0 invalid, **0 skipped by the time
guard**, guard not tripped, all 36 primary pairs, 24 A/A pairs and 12 planted
pairs complete, 13 units seen (12 points and Q0).

- Before timing: K600 and M38 tables and both closure bases re-verified by the
  pinned pure-Python oracle (`log-table-check.json`), planted closure
  corruptions rejected; the verifier's 29 unit tests, `cargo test` of `lift2`
  and `online` all ran in the job (`verifier-tests.txt`, `cargo-test-*.txt`).
- Build-pipeline gate: every B process recorded `index_build_pipeline`
  `row_batched_inverse+lookahead32_prefetch+selftest_lanes8`, every A process
  none; the full scan self-test ran in every process.
- One scalar per point across every IC process and rT, replayed in the oracle;
  one relation and one probe count per point and base.
- Layout gate: one index and layout digest set per base (K600, M38, M10), each
  equal to the frozen one (`stored_states_blake3`, `table_slots_blake3`, and
  the logical-state and table-map digests); Q0 equal to the archived
  identities; rank tables equal to the frozen verified tables.
- Planted index check: all 12 cM38IBX processes reported
  `index_plant_checked_inputs` = **30,682,720** (2 x 15,341,360 stored states),
  kept the frozen layout digests and recovered the scalar; every other arm
  reported 0 (`arm.py` gate, 0 issues).
- Per rank seed (36 seeds, 1401-1436): identical relation digests, probe
  vectors, root calls and counters across kM38I, kM38IB and kM38IBaa (0 rows
  without gain, 0 rank-seed failures).
- Probe law gate: kM38I 0.9937 [0.8859, 1.1074] and kM38IB 0.9937 [0.8861,
  1.1062] over 576 attempts (36 blocks), inside the frozen band [0.80, 1.20]
  (pass). The mean probes per relation are identical (1,689,309.2) because the
  arms share rank seeds.
- Runner identity equals the frozen files, binaries unchanged
  (`binaries.sha256`), CPU record unchanged start to end, every process placed
  on CPU 0 (`Cpus_allowed_list` 0, 282/282), `receipt_matches_schedule`, no
  contention flags, no problems.

`verify_receipt.py` re-run on a **copy of the whole receipt directory** (with
`result.json`, `result_table.md` and `verify-stdout.json` removed first; the
gitignored `snapshots/r770` oracle restored by
`restore.py --crypto-repo /home/user/crypto`, read only) reproduces
`panel/result.json`, `panel/result_table.md` and the verifier's stdout **byte
for byte**.

![Frozen ratios with 95% bootstrap intervals, all from `result.json`
([source](figures/result.tex), [vector](figures/result.pdf), [SVG](figures/result.svg),
rendered by the script listed under Files).](figures/result.png)

### Primary and controls (frozen rule)

Improvement iff the 95% lower bound of R = sum E2E(A) / sum E2E(B) over the 36
alternating pairs exceeds 1, with a two-stage paired bootstrap (points, then
pairs within points; 10,000 draws), and both A/A ratios lie in [0.97, 1.03]
and the planted index-build lower bound exceeds 1. A = kM38I + cM38I (the
current n = 83 row, closure + index lift), B = kM38IB + cM38IB (the derived
index-build producer).

| Statistic | Estimate [95%] | Reading |
| --- | --- | --- |
| **R = E2E(A) / E2E(B)** (36 pairs, 12 points) | **1.7406 [1.7129, 1.7676]** | **improvement** (lower bound above 1) |
| geometric mean of the 36 pair ratios | 1.7448 [1.7185, 1.7708] | reported |
| A/A E2E B / Baa (24 pairs) | 0.9998 [0.9984, 1.0011] | pass (inside [0.97, 1.03]) |
| A/A cold cM38IB / cM38IBaa (24 pairs) | 0.9994 [0.9977, 1.0010] | pass (inside [0.97, 1.03]) |
| planted index build cM38IBX / cM38IB (12 pairs) | 2.0847 [2.0812, 2.0876] | pass (lower bound above 1) |
| planted exactness corruptions | rejected before timing | pass |

Mean E2E per side: A 24,736.5 ms (4,433.5 rank stage + 20,303.0 cold),
B 14,211.6 ms (4,429.9 rank stage + 9,781.7 cold), a saving of 10,524.9 ms per
target. The saving is the cold path (10,521.3 ms); the rank stage is unchanged.

### Secondaries (none changes the verdict)

**Per-phase breakdown** (means over the 36 pairs; A over B, above 1 = B
faster):

| Phase | A (kM38I + cM38I) | B (kM38IB + cM38IB) | A / B [95%] |
| --- | ---: | ---: | :--- |
| index-build stage (ms) | 17,084.8 | 7,247.2 | 2.3574 [2.3539, 2.3611] |
| scan self-test (ms) | 2,233.6 | 1,531.6 | 1.4583 [1.4480, 1.4708] |
| setup (ms) | 19,719.4 | 9,195.0 | 2.1446 [2.1404, 2.1493] |
| cold = setup + online (ms) | 20,303.0 | 9,781.7 | 2.0756 [2.0299, 2.1139] |
| rank stage (ms) | 4,433.5 | 4,429.9 | 1.0008 [0.9982, 1.0032] |
| online (ms) | 583.60 | 586.69 | 0.9947 [0.9888, 1.0006] |
| process CPU time (ms) | 49,371.9 | 28,283.9 | 1.7456 [1.7240, 1.7658] |
| process wall (ms) | 49,380.1 | 28,289.6 | 1.7455 [1.7238, 1.7662] |
| cold minor faults | 27,904 | 25,421 | 1.0977 [1.0896, 1.1056] |
| peak RSS (bytes) | 1,897,379,157 | 1,895,541,191 | 1.0010 [1.0009, 1.0011] |
| index build in the rank process (ms) | 17,080.5 | 7,250.2 | 2.3559 [2.3490, 2.3617] |

Of the 10,524.9 ms saved in setup, 9,837.6 ms (93.5%) is the root-index build
(state loop and insert loop), 702.0 ms (6.7%) the lane-wise self-test, and the
rest of setup (base load, linear algebra, input control; about 401 ms in A and
416 ms in B) is 15 ms slower. The index build is 86.6% of A's setup and 78.8%
of B's. The online phase shows no difference (0.9947, interval [0.9888, 1.0006] contains 1). The rank stage and the online phase run the same code in both arms, so their ratios near 1 are the control for the unchanged stages. The process CPU ratio (1.7456) equals the E2E ratio (1.7406) to 0.3%,
and the end-to-end saving is not explained by an off-CPU effect.

**Rank-stage share of E2E cold:** A 17.9% (4,433.5 / 24,736.5), B 31.2%
(4,429.9 / 14,211.6); cold is 82.1% of A and 68.8% of B. Rank-stage ns per
probe: kM38I 164.02, kM38IB 163.94, kM38IBaa 163.90; mean per attempt 277.09,
274.24 and 270.13 ms (kM38IB and kM38IBaa also include the 24 A/A processes).
The per-probe code is the same across arms.

**Probe law** (mean probes per relation over the law value):

| Arm | Estimate [95%] | Attempts | Role |
| --- | --- | ---: | --- |
| kM38I | 0.9937 [0.8859, 1.1074] | 576 (36 blocks) | reported |
| kM38IB | 0.9937 [0.8861, 1.1062] | 576 (36 blocks) | gate, band [0.80, 1.20]: pass |

**S** (cost over this run's measured rT770 step, 317.40 ns, per sqrt(r); one
unit is 29,382.9 ms): end-to-end cold S(A) = 0.84187, S(B) = 0.48367
(delta S = -0.35820); rank stage 0.15089 (A) and 0.15076 (B); setup 0.67112 (A)
and 0.31294 (B); cold without rank 0.69098 (A) and 0.33291 (B); online S(A) =
0.019862, S(B) = 0.019967. The tuned rho's own S: cold 0.11632 (mean rT770
cold 3,417.8 ms, online 3,179.3 ms; 0.10820 online).

**Gap to tuned rho rT770** (IC time over rT time, point estimates from
`result.json`; no interval is computed for the gaps, distance remaining, not a
gate):

| Arm | End-to-end cold | Online |
| --- | ---: | ---: |
| A = kM38I + cM38I (current row) | 7.2375 | 0.1836 (583.60 / 3,179.28 ms) |
| B = kM38IB + cM38IB (candidate) | 4.1581 | 0.1845 (586.69 / 3,179.28 ms) |

The gap is distance remaining: B is 4.16 times the tuned rho end to end, and
no arm beats it. Compared with the parent's runs (6.86 in #997, 8.43 in #1002)
these absolute gaps are not a delta: runner, host class and the rT770 step
(317.40 ns here, 246.64 ns in #1002, 281.09 ns in #997) differ, so only the
paired within-run figures are comparable.

**Per-pair ratio spread** (36 pairs): minimum 1.608, median 1.755, mean 1.746,
maximum 1.891, standard deviation 0.0655, quartile positions (9th and 27th of
36 sorted) 1.695 and 1.789. Per point (12 points): 1.683 to 1.791. By pair
position within the point: 1.747 (first), 1.746 (second), 1.729 (third). By
order: A first (21 pairs) 1.7238, B first (15 pairs) 1.7654, a 2.4% order
effect, with the larger ratio when B runs first. The alternation balances it
only approximately (the start was drawn per point), and it is far inside the
interval's distance from 1.

### Host and isolation records

From `host-cpu.json`, `allocation.json`, `panel/runner_start.json`,
`panel/runner_end.json` and the 282 per-row records in `panel/runs.jsonl`:

| Record | Observed |
| --- | --- |
| provider, instance | GitHub Actions, run 39383739494 attempt 1, instance id `gh-39383739494-1-indexbuild`, runner `runnervm8k3b6` ("GitHub Actions 1000364632"), advertised 4 vCPU / 16 GB, image 20261012.334.1; allocation receipt `allocation.json` |
| CPU | AMD EPYC 9V74 80-Core (family 25, model 17, stepping 1), **no AVX-512 flag exposed** (`avx512=n`; the runner of #1002 exposed AVX-512), 4 vCPUs = 2 cores x 2 threads, 1 socket, 1 NUMA node; Microsoft hypervisor; L2 1 MiB shared by vCPUs 0-1, L3 32 MiB shared by 0-3 |
| microcode | `0xffffffff` (not readable inside the guest), uniform across CPUs, same at start and end |
| frequency | nominal `cpu_mhz` 2799.6 at start, 2861.1 at end; `scaling_cur_freq` not exposed (null), not fixed |
| placement | every process on CPU 0 (`Cpus_allowed_list` 0), 282/282 |
| cgroup | `/system.slice/hosted-compute-agent.service`, `cpu.max` quota none, `isolcpus`/`nohz_full` empty |
| steal | 0 ticks in every row (`/proc/stat`), total 0 |
| throttling | `nr_throttled` 0 and `throttled_usec` 0 in every row |
| memory failures | `memory.events` max and oom_kill deltas 0; 0 major faults |
| scheduling | run-queue wait 1.602 s against 4,671.8 s on CPU (0.034%); 93,842 timeslices; 46,766 involuntary switches in total (at most 411 in one process), 2,784 voluntary |
| CPU pressure | `cpu.pressure` some-delta per row 473 to 6,973 us |
| contention flags | none |
| transparent hugepages | `enabled` always, `defrag` madvise (the runner of #1002 had `enabled` madvise) |

### AGENTS.md Tier 1 assessment

AGENTS.md Tier 1 (cloud instance) requires: a frozen provider allocation
receipt and instance ID; both variants on the same pinned exposed CPU with the
same workload and limits; code and workload hashes, paired order, raw
failures, correctness, process CPU time, memory, cgroup throttling and memory
failures, steal time and scheduling counters; repeated alternating pairs and a
95% paired interval whose lower bound exceeds 1.

**Met:** the allocation record and instance ID (`allocation.json`); one pinned
CPU for all 282 processes with the same workload, binaries and no CPU quota;
code and workload hashes (protocol, schedule, arm wrapper, runner, binaries,
log tables, `frozen.sha256`); paired alternating order from the frozen
schedule; raw failures (0) and correctness (every gate above); process CPU
time, peak RSS, cgroup throttling (0), memory events (0), steal (0) and
`/proc/schedstat` counters per row; 36 alternating pairs and a lower bound of
1.7129.

**Gaps (named, none changes the verdict, all limit the claim):**

1. No host-wide exclusivity. CPU affinity records placement inside the VM; the
   cgroup is the runner agent's service, and the other three vCPUs, the agent
   and the hypervisor's other tenants are not controlled. Steal of 0 in the
   guest does not prove an unshared physical core.
2. The SMT sibling is not excluded. CPU 0 shares its core and its L1/L2 with
   vCPU 1 (cache `shared_cpu_list` 0-1); the sibling thread was not offlined
   or shown idle.
3. Microcode is unreadable (`0xffffffff`), so the CPU identity rests on the
   model name, flags and the unchanged record, not on a microcode revision.
4. The frequency is neither fixed nor observable (`scaling_cur_freq` not
   exposed); only nominal `cpu_mhz` is recorded, and it differed between start
   and end (2799.6 and 2861.1 MHz).
5. No IRQ routing control, no `isolcpus`/`nohz_full`, no NUMA memory policy
   beyond the single node.
6. One instance only (instance scope): another runner may differ; this run's
   host class exposes no AVX-512 and its transparent-hugepage setting is
   `always`, unlike the runner of #1002, so the absolute times, the rT770 step
   and the gaps to it are not comparable across runs, only the paired ratios.

The result is a **Tier 1, instance-scoped** paired wall-time comparison, not
host-isolated (Tier 2).

### Limits of this result

- Tier 1, instance scope: one runner, 12 cold points, 3 alternating pairs per
  point, one fresh process per arm per pair. The interval covers points and
  pairs; it does not cover another host class.
- Wall time on one host class. The saving is the root-index build (state loop
  and insert loop, 9.84 s of 10.52 s) and the self-test (0.70 s); the rank
  stage and the online phase are the parent's code and are unchanged. The
  absolute saving may differ on a host with other memory latency (the
  prefetched insert loop) or with AVX-512.
- **Factor-base construction is charged to no arm** (the n = 83 convention),
  so 1.7406 is an upper bound on the every-phase ratio and the cold S a lower
  bound.
- The gap to rT770 is a point estimate from one run with no interval; the
  rT770 step differs across runs.
- The probe law passes its band with a wide interval ([0.8861, 1.1062]); both
  arms read the same value because the rank seeds are shared.
- The section 5a band is not computable (the IC arms emit no group-operation
  counts). Not replayed on another host class.

## Files

| File | Role |
| --- | --- |
| `make_indexbuild_source.py` | the derivation of side B's producer (7 counted, invertible edits on `1d328b2e...`) |
| `protocol.json`, `make_protocol.py`, `schedule.json`, `make_schedule.py` | frozen protocol (sha256 `3073d0c5...`), its builder, frozen run order (`5b1db827...`) |
| `restore.py` | restore crypto 770f6a69, derive both producers, regenerate the closure headers, check every parent, template and local pin |
| `arm.py` | the parent's wrapper with two marked gates |
| `run_schedule.py`, `check_panel_disjoint.py` | the template's, verbatim |
| `verify_receipt.py`, `test_verify_receipt.py` | gates, statistics, fail-closed decision rule (29 unit tests) |
| `make_targets.py`, `inputs/cold_targets.json`, `inputs/panel_disjointness.json`, `check_seed_disjoint.py`, `inputs/seed_disjointness.json` | the new panel, seeds, and their disjointness records |
| `profile/` | profiling patch (scratch copies only), raw profile and exactness records, summarizers; `inputs/local_profile.json`, `inputs/local_exactness.json` |
| `make_power_prior.py`, `inputs/power_prior.json`, `power_check.py`, `analysis/power.json` | power prior (run 39359922687), simulation and result |
| `make_*_source.py` (other), `make_online_source.py`, `online/`, `lift2/`, `make_closure_base.py`, `verify_closure.py`, `check_log_table.py`, `inputs/factor_logs_*`, `inputs/*` (parent) | the parent's files, byte for byte (except `online/Cargo.toml`: one added `[[bin]]`) |
| `figures/profile.*`, `figures/power.*`, `make_figures.py`, `figures/design.*` | profile and power figures (SVG, PDF, PNG); design diagram (TikZ source, PDF, PNG) |
| `run_github_39383739494/` | the archived receipt: `panel/result.json`, `panel/result_table.md`, `verify-stdout.json`, host and allocation records, 282 per-row records |
| `figures/result.*`, `figures/make_result_figure.py` | result figure (TikZ source, PDF, SVG, PNG), drawn from `result.json` |
| `smoke/` | local correctness smoke of the frozen schedule |
| `README.pdf` | this report: `pandoc README.md -o README.pdf --pdf-engine=pdflatex -H report_header.tex --lua-filter report_filter.lua -V geometry:margin=2cm -V fontsize=10pt -V colorlinks=true` |
