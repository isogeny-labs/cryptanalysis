---
title: "n = 83: round 2 of the root-index build speedup, exact changes only (Tier 1 design)"
date: 2026-10-20
---

# n = 83: round 2 of the root-index build speedup, exact changes only (Tier 1 design)

**Status (2026-10-20): result in. Verdict: improvement; every gate passes and
the run is valid.** R = E2E(A) / E2E(B) = **1.1169 [1.1110, 1.1231]** over 36
alternating pairs (12 points x 3 pairs), run
[39464544962](https://github.com/aburan28/cryptanalysis/actions/runs/39464544962),
Tier 1, instance scope. The design sections below are the frozen text,
unchanged. This round makes only exact, byte-identical changes and uses no
sampled self-test. Every profile figure and saving in the design sections comes
from the shared cloud-agent VM; they are local diagnostics, used only to rank
the candidates and size the design. The [Result](#result) section was added
with the archived receipt.

## Why this run

The n = 83 a = 1 baseline row is the **index-build producer**:

- experiment [`koblitz-n83-indexbuild-20261020`](../koblitz-n83-indexbuild-20261020/README.md);
- PR #1006, run 39383739494;
- source `bc6a31c7...`, binary `ic_online_indexbuild_r770`;
- Tier 1-qualified at 1.7406 [1.7129, 1.7676] over the closure + index-lift
  row.

In that run the row (its side B) spent its 14.21 s end to end as follows:

| Stage (parent run, side B means) | Time (ms) | Share of E2E |
| --- | ---: | ---: |
| root-index build | 7,247.2 | 51% |
| rank stage | 4,429.9 | 31% |
| full scan-order self-test | 1,531.6 | 11% |
| online (one target) | 586.7 | 4% |
| rest of setup (base load, basis, tables, input control) | about 416 | 3% |

The index build is still the largest stage. The rank stage is the next
largest, but it is not an index-build or setup cost, so this round leaves it
alone (see [Not in scope](#not-in-scope)).

## 1. Profile of the current build (local diagnostic)

![LOCAL DIAGNOSTIC: the row's index build and self-test on the M38 closure
header against the round-2 build (bench medians of 5 interleaved rounds),
and every candidate with its modelled saving and status. Rendered from
`inputs/local_profile.json` by `make_figures.py`
([svg](figures/profile.svg), [pdf](figures/profile.pdf)).](figures/profile.png)

**Method.** This follows round 1's instrumented-scratch approach.
[`profile/profile2_patch.py`](profile/profile2_patch.py) patches a *scratch
copy* of the row's producer, which is never committed as a producer. The
patched process loads the M38 header exactly as the producer does and then
does two things.

- With `KIC_INDEX_PROFILE2=1`, it builds the producer's index with the
  producer's own functions, then times each component alone and every
  candidate. Each candidate is asserted equal to the producer's output.
- With `KIC_INDEX_PROFILE2=bench`, it runs five interleaved rounds in
  rotated order. Each round times the insert pipelines on one pre-faulted,
  re-zeroed table (so that first-touch faults drop out of the comparison),
  then the state loops, then the self-tests.

Each process was pinned with `taskset -c 2` and built with rustc 1.97 (the
workflow pins 1.99). `perf` is not available. The VM's transparent huge
pages are `madvise`, but the parent's runner had `always`, so the local
first-touch fault costs (about 0.9 s for the 1 GiB table) are much larger
than on the runner. That is one reason the bench excludes them.
[`profile/summarize2.py`](profile/summarize2.py) writes
[`inputs/local_profile.json`](inputs/local_profile.json) from `profile/raw2/`.

| Component of the row's index build (M38: 15,341,360 stored states, 30,682,720 roots, 2^26 slots) | Local (ms) |
| --- | ---: |
| **state loop** (bench median of 5) | **7,074** |
| &nbsp;&nbsp;prepare (2 table squares, 2 products) | 1,174 |
| &nbsp;&nbsp;Montgomery products + one inversion per row | 1,017 |
| &nbsp;&nbsp;finish (6 products, half trace, trace test) | 1,858 |
| &nbsp;&nbsp;`to_normal` x 2, push, first touch of 736 MB | 4,061 |
| **insert pipeline** on a pre-faulted table (bench median of 5) | **4,005** |
| &nbsp;&nbsp;`lift_scan` canonicalization alone (all roots) | 1,921 |
| &nbsp;&nbsp;prefetched insert alone, from precomputed keys (with faults) | 2,136 |
| &nbsp;&nbsp;first-touch faults alone (1 GiB, read then write per page) | 876 |
| **scan self-test**, 2 keys (bench median of 5; outside the index build) | **1,488** |

The four phase timings come from an instrumented copy with per-row timers,
in one process. They include the fault cost of the 736 MB state vector, so
they add up to more than the bench state loop.

Two findings from the profile:

1. **The canonicalization is not hidden behind the inserts.** The pipeline
   costs about the sum of its parts (4.0 s against 1.9 + 2.1 s). The
   look-ahead overlaps the memory latency, but `lift_scan`'s dependent
   lifting chain (13 serial stages) and its data-dependent candidate loop
   still sit on the critical path, between the inserts' own mispredicts.
2. **The state loop is field arithmetic.** It does 11 field products per
   state (2 in prepare, 3 in Montgomery's trick, 6 in finish), plus three
   table maps and two normal-basis maps. That arithmetic comes with Montgomery's serial
   prefix chain over the 83 states of each row.

## 2. Candidates

Every candidate had to produce byte-identical output: the frozen
`stored_states_blake3` / `table_slots_blake3` and index digests on K600, M38
and M10; the same relations, probes and Q0 identities; and rank tables equal
to the frozen ones. The self-test's coverage was not to change.

| # | Candidate | Proof | Local modelled saving | Status |
| --- | --- | --- | ---: | --- |
| **C9** | State roots from 1/l, 1/r and 1/(l+r): 7 field products per state instead of 11 | algebraic identity + unique inverses (below) | **1.69 s** (state loop 7.07 to 5.39 s) | **implemented** |
| **C7** | Index keys from the linear run finder, 8 roots in lock step | equivalence to lift_scan for every word (below) | **1.46 s** (pipeline 4.00 to 2.55 s) | **implemented** |
| C6 | Bucketed (radix-ordered) insert | plain radix order: **counterexample**; with a left-to-right spill carry: exact (proof below) | **-1.35 s** (slower) | rejected on cost |
| C8 | Build the state loop with `pclmulqdq` enabled so the field products inline | same arithmetic, different inlining | 0.0 s | rejected (no saving) |
| S3 | Branch-free bitmap in the self-test (same domain, same three checks) | same predicate, evaluated without early exit | 0.06 s (noise) | rejected (no saving) |

### C9: the state roots from fewer products (proof)

For a stored state with left code l and right code r, the parent's
`S3Solver128` computes:

- a = (l + r)^2, p = l r, ps = p^2, c = ps + b;
- the denominator a ps, and inv = (a ps)^-1 (one inversion per row);
- q = p (ps inv), d = (c a)(a inv);
- the trace test on d, then first = q HT(d), and the roots [first, first + q].

When a ps = 0 it falls back to `s3_x_roots_128(gf, b, l, r)`.

The round-2 loop computes, for a **regular** state (l != r, l != 0, r != 0):

- q' = p ((l + r)^-1)^2;
- d' = c (l^-1 + r^-1)^2.

These are the same field elements:

- q = p ps / (a ps) = p / a = p ((l + r)^-1)^2 = q';
- d = c a^2 / (a ps) = c a / ps, and a / ps = (l + r)^2 / (l r)^2 =
  ((l + r)/(l r))^2 = (1/r + 1/l)^2, so d = d'.

The regular states are exactly the parent's non-zero denominators. Squaring
is injective, so a = 0 iff l = r, and GF(2^83) has no zero divisors, so
ps = 0 iff l = 0 or r = 0. Every irregular state (the 600 or 608 diagonal
relative-0 states per base) takes the parent's own fallback call.

The inverses are field inverses:

- 1/l and 1/r: the inverse of a representative x, squared k times, is the
  inverse of its k-th Frobenius shift x^(2^k). Each one is checked by a
  product at build time.
- 1/(l + r): Montgomery's trick over four interleaved chains (position mod
  4), with one inversion per row. The chains break the parent's serial
  prefix chain.

A non-zero field element has exactly one inverse, and every field element
has exactly one reduced representation. So q', d', the trace test, the half
trace, the root order, the `to_normal` images and the pushed states are the
parent's, bit for bit. The cost is 7 products per state: p, d, q, first, and
3 for Montgomery's trick.

### C7: the linear run finder (proof)

lift_scan's convention: bit i is normal-basis coefficient i,
rotl(x, s) = ((x << s) | (x >> (N - s))) & mask, and the canonical form is
(min_s rotl(x, s), least such s). The words 0 and all-ones get shift 0.

For a nonconstant N-bit word v, let z_1 = !v and
z_(j+1) = z_j & rotl(z_j, 1). By induction, bit p of z_j is set iff the j
bits p, p-1, ..., p-j+1 (cyclically) are all zero:

- z_(j+1)[p] = z_j[p] & z_j[p-1];
- that is "bits p..p-j+1 zero" and "bits p-1..p-j zero", which is "bits
  p..p-j zero".

So z_j != 0 iff j <= L, where L is the longest cyclic zero run (1 <= L <= N - 1
for a nonconstant word). The loop stops with z = Z_L, the tops of all
longest runs. That is exactly the run set lift_scan's greedy lifting ends
with (`lift2/src/lib.rs`: "R = the tops of all longest runs").

The candidates s = N - 1 - p and the choice between them are lift_scan's own
code: the least rotation, ties to the smaller shift. That choice is a
lexicographic minimum, so it does not depend on the order in which the
candidates are visited. Hence the key and the shift equal lift_scan's for
every word.

In the eight-lane form, a lane that has reached its Z_L keeps it by a select
(no jump) while the other lanes continue. The word 0 starts at z = 0 (an
all-ones z would never shrink). The keys are computed once per root, in
increasing root order: eight at a time, 32 to 40 roots ahead, with the tail
one at a time by the parent's call. Each key's home slot is prefetched.
`insert_if_absent` receives the parent's (key, value) sequence, so every slot
word is the parent's. In `lift_plant` every linear key is also checked
against lift_scan and the selected canonicalizer, with one planted count per
root as before.

**Tested:**

- exhaustively against the full scan on every word of 3 to 20 bits, both
  the scalar and the eight-lane form;
- exhaustively against lift_scan on eight small two-limb geometries
  ((5,3), (7,4), (9,5), (12,8), (13,7), (16,8), (18,12) and (20,11), which
  exercise the limb carry and the wrap);
- against lift_scan on 2^22 random 83-bit words and on about 207,000
  structured ones: every single run at every start (including across the
  wrap), two- and three-way ties, sparse and dense words, and 0 and
  all-ones;
- against lift_scan on **every stored root of K600, M38 and M10**
  (29,880,600 + 30,682,720 + 29,880,600 roots, 0 key and 0 shift
  mismatches). About 27% of those roots have tied longest runs.

### C6: bucketed or radix-ordered insert (proof and rejection)

**A plain radix or bucket order is not exact.** Linear probing with
first-wins is order-dependent. Take keys x and y with home h, and z with
home h + 1:

- inserted in the order z, x, y, the table holds z at h+1, x at h and y at
  h+2;
- sorted by home (x, y, z), it holds x at h, y at h+1 and z at h+2.

So the final layout is **not** order-independent, and sorting the inserts by
home slot changes `table_slots_blake3`.

**An exact bucketed form exists.** It does the following:

1. Partition the inserts stably by home-slot range: 2^k contiguous ranges,
   with each insert's global index kept.
2. Process the ranges left to right. A probe that walks past its range's
   end becomes a *carry* into the next range. The carry enters that range at
   its first slot, with its global index.
3. Within a range, merge the range's own inserts and the incoming carries
   by global index.

*Proof.* An insert reads and writes only the slots from its entry point
forward to where it stops. So range k's slots are touched only by the keys
that enter range k: its own keys at their home slots, and carries at its
first slot. A key leaves range k (becomes a carry) depending only on range
k's state at its arrival. By induction on k, the merged sequence is the
parent's sequence restricted to range k, in the parent's order, so range k
evolves exactly as in the parent, and so do its outgoing carries.
Duplicates are covered: a duplicate has its first occurrence's home, so it
follows the same path. A wrap from the last range into range 0 needs a
second pass over range 0. None occurred on M38.

**Measured:** exact on M38 (slot words equal for 2^10, 2^12 and 2^14 buckets,
with 195, 783 and 3,138 carries), but slower. The partition alone costs
0.8 to 1.7 s, the bucketed insert costs 2.4 to 5.0 s, and the prefetched
insert it would replace costs 2.1 s. The prefetched insert is no longer
latency-bound: most of what is left is first-touch and bandwidth, which
bucketing does not remove. C6 also needs about 614 MB more memory. **Rejected on cost.**

### Not in scope

- **Sampled self-test (round 1's S2).** It is not used, as instructed. The
  self-test is the parent's exhaustive eight-image loop, unchanged.
- **Rank stage (31% of E2E).** Its code is unchanged and gated identical per
  seed. Its probe loop also canonicalizes with lift_scan
  (`KIC_RANK_CANON=lift`, `KIC_TARGET_CANON=lift`), so C7 could carry over
  there exactly. That is a separate, named follow-up, not part of this
  round.
- **Other lift_scan variants measured:**
  - lift_scan's own runs, 8 lanes: 1.35 s;
  - linear with 10 jump-free steps: 1.69 s;
  - block-pipelined lift_scan: 3.59 s.

  All are exact, and the chosen lane-linear pipeline beats each of them.

## 3. What is implemented: a counted derivation

[`make_indexbuild2_source.py`](make_indexbuild2_source.py) follows the
parents' `make_*_source.py` pattern:

1. It re-derives the row's producer with the parent's
   `make_indexbuild_source.py` (verbatim). That script re-derives the
   closure + index-lift producer `1d328b2e...` through its own verbatim
   chain and runs its own inverse check.
2. It requires the result to be `bc6a31c7...`.
3. It applies **7 counted replacements**, each of which must occur exactly
   once:
   - the header comment;
   - two constants;
   - the new functions;
   - the state loop (C9);
   - the compact insert loop (C7);
   - the summary field `index_build_pipeline`, now
     `sum_inverse_lanes4+linear_canon_lanes8+lookahead32_prefetch+selftest_lanes8`;
   - one appended test module.
4. `check_inverse()` undoes them on every derivation and must get the
   parent's bytes back.

The derived source is `4008a47a...`
(`koblitz_orbit_dlp_fast_online_indexbuild2.rs`), and the binary is
`ic_online_indexbuild2_r770`. Both IC binaries are built by one `cargo build`
from the parent's lock file. `online/Cargo.toml` drops the grandparent's
`[[bin]]` (it is still derived, but no longer an arm) and adds this one.

[`restore.py`](restore.py) checks the following on every build:

- the parent protocol `3073d0c5...`;
- side A's producer equals the parent's frozen `bc6a31c7...`, and the
  grandparent equals `1d328b2e...`;
- both closure headers;
- the 29 files copied byte for byte from the parent (`VERBATIM`), including
  `arm.py`, `make_schedule.py`, `run_schedule.py`, `check_log_table.py`,
  `lift2/` and `scripts/host_cpu_record.py`;
- every local pin in `protocol.json`.

**`indexbuild2_tests`** (7 tests, in the online crate's
`cargo test --bins`, which the workflow runs before timing). The parent's
state loop and compact insert loop are kept there verbatim (re-indented) as
references. The tests cover:

- C9's states, slot words, entries and planted counts against the parent's
  loops, for widths 1, 2, 9 and 17, every index canonicalizer (selected,
  lift, lift_plant), folded and planted modes, and compact and base tables;
- `s3_roots_from_inverses` against `S3Solver128::roots` on 200,000 random
  pairs, including the trace test's `None` branch;
- `sum_inverses_lanes4` against `gf.inv` for every count 0..90;
- `index_keys8` against `index_canonical128` in every mode;
- the linear canonicalizer tests listed under C7.

All 32 tests of the derived binary pass: the parent's 25 (including round
1's 4 `indexbuild_tests`, now run against the round-2 functions) and the 7
new ones ([`profile/raw2/cargo-test-online-indexbuild2.txt`](profile/raw2/cargo-test-online-indexbuild2.txt)).

## 4. Exactness checks before freezing (cloud-agent VM, correctness only)

[`inputs/local_exactness.json`](inputs/local_exactness.json) is written by
`profile/summarize2.py` from `profile/raw2/`. It records two kinds of check.

**Whole-base check** ([`profile/exactness2_patch.py`](profile/exactness2_patch.py),
a scratch copy of the round-2 producer). On **K600, M38 and M10**:

- every stored state equals the parent's state loop (verbatim);
- every slot word equals the parent's insert loop (verbatim);
- the linear key and shift equal `lift_scan` on every stored root (0
  mismatches on each base);
- 600, 608 and 600 irregular states took the fallback.

**Full-gate processes** (`arm.py`, verbatim from the parent, run with the
frozen protocol's arms). The round-2 producer:

- reproduced the frozen **layout digests** on **K600**
  (`d8cfe443...`/`5f53764e...`), **M38** (`f7a8d6b8...`/`6c08c6c2...`) and
  **M10** (`c90b501b...`/`4973cfe5...`);
- reproduced the **Q0 identities** on all three bases:
  - 1,987,852, 1,612,533 and 2,130,165 probes;
  - the frozen relations;
  - scalar 3141592653589793;
- passed `cM38ICX` with 30,682,720 planted checks (2 x 15,341,360);
- on rank seed 1501, gave the **same rank relation digest, per-attempt probe
  vector and root calls** as the row's producer, with the rank table equal
  to the frozen verified table.

**Smoke of the frozen schedule**: O1 and P1 after freezing; see
[`smoke/README.md`](smoke/README.md).

## 5. Frozen design (Tier 1, repeated alternating pairs)

![Design (from the frozen protocol and schedule; not a result). Source
[figures/design.tex](figures/design.tex), vector
[figures/design.pdf](figures/design.pdf).](figures/design.png)

The design is the parent's (itself the Tier 1 template's): one GitHub
`ubuntu-24.04` runner, and a fresh process for every run, pinned to one CPU
with a clean environment. It keeps:

- `run_schedule.py` (verbatim): CPU record, placement, scheduling counters,
  cgroup, steal and fault counters, time guard;
- `arm.py` (verbatim);
- the two-stage paired bootstrap, the A/A band, and the hardened fail-closed
  verifier with only the arm names changed (30 unit tests).

**Sides and pairs.**

| side | processes, in order | binary |
| --- | --- | --- |
| **A** | kM38IB (rank stage, 16 attempts on M38, pair's seed, then the point), then cM38IB (verified table, the point) | the row, `ic_online_indexbuild_r770` (the parent's arms, verbatim) |
| **B** | kM38IC (same seed), then cM38IC | round 2, `ic_online_indexbuild2_r770` |
| **Baa** | kM38ICaa, then cM38ICaa | A/A copy of B |

- **Primary:** 12 points x **3 pairs = 36 primary pairs**. Each point's six
  sides strictly alternate, ABABAB or BABABA; 8 points start with A and 4
  with B. Seed of pair *j* at point *i*: 1500 + 3*i* + *j* (1501-1536, new).
- **A/A:** 2 pairs per point (B against Baa), with the seeds of primary
  pairs 1 and 2.
- **Planted:** 1 cold pair per point, cM38IC against cM38ICX. In cM38ICX,
  `lift_plant` checks every linear key against lift_scan and the selected
  canonicalizer: same layout, slower index build (locally 2.1x).
- **rho:** one rT per point, seed 1040000 + point seed.
- **O1:** Q0 on cPIB, cPIC, cM10IB, cM10IC, cM38IB and cM38IC, so both
  binaries run on all three bases. This is exactness only.
- In total, **282 processes**. Sub-block order and starts come from
  `random.Random(2026102070 + i)`.

**Primary (pre-registered).**

- E2E(side) = `timing_ms.rank_stage` (rank process) + `cold_in_process_ms`
  (cold process).
- R = sum E2E(A) / sum E2E(B) over the 36 pairs.
- 95% two-stage paired bootstrap: points, then pairs within points, with A
  and B of a pair kept together; 10,000 draws, `random.Random(20261040)`.
- **Improvement iff the lower bound > 1.** Regression iff the upper bound
  < 1. Otherwise not separated.
- **Invalid** if any gate is false or unknown, if any control fails, or if
  any row is missing (including time-guard skips).

**Stage secondary (labelled):** the index-build ratio, cM38IB / cM38IC
`timing_ms.index_build`, with the same bootstrap. The run also reports the
index build in the rank processes.

**Other secondaries (descriptive):** geometric mean of the pair ratios;
cold, setup, self-test (expected about 1, since the code is unchanged),
online, rank stage (expected about 1), CPU time, wall, peak RSS and faults;
per point, by pair position and by side order; probe law; S and the gap to
rT.

**Controls.**

- **A/A:** E2E(B)/E2E(Baa) and cold cM38IC/cM38ICaa, each inside
  [0.97, 1.03] over 24 pairs.
- **Planted timing:** index build cM38ICX/cM38IC, lower 95% bound > 1 over
  12 pairs.
- **Planted exactness:**
  - the three closure corruptions rejected before timing
    (`check_log_table.py`);
  - the parent's planted non-bijections rejected in the crate tests;
  - every cM38ICX checks 2 x 15,341,360 roots and keeps the frozen layout.

**Gates.** All gates are the parent's and fail closed; an unknown gate
counts as a failure:

- every row ran its arm's binary, by name and by digest;
- one index and layout digest set per base on K600, M38 and M10, equal to
  the frozen one;
- Q0 identities on all six O1 arms;
- one scalar, relation and probe count per point, replayed in the oracle;
- rank tables equal to the frozen tables;
- per rank seed, identical relation digests, probe vectors, root calls and
  counters across kM38IB, kM38IC and kM38ICaa;
- the probe-law band for kM38IB over 36 seeds (576 attempts);
- placement, CPU identity, schedule identity and order.

**Panel and seeds.** The panel is 12 new public points, role
`indexbuild2-cold-v1`, seeds 0..11 ([`make_targets.py`](make_targets.py)).
They are checked against every earlier role of the law, including the
parent's `indexbuild-cold-v1`. A role-agnostic x/y scan
([`inputs/panel_disjointness.json`](inputs/panel_disjointness.json)) found
**0 hits** in all of these:

- origin/main at `5ab7d5bc`;
- 858 other origin branches (1,645,857 changed files);
- the ten scratch n83 worktrees.

The rank seeds 1501-1536 are new
([`inputs/seed_disjointness.json`](inputs/seed_disjointness.json): 85 refs
plus the worktrees). The scan's positive control finds the parent's
1401-1436.

## 6. Power and runtime

![Design-stage power and runtime (not a result), from `analysis/power.json`
by [`make_figures.py`](make_figures.py) ([svg](figures/power.svg),
[pdf](figures/power.pdf)).](figures/power.png)

The prior is the parent's archived run 39383739494
([`make_power_prior.py`](make_power_prior.py), pinned `runs.jsonl` digest
`fe0c3659...`):

- the row's 36 primary pairs (kM38IB rank stage; cM38IB cold, index build
  and self-test);
- its 24 A/A ratios, used as per-process noise factors. This is
  conservative by about sqrt(2).

Side B is modelled as A minus (1 - f) x index build, with the self-test
unchanged. f comes from the local alternating cold processes, 0.729: the
round-2 index build at 10.03 s against 13.75 s for the row, three pairs on
s000. The smoke of the frozen schedule ([`smoke/README.md`](smoke/README.md)) showed a smaller local gap (about 0.87); at that factor the model predicts about 1.07, still above the minimal effect of interest 1.05, where the power is 1.00. In the effect cells, f is set to hit each effect. There are 400
simulations per cell and 500 draws each.

| true end-to-end effect | P(lower bound > 1) |
| --- | ---: |
| 1.00 (no gain; type I) | 0.005 |
| 1.02 | 1.00 |
| 1.03 | 1.00 |
| **1.05 (minimal effect of interest)** | **1.00** |
| 1.10 | 1.00 |
| **modelled, about 1.160** | **1.00** (median interval hi/lo 1.013) |

At the parent run's means, the model predicts the following. These are
estimates for sizing the design, not claims:

- end to end about **1.16**;
- cold about 1.25;
- index build about 1.37.

The controls behave as follows in simulation:

- the A/A point estimates are inside the band in 100% of simulations;
- the probe-law gate (576 attempts) passes at the archived law in 100% and
  rejects a law 1.5x worse in 100%;
- the planted lower bound exceeds 1 in 100%, modelled at 1.5x.

**Runtime.** The process walls are the parent run's, with side B's reduced
by the modelled saving, giving:

- about 287 s per point segment;
- a **59 min** schedule;
- a **job of about 77 min** with 16 min fixed before (restore, build of three
  binaries, both crates' tests, table checks) and 2 min after;
- **114 min** on a host 1.5x slower.

The time guard is **165 min** and the job limit is **180 min**, so one job
fits within the 3 h budget. Any time-guard skip makes the run invalid.

## Trigger

The run is the workflow
[`.github/workflows/n83-indexbuild2.yml`](../../.github/workflows/n83-indexbuild2.yml)
(`workflow_dispatch`, plus a push trigger restricted to branch
`claude/n83-indexbuild2` and to this experiment's non-receipt paths). The
trigger outcome and the run URL are recorded in [Run](#run).

## Run

A `workflow_dispatch` call (ref `claude/n83-indexbuild2`) returned **403**
("Resource not accessible by integration"). The workflow therefore also has a
push trigger. It is restricted to this branch and to the experiment's
non-receipt paths, as in the parent's `n83-indexbuild.yml`. The push that
added it (commit `d2d63308`) started the run at the frozen protocol
(`5cee1a72...`) and schedule (`f5ac4c17...`). The run is
[39464544962](https://github.com/aburan28/cryptanalysis/actions/runs/39464544962).
The result is in its own [section](#result), leaving the design text above
unchanged.

## Result

Run [39464544962](https://github.com/aburan28/cryptanalysis/actions/runs/39464544962)
(workflow `n83-indexbuild2.yml`, push trigger, frozen commit `d2d63308`, attempt
1, conclusion success) on one GitHub-hosted `ubuntu-24.04` runner
(`GitHub Actions 1000367839`, image 20261012.334.1, 4 vCPUs, Intel Xeon
Platinum 8370C, kernel 6.17.0-1022-azure, execution CPU 0). The run queued for
62 min (created 17:15, started 18:17 UTC); the job ran 18:17 to 19:25 UTC
(68 min); the runner's schedule took 52.9 min against the 165-minute guard.
The receipt is archived in [`run_github_39464544962/`](run_github_39464544962/).

**All gates pass; the run is valid.** The runner executed all 282 scheduled
rows (`schedule-exit.txt`: 0): 282 valid, 0 invalid, **0 skipped by the time
guard**, guard not tripped, all 36 primary pairs, 24 A/A pairs and 12 planted
pairs complete, 13 units seen (12 points and Q0).

- Before timing: K600 and M38 tables and both closure bases re-verified by the
  pinned pure-Python oracle (`log-table-check.json`, 10 of 10 PASS), planted
  closure corruptions rejected; the verifier's 30 unit tests, `cargo test` of
  `lift2` (24 tests) and `online` (32 tests of the round-2 binary, 25 of the
  parent's, 4 of rho) all ran in the job and passed (`verifier-tests.txt`,
  `cargo-test-*.txt`).
- Build-pipeline gate: every B process recorded `index_build_pipeline`
  `sum_inverse_lanes4+linear_canon_lanes8+lookahead32_prefetch+selftest_lanes8`,
  every A process `row_batched_inverse+lookahead32_prefetch+selftest_lanes8`;
  the full scan self-test ran in every process.
- One scalar per point across every IC process and rT, replayed in the oracle;
  one relation and one probe count per point and base.
- Layout gate: one index and layout digest set per base (K600, M38, M10), each
  equal to the frozen one; Q0 equal to the archived identities; rank tables
  equal to the frozen verified tables.
- Planted index check: all 12 cM38ICX processes reported
  `index_plant_checked_inputs` = **30,682,720** (2 x 15,341,360 stored states),
  kept the frozen layout digests and recovered the scalar; every other arm
  reported 0.
- Per rank seed (36 seeds, 1501-1536): identical relation digests, probe
  vectors, root calls and counters across kM38IB, kM38IC and kM38ICaa (0 rows
  without gain, 0 rank-seed failures).
- Probe law gate: kM38IB 1.0479 [0.9380, 1.1750] and kM38IC 1.0479 [0.9378,
  1.1716] over 576 attempts (36 blocks), inside the frozen band [0.80, 1.20]
  (pass). The mean probes per relation are identical (1,781,484.5) because the
  arms share rank seeds.
- Runner identity equals the frozen files (protocol `5cee1a72...`, schedule
  `f5ac4c17...`), binaries unchanged (`binaries.sha256`), CPU record unchanged
  start to end, every process placed on CPU 0 (`Cpus_allowed_list` 0, 282/282),
  `receipt_matches_schedule`, no contention flags, no problems.

`verify_receipt.py` re-run on a **copy of the whole receipt directory** (with
the gitignored `snapshots/r770` oracle, crypto 770f6a69, as restored in the
worktree; the verifier reads only that snapshot) reproduces `panel/result.json` and `panel/result_table.md` **byte
for byte** (`cmp`) and the same decision and statistics on stdout.

![Frozen ratios with 95% bootstrap intervals, all from `result.json`
([source](figures/result.tex), [vector](figures/result.pdf), [SVG](figures/result.svg),
rendered by the script listed under Files).](figures/result.png)

### Primary and controls (frozen rule)

Improvement iff the 95% lower bound of R = sum E2E(A) / sum E2E(B) over the 36
alternating pairs exceeds 1, with a two-stage paired bootstrap (points, then
pairs within points; 10,000 draws), and both A/A ratios lie in [0.97, 1.03]
and the planted index-build lower bound exceeds 1. A = kM38IB + cM38IB (the
current n = 83 row, the index-build producer), B = kM38IC + cM38IC (the
round-2 derived producer).

| Statistic | Estimate [95%] | Reading |
| --- | --- | --- |
| **R = E2E(A) / E2E(B)** (36 pairs, 12 points) | **1.1169 [1.1110, 1.1231]** | **improvement** (lower bound above 1) |
| geometric mean of the 36 pair ratios | 1.1178 [1.1120, 1.1238] | reported |
| A/A E2E B / Baa (24 pairs) | 0.9996 [0.9968, 1.0024] | pass (inside [0.97, 1.03]) |
| A/A cold cM38IC / cM38ICaa (24 pairs) | 0.9993 [0.9953, 1.0036] | pass (inside [0.97, 1.03]) |
| planted index build cM38ICX / cM38IC (12 pairs) | 2.5856 [2.5830, 2.5883] | pass (lower bound above 1) |
| planted exactness corruptions | rejected before timing | pass |

Mean E2E per side: A 12,886.3 ms (4,235.5 rank stage + 8,650.7 cold),
B 11,537.5 ms (4,216.1 rank stage + 7,321.3 cold), a saving of 1,348.8 ms per
target. Of it, 1,331.1 ms (98.7%) is the root-index build, 19.4 ms the rank
stage, 2.7 ms the online phase, and the self-test and the rest of setup are
slightly slower (3.1 ms and 1.3 ms). The ratio of 1.117 is below the design's
modelled 1.16 and above the minimal effect of interest, 1.05 (the local smoke
suggested 1.07).

### Secondaries (none changes the verdict)

**Per-phase breakdown** (means over the 36 pairs; A over B, above 1 = B
faster):

| Phase | A (kM38IB + cM38IB) | B (kM38IC + cM38IC) | A / B [95%] |
| --- | ---: | ---: | :--- |
| index-build stage (ms) | 6,501.9 | 5,170.8 | **1.2574 [1.2563, 1.2586]** (labelled stage secondary) |
| scan self-test (ms) | 1,433.9 | 1,436.9 | 0.9979 [0.9750, 1.0214] |
| setup (ms) | 8,315.7 | 6,989.0 | 1.1898 [1.1844, 1.1954] |
| cold = setup + online (ms) | 8,650.7 | 7,321.3 | 1.1816 [1.1746, 1.1891] |
| rank stage (ms) | 4,235.5 | 4,216.1 | 1.0046 [1.0033, 1.0059] |
| online (ms) | 335.08 | 332.36 | 1.0082 [1.0068, 1.0098] |
| process CPU time (ms) | 25,015.5 | 22,327.1 | 1.1204 [1.1159, 1.1248] |
| process wall (ms) | 25,020.4 | 22,331.0 | 1.1204 [1.1159, 1.1249] |
| cold minor faults | 25,475 | 25,451 | 1.0010 [0.9948, 1.0071] |
| peak RSS (bytes) | 1,895,713,337 | 1,895,754,069 | 1.0000 [0.9999, 1.0001] |
| index build in the rank process (ms) | 6,497.1 | 5,173.4 | 1.2559 [1.2549, 1.2568] |

The index-build stage ratio 1.2574 is the whole effect: the build is 50.5% of
A's E2E and 44.8% of B's, and 78.2% of A's setup and 74.0% of B's. The
self-test (the same code in both arms, ratio 0.9979, interval contains 1) and
the rest of setup (base load, linear algebra, input control; 379.9 ms in A and
381.2 ms in B) are controls for the unchanged setup stages. The process CPU
ratio (1.1204) and wall ratio (1.1204) equal the cold-path saving seen in the
timed stages, and the end-to-end saving is not explained by an off-CPU effect.

Two unchanged stages have intervals that **exclude 1**: the rank stage (1.0046
[1.0033, 1.0059]) and the online phase (1.0082 [1.0068, 1.0098]) run the same
source in both arms, so these are not treatment effects of the frozen edits.
They are small (the rank stage 0.46%, online 0.82%, together 22.1 ms of the
1,348.8 ms saving), they are not a gate, and this run cannot tell their cause
(binary layout and alignment of the two binaries, or cache and page state left
behind by the faster build, are candidates, untested). The A/A pairs (B against
an identical copy, ratio 0.9996) show no such offset between identical binaries,
and the parent's run read 1.0008 [0.9982, 1.0032] and 0.9947 [0.9888, 1.0006] on
the same two stages. If both were set to 1.0, R would be 1.1148, still above 1.

**Rank-stage share of E2E:** A 32.9% (4,235.5 / 12,886.3), B 36.5% (4,216.1 /
11,537.5); cold is 67.1% of A and 63.5% of B. Rank-stage ns per probe: kM38IB
148.59, kM38IC 147.95, kM38ICaa 147.99 (the per-attempt means, 264.7, 257.9 and
249.5 ms, are over different seed sets: 36, 60 and 24 blocks, so only the
paired ratio is a comparison).

**Probe law** (mean probes per relation over the law value):

| Arm | Estimate [95%] | Attempts | Role |
| --- | --- | ---: | --- |
| kM38IB | 1.0479 [0.9380, 1.1750] | 576 (36 blocks) | gate, band [0.80, 1.20]: pass |
| kM38IC | 1.0479 [0.9378, 1.1716] | 576 (36 blocks) | reported |

**S** (cost over this run's measured rT770 step, 275.04 ns, per sqrt(r); one
unit is 25,460.9 ms):

| Quantity | S(A) | S(B) | delta S |
| --- | ---: | ---: | ---: |
| end-to-end cold | 0.50612 | 0.45315 | -0.05298 |
| rank stage | 0.16635 | 0.16559 | -0.00076 |
| setup without the rank stage | 0.32661 | 0.27450 | -0.05211 |
| setup with the rank stage | 0.49296 | 0.44009 | -0.05287 |
| cold without the rank stage | 0.33977 | 0.28755 | -0.05221 |
| online | 0.013161 | 0.013054 | -0.000107 |

The tuned rho's own S: cold 0.10261 (mean rT770 cold 2,612.4 ms), online 0.09180
(2,337.4 ms).

**Gap to tuned rho rT770** (IC time over rT time, point estimates from
`result.json`; no interval is computed for the gaps, distance remaining, not a
gate):

| Arm | End-to-end cold | Online |
| --- | ---: | ---: |
| A = kM38IB + cM38IB (current row) | 4.9327 | 0.1434 (335.08 / 2,337.42 ms) |
| B = kM38IC + cM38IC (candidate) | 4.4164 | 0.1422 (332.36 / 2,337.42 ms) |

The gap is distance remaining: B is 4.42 times the tuned rho end to end, and no
arm beats it. **Cross-run rho-gap artifact:** the same producer as A, as side B
of run 39383739494, read 4.158 over that run's rT770. The new producer's 4.416
here is numerically larger than that landed 4.158, although the new producer is
faster than the old one in this run's paired comparison (4.933 to 4.416, 1.117x
closer). The runs differ in host class (this runner has an Intel Xeon Platinum
8370C with AVX-512 exposed; that one an AMD EPYC 9V74 without) and
in the rT770 step (275.04 ns here, 317.40 ns there; the rho runs 2,612.4 ms cold
here against 3,417.8 ms there, the IC's A side 12,886.3 ms against 14,211.6 ms),
so only the paired within-run gap is a delta; the absolute gaps are not
comparable across runs.

**Per-pair ratio spread** (36 pairs): minimum 1.0911, median 1.1179, mean
1.1179, maximum 1.1479, standard deviation 0.0131, quartile positions (9th and
27th of 36 sorted) 1.1095 and 1.1260. Per point (12 points): 1.1017 to 1.1330.
By pair position within the point: 1.1162 (first), 1.1222 (second), 1.1126
(third). By order: A first (24 pairs) 1.1172, B first (12 pairs) 1.1163, an
order effect of 0.09% (the start was drawn per point, 8 points A first, 4 B
first), far inside the interval's distance from 1.

### Host and isolation records

From `host-cpu.json`, `allocation.json`, `host-probe.json`,
`panel/runner_start.json`, `panel/runner_end.json` and the 282 per-row records
in `panel/runs.jsonl`:

| Record | Observed |
| --- | --- |
| provider, instance | GitHub Actions, run 39464544962 attempt 1, instance id `gh-39464544962-1-indexbuild2`, runner `GitHub Actions 1000367839`, advertised 4 vCPU / 16 GB, image 20261012.334.1; allocation receipt `allocation.json` |
| CPU | Intel Xeon Platinum 8370C @ 2.80 GHz (family 6, model 106, stepping 6), **AVX-512 exposed** (the parent's AMD EPYC 9V74 exposed none), 4 vCPUs = 2 cores x 2 threads, 1 socket, 1 NUMA node; Microsoft hypervisor; L1d 48 KiB and L2 1.25 MiB per core shared by vCPUs 0-1, L3 48 MiB shared by 0-3 |
| microcode | `0xffffffff` (not readable inside the guest), uniform across CPUs, same at start and end |
| frequency | `lscpu` max 2800 MHz, nominal `cpu_mhz` 3490.5 at start and 3487.0 at end; the per-row `frequency_khz` readings on CPU 0 range from 2,475,754 to 3,599,001 kHz: not fixed, and varying by about 45% across the run |
| placement | every process on CPU 0 (`Cpus_allowed_list` 0), 282/282 |
| cgroup | `/system.slice/hosted-compute-agent.service`, `cpu.max` quota none, `isolcpus` / isolated CPUs empty |
| steal | 0 ticks in every row (`/proc/stat`), total 0 |
| throttling | `nr_throttled` 0 and `throttled_usec` 0 in every row |
| memory failures | `memory.events` max and oom_kill deltas 0; 0 major faults |
| scheduling | run-queue wait 1.444 s against 3,171.0 s on CPU (0.046%); 68,656 timeslices; 34,203 involuntary switches in total (at most 358 in one process), 2,718 voluntary |
| CPU pressure | `cpu.pressure` some-delta per row 773 to 5,142 us |
| contention flags | none |
| transparent hugepages | `enabled` always, `defrag` madvise (as the parent's run) |

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
scheduler counters per row; 36 alternating pairs and a lower bound of 1.1110.

**Gaps (named, none changes the verdict, all limit the claim):**

1. No host-wide exclusivity. CPU affinity records placement inside the VM; the
   cgroup is the runner agent's service, and the other three vCPUs, the agent
   and the hypervisor's other tenants are not controlled. Steal of 0 in the
   guest does not prove an unshared physical core.
2. The SMT sibling is not excluded. CPU 0 shares its core and its L1/L2 with
   vCPU 1 (cache `shared_cpu_list` 0-1); the sibling thread was not offlined or
   shown idle.
3. Microcode is unreadable (`0xffffffff`), so the CPU identity rests on the
   model name, flags and the unchanged record, not on a microcode revision.
4. The frequency is neither fixed nor controlled: the per-row readings span
   2.48 to 3.60 GHz while the nominal value stays near 3.49 GHz. The pairs are
   adjacent in time and alternate, which balances a slow drift but not a fast
   one.
5. No IRQ routing control, no `isolcpus` / `nohz_full`, no NUMA memory policy
   beyond the single node.
6. One instance only (instance scope): another runner may differ. This host
   class (Intel Xeon Platinum 8370C, AVX-512 exposed) differs from the parent's
   (AMD EPYC 9V74), so the absolute times, the rT770 step and the gaps to it
   are not comparable across runs, only the paired ratios. The saving rests on
   field arithmetic and the insert loop, whose cost depends on the host, and has
   not been replayed on another host class.

The result is a **Tier 1, instance-scoped** paired wall-time comparison, not
host-isolated (Tier 2).

### Limits of this result

- Tier 1, instance scope: one runner, 12 cold points, 3 alternating pairs per
  point, one fresh process per arm per pair. The interval covers points and
  pairs; it does not cover another host class.
- Wall time on one host class. The saving is the root-index build (1,331.1 ms
  of 1,348.8 ms); the self-test, the rest of setup, the rank stage's code and
  the online code are the parent's and unchanged. The rank stage and online
  ratios 1.0046 and 1.0082 are small unexplained offsets (see Secondaries).
- **Factor-base construction is charged to no arm** (the n = 83 convention),
  so 1.1169 is an upper bound on the every-phase ratio and the cold S a lower
  bound. At the construction time measured on another host class (X = 427.5
  ms, run 39007026856, illustrative, mixes hosts) the every-phase figures are R
  1.1127 and cold S(B) 0.46994.
- The gap to rT770 is a point estimate from one run with no interval; the
  rT770 step differs across runs (cross-run artifact above).
- The probe law passes its band with a wide interval ([0.9380, 1.1750]); both
  arms read the same value because the rank seeds are shared.
- The design's modelled 1.16 and the index-build ratio of 1.37 were not reached
  (1.1169 and 1.2574): the local model's saving on the shared cloud-agent VM
  did not carry over fully to this host.
- The section 5a band is not computable (the IC arms emit no group-operation
  counts). Not replayed on another host class.

## Files

| File | Role |
| --- | --- |
| `make_indexbuild2_source.py` | the derivation of side B's producer (7 counted, invertible edits on `bc6a31c7...`) |
| `protocol.json`, `make_protocol.py`, `schedule.json` | frozen protocol (sha256 `5cee1a72...`), its builder, frozen run order (`f5ac4c17...`) |
| `restore.py` | restore crypto 770f6a69, derive the three producers, regenerate the closure headers, check every parent, template and local pin |
| `verify_receipt.py`, `test_verify_receipt.py` | the parent's gates, statistics and fail-closed decision rule with this experiment's arm names (30 unit tests) |
| `make_targets.py`, `inputs/cold_targets.json`, `inputs/panel_disjointness.json`, `check_seed_disjoint.py`, `inputs/seed_disjointness.json` | the new panel, seeds, and their disjointness records |
| `profile/` | profiling and exactness patches (scratch copies only), raw records in `raw2/`, summarizer; `inputs/local_profile.json`, `inputs/local_exactness.json` |
| `make_power_prior.py`, `inputs/power_prior.json`, `power_check.py`, `analysis/power.json` | power prior (run 39383739494), simulation and result |
| `arm.py`, `make_schedule.py`, `run_schedule.py`, `check_panel_disjoint.py`, `check_log_table.py`, `make_*_source.py` (other), `online/Cargo.lock`, `lift2/`, `make_closure_base.py`, `verify_closure.py`, `inputs/*` (parent) | the parent's files, byte for byte |
| `figures/profile.*`, `figures/power.*`, `make_figures.py`, `figures/design.*` | profile and power figures (SVG, PDF, PNG); design diagram (TikZ source, PDF, PNG) |
| `run_github_39464544962/` | the archived receipt: `panel/result.json`, `panel/result_table.md`, `verify-stdout.json`, host and allocation records, 282 per-row records |
| `figures/result.*`, `figures/make_result_figure.py` | result figure (TikZ source, PDF, SVG, PNG), drawn from `result.json` |
| `smoke/` | local correctness smoke of the frozen schedule |
| `README.pdf` | this report: `pandoc README.md -o README.pdf --pdf-engine=pdflatex -H report_header.tex --lua-filter report_filter.lua -V geometry:margin=2cm -V fontsize=10pt -V colorlinks=true` |
