---
title: "n = 83: the online frame loop in the current producer, exact change only (Tier 1 design)"
date: 2026-10-21
---

# n = 83: the online frame loop in the current producer, exact change only (Tier 1 design)

**Status (2026-10-21): design frozen; no Tier 1 timing yet.** The
[protocol](protocol.json) (SHA-256 `50e50718...`) and the
[schedule](schedule.json) (`6c84dfe5...`) were committed before any Tier 1
timing. Every number in this document that is not from an archived run is a
design estimate or a local correctness diagnostic from the shared
cloud-agent VM. Those diagnostics are not timing evidence. The trigger and
the run are recorded under [Run](#run). The result will be added in its own
section, and the design text will stay unchanged.

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

The run is the workflow
[`.github/workflows/n83-onlineframe2.yml`](../../.github/workflows/n83-onlineframe2.yml).
The trigger outcome and the run URL are recorded here when the run starts.

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
| `make_figures.py`, `figures/` | design diagram (TikZ), power figure |
| `README.pdf` | this report: `pandoc README.md -o README.pdf --pdf-engine=pdflatex -H report_header.tex --lua-filter report_filter.lua -V geometry:margin=2cm -V fontsize=10pt -V colorlinks=true` |
