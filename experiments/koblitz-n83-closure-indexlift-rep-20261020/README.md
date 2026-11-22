---
title: "n = 83: closure + index lift replication with repeated alternating pairs (Tier 1)"
date: 2026-10-20
---

# n = 83: closure + index lift replication with repeated alternating pairs (Tier 1)

**Status (2026-10-20): result in. Verdict: improvement; every gate passes and
the run is valid.** R = E2E(A) / E2E(B) = **7.4133 [7.1999, 7.6362]** over 30
alternating pairs (10 points x 3 pairs), run 39359922687, Tier 1, instance
scope. The design sections below are the frozen text, unchanged; the
[Result](#result) section was added with the archived receipt.

## Why this run

PR #997 (merged as `e55510070`) made the closure + index-lift M38I producer
the n = 83 a = 1 baseline row: end-to-end cold **7.6558 [7.2192, 8.1103]**
over the index-lift row, run 39335956567,
[`koblitz-n83-closure-indexlift-20261019`](../koblitz-n83-closure-indexlift-20261019/README.md).
That primary had a single cM38I and a single cPI cold observation per point
(20 points), plus separate rank blocks (4 kPI, 16 kM38I). Neither the cold
arms nor the rank arms were *repeated alternating primary pairs*.

The Tier 1 rule in AGENTS.md ("CPU performance isolation gate" / "CPU
performance evidence tiers") requires repeated alternating pairs and a 95%
paired confidence interval whose lower bound exceeds 1 before a result is
called a Tier 1 speedup. docs/ic/BASELINES.md ("The rule this file serves")
asks for a *verified, measured improvement ... under a protocol frozen
before timing*.

The owner's qualification notes for PR #986
(`reviews/pr-986-knownlog-qualification-20261020/QUALIFICATION.md` on
`claude/n83-knownlog`) and for PR #988
(`reviews/pr-988-onlineframe-qualification-20261019/QUALIFICATION.md` on
`claude/n83-onlineframe`) explain this gap: "one ... primary observation per
point" plus separate rank or A/A blocks "are not repeated alternating
primary pairs". The same applies to #997. This experiment replicates #997
under that rule. It does not change or reinterpret the parent's record.

## The producer: unchanged

There is no code change. The parent's derivation chain is copied byte for
byte:

1. the rank-probe producer (`d4394df3...`, PR #980);
2. the index-lift producer (`7df72603...`, PR #981);
3. the closure producer (`8916e034...`);
4. the composition `make_online_source.py`.

The parent's `arm.py`, `check_log_table.py`, `verify_closure.py`,
`make_closure_base.py`, the `online/` and `lift2/` crates and every closure
input are also copied byte for byte.

`restore.py` checks every parent digest on every build, and the workflow
runs it before the build. It checks:

- the parent protocol's own SHA-256 (`ff5b4cbf...`, pinned in `restore.py`);
- the derived producer, which must equal the parent's frozen
  `online_source_sha256`, `1d328b2e461a...`;
- both regenerated closure headers (M38 `42e0de3d...`, M10 `ba99464a...`),
  which must equal the parent's;
- each of the 25 copied files, which must have the digest the parent
  protocol froze for it (`VERBATIM` in `restore.py`).

On the cloud-agent VM, `restore.py --crypto-repo` (crypto 770f6a69, read
only) passed all of these, and `make_online_source.py --check` passed. The
bases, the arm configurations and the per-process gates in `protocol.json`
are the parent's, copied verbatim (`replication_source` on each).

## Frozen design

![Design (from the frozen protocol and schedule; not a result). Source
[figures/design.tex](figures/design.tex), vector
[figures/design.pdf](figures/design.pdf).](figures/design.png)

**Instance.** One GitHub `ubuntu-24.04` runner. Every process is a fresh
process pinned to one CPU (`sched_setaffinity` before exec), with a clean
environment. Every IC arm runs `ic_online_closure_indexlift_r770` with
`KIC_INDEX_CANON=lift`, the full scan self-test, lift_scan target keys,
Feistel, prefetch and the 16-byte compact table over the folded index.

**Panel.** 10 new public points, role `closureindexlift-rep-cold-v1`, seeds
0..9 ([`make_targets.py`](make_targets.py), `inputs/cold_targets.json`). The
panel is disjoint from Q0, B's panel and every role the parent excluded, and
from the parent's own `closureindexlift-cold-v1`. Each of these was
regenerated and compared.

A role-agnostic scan ([`check_panel_disjoint.py`](check_panel_disjoint.py),
[`inputs/panel_disjointness.json`](inputs/panel_disjointness.json)) also
looked for each of the 20 coordinates in three places:

- every file of `origin/main` under `experiments/` and `research/`;
- every file that any of the 858 other `origin/*` branches changes against
  `origin/main` (1,696,544 files);
- every file in the scratch worktrees `n83-blrp`, `n83-cli`, `n83-closure`,
  `n83-indexlift`, `n83-k899`, `n83-knownlog`, `n83-onlineframe` and
  `n83-rotkey` (30,084 files).

It found **0 hits**. As a positive control, the same `git grep` finds a
parent panel x-coordinate in the parent's `cold_targets.json`, `schedule.json`
and archived `runs.jsonl`. No scalar is known for any of the points.

**Rank seeds.** 1201-1230 are new on n = 83. The seeds used before are 7, 29,
101-102, 201-204, 301-309, 401-404, 501-504, 701, 801-816, 901-904 and
1101-1116. Primary pair *j* at point *i* uses seed 1200 + 3*i* + *j*.

**Sides and pairs.**

| side | processes, in order | role |
| --- | --- | --- |
| **A** | kPI (rank stage, 600 attempts on K600, pair's seed, then the point), then cPI (B's verified table, the point) | index-lift row (baseline) |
| **B** | kM38I (rank stage, 16 attempts on M38, same seed, then the point), then cM38I (M38 verified table, the point) | closure + index lift (candidate) |
| **Baa** | kM38Iaa, then cM38Iaa | A/A copy of B |

Each point gets one segment, P*i*. Its four sub-blocks run in an order
shuffled by `random.Random(2026102000 + i)`, and the same generator draws
each block's starting side:

- **primary:** k = **3 pairs** as 6 sides in strict alternation, ABABAB or
  BABABA. Pair *j* is sides 2*j*-1 and 2*j*. Both sides of a pair share the
  point and the rank seed.
- **A/A:** 2 pairs of B and Baa, alternating, with the seeds of primary
  pairs 1 and 2.
- **planted:** 1 pair of kM38I and kM38IX (the parent's `frame_plant`,
  about 1.96x per attempt), alternating, with the seed of primary pair 3.
- **rho:** one rT (tuned rho rT770), seed 1020000 + point seed.

The run starts with O1, which runs Q0 on cPI and cM38I as an exactness check.
In total there are **232 processes**: **30 primary pairs** (30 kPI and 30
kM38I rank blocks, 30 cPI and 30 cM38I cold rows), 20 A/A pairs and 10
planted pairs. The primary starts with A at 7 points and with B at 3.

**How E2E is formed (per side).** E2E(side) = `timing_ms.rank_stage` of the
side's rank process + `cold_in_process_ms` of the side's cold process. The
cold process covers setup, index build and the one-target online phase. The
rank stage covers the rank attempts and the linear algebra. Together that is
the row's end-to-end cold definition. It is the parent's E2E, except that
here the rank and cold terms come from one adjacent pair of processes with
the same point and seed, not from arm-wide means.

**Pairing basis.** The Tier 1 paragraph says to "run both variants on the
same pinned exposed CPU with the same workload and limits" and to "require
repeated alternating pairs". Here a pair is the two variants on the same
point with the same rank seed, adjacent in time on one CPU, in alternating
order. That is also the unit of docs/IC_BENCHMARK_TIERS.md: the same point,
alternating order, one allocation.

**Primary (pre-registered).**

- R = sum over the 30 primary pairs of E2E(A) / sum over the same pairs of
  E2E(B).
- 95% percentile interval from a **two-stage paired bootstrap**: draw the
  10 points with replacement, then each drawn point's 3 pairs with
  replacement. A and B of a pair are always drawn together. 10,000 draws,
  `random.Random(20261020)`.
- **Improvement iff the lower bound > 1.** Regression iff the upper bound
  < 1. Otherwise not separated.
- **Invalid** if any gate is false, unknown or missing, if any control
  fails, or if any scheduled row is missing (time-guard skips included).

**Controls.**

- A/A: E2E(B) / E2E(Baa) and cold cM38I / cM38Iaa over the 20 A/A pairs.
  Both point estimates must lie in [0.97, 1.03].
- Planted timing: kM38IX / kM38I per attempt over the 10 planted pairs, with
  attempts paired. The lower 95% bound must exceed 1.
- Planted exactness: the three closure corruptions (a label, a duplicated
  orbit, a log) must be rejected on both closure bases before timing
  (`check_log_table.py`, verbatim).

**Secondaries (descriptive; none changes the verdict).**

- the geometric mean of the per-pair ratios;
- the paired rank-stage, cold, process-CPU-time and process-wall ratios;
- setup, index build, online and peak RSS;
- the per-point ratios, the ratio by pair position and the ratio by which
  side ran first;
- the probe law of kPI;
- S and the gap to rT.

**Gates.** These are the parent's, plus the Tier 1 records.

1. Before timing: B's table re-verified in the pinned oracle. Both closure
   headers regenerated to their frozen digests and passed by
   `verify_closure.py`, with the planted corruptions rejected. The closure
   tables checked, and the closure logs equal to B's.
2. Every IC process (`arm.py`): `KIC_INDEX_CANON=lift`, 0 roots checked
   against the selected canonicalizer, the full self-test, and the base's
   frozen index digests and **layout digests**. For K600 these are
   index-lift's `d8cfe443...` / `5f53764e...`.
3. Per point: one scalar across every IC process (both bases, cold and rank)
   and rT, **replayed in the oracle**. One relation and one probe count per
   point and base. One index and layout digest set per base, equal to the
   frozen one.
4. **Q0:** cPI must give B's archived identity (1,987,852 probes), and cM38I
   the closure protocol's frozen identity.
5. Rank processes: full rank and 0 failures. The written table must be
   **equal to the frozen verified table**. Every kM38I, kM38Iaa and kM38IX
   process with the same seed must have identical relation digests, probe
   vectors, root calls and counters.
6. **Probe-law band:** kM38I's pooled probes per relation over its 30
   distinct seeds (480 attempts), divided by r / (166 E), must lie in
   [0.80, 1.20].
7. Tier 1 records:
   - every process's `Cpus_allowed_list` (read from `/proc` while it ran)
     is the execution CPU;
   - the CPU record (`scripts/host_cpu_record.py` from main: model,
     microcode, flags, caches, topology, kernel) is the same at the start
     and the end.

   Per run the receipt also holds:
   - process CPU time (user and system) and wall time;
   - producer peak RSS;
   - cgroup `cpu.stat` throttling, memory events, memory current and peak;
   - steal, IRQ and softirq on the execution CPU, and interrupts;
   - CPU pressure;
   - `/proc/schedstat` and `/proc/stat` scheduling counters;
   - voluntary and involuntary switches, and minor and major faults;
   - every raw failure (rows are never re-run, and failed rows are kept).

   The host probe and the allocation record identify the host, kernel and
   placement.
8. **Receipt integrity, fail closed** (main's hardened verifier plus
   schedule identity):
   - every raw record decodes, and its SHA-256 equals the wrapper's
     `raw_result_sha256`;
   - its arm, kind, panel, point and seed equal the schedule's;
   - each row's serial, segment, command line and stdout file are the
     schedule's, and rows ran in schedule order;
   - `runner_start.json` names this protocol's, this schedule's, `arm.py`'s
     and `run_schedule.py`'s digests and no smoke subset;
   - the binaries were unchanged at the end;
   - every required gate must be present and `true`.

## Power and runtime

[`power_check.py`](power_check.py) simulates receipts of exactly this design
and applies the frozen statistic and bootstrap
([`analysis/power.json`](analysis/power.json); 400 simulations per cell, 500
draws each). Its prior is the parent's archived run 39335956567
([`make_power_prior.py`](make_power_prior.py), `inputs/power_prior.json`,
with every raw record's digest checked).

- kPI is resampled from its 4 archived blocks.
- kM38I is drawn from the 256 archived attempts.
- The cold times come from the 20 archived points.
- Each process carries a noise factor drawn from the archived A/A ratios.
  This overstates the per-process noise by about sqrt(2), so the power
  figures are conservative.

![Design-stage power and runtime (not a result), from `analysis/power.json`
by [`make_figures.py`](make_figures.py) ([svg](figures/power.svg),
[pdf](figures/power.pdf)).](figures/power.png)

| true end-to-end effect | P(lower bound > 1) |
| --- | ---: |
| 1.00 (no gain; type I) | 0.018 |
| 1.10 | 0.51 |
| 1.25 | 1.00 |
| **1.50 (minimal effect of interest)** | **1.00** |
| 2.00 | 1.00 |
| 4.00 | 1.00 |
| **modelled: the parent's costs, about 7.66** | **1.00** (median R 7.68, median interval hi/lo 1.06) |

The A/A point estimates fall inside [0.97, 1.03] in 100% of simulations. The
probe-law gate passes at the archived law in 100% of simulations and rejects
a law 1.5x worse in 100% of them (480 attempts). The planted lower bound
exceeds 1 in 100% of simulations.

**Runtime.** The estimate uses the parent's mean process walls: kPI 162.6 s,
kM38I 22.9 s, cold 18.9 s, kM38IX 28.4 s and rT 3.1 s. That gives a P
segment of about 891 s and a schedule of about **149 min**. Adding the
parent's fixed cost before the schedule (11.7 min: restore, build, tests,
table checks) and after it (about 2 min) gives a job of about **163 min
(2.7 h)**, or about **243 min** on a host 1.5x slower.

The time guard is at 285 min of job time and the job limit is 300 min, so
**one job fits**, and the run is not split. The guard skips a segment if the
elapsed time plus the larger of 1,300 s and 1.1x the longest P segment so far
would pass 285 min. Any skip makes the run invalid. That outcome is recorded,
never patched.

## Exactness checks done before freezing (cloud-agent VM, correctness only)

- `restore.py --crypto-repo /home/user/crypto` passed. It checked the r770
  snapshot against the reconcile protocol's digests, the derivation chain,
  both closure headers, the parent protocol and the 25 copied files.
- `check_log_table.py` passed for K600, M38 and M10, and the planted
  corruptions were rejected ([`smoke/log-table-check.json`](smoke/log-table-check.json)).
- 23 verifier unit tests passed (`test_verify_receipt.py`). They cover:
  - a missing, unknown or extra gate, each of which is invalid;
  - raw tampering and identity mismatch;
  - command and runner identity;
  - a paired bootstrap that keeps the pairs together;
  - strict alternation and seed sharing in the frozen schedule.
- A smoke of O1 and the first process of every arm in P5 gave 10 of 10
  valid rows ([`smoke/README.md`](smoke/README.md),
  [`smoke/correctness_smoke.json`](smoke/correctness_smoke.json)):
  - Q0 equal to the archived and frozen identities;
  - one scalar per point, replayed;
  - the index and layout digests equal to the frozen ones on K600 and M38;
  - the rank tables equal to the frozen tables;
  - kM38I and kM38Iaa identical on seed 1213;
  - placement and CPU identity recorded and passing.

  The probe-law band is not evaluable on 2 blocks. The protocol was frozen
  before the smoke and not changed after it.

## Trigger

The run is the workflow `n83-closure-indexlift-rep.yml`. A
`workflow_dispatch` call (ref `claude/n83-closure-indexlift-rep`) returned
**403** ("Resource not accessible by integration"). The workflow therefore
also has a push trigger. It is restricted to this branch and to the
experiment's non-receipt paths, as in `n83-closure-indexlift.yml`, and the
push that added it started the run at the frozen protocol and schedule. The
run URL is recorded in the result once the receipt is archived.

## Result

Run [39359922687](https://github.com/aburan28/cryptanalysis/actions/runs/39359922687)
(workflow `n83-closure-indexlift-rep.yml`, push trigger, frozen commit
`5634fc23`, attempt 1, conclusion success) on one GitHub-hosted `ubuntu-24.04`
runner (`runnervmxehtw`, image 20261018.339.1, 4 vCPUs, AMD EPYC 9V74,
kernel 7.0.0-1017-azure, execution CPU 0). The job ran 02:37 to 05:28 UTC
(2 h 51 min; the runner's schedule took 153 min, against the 285-minute
guard). The receipt is archived in
[`run_github_39359922687/`](run_github_39359922687/).

**All gates pass; the run is valid.** The runner executed all 232 scheduled
rows (`schedule-exit.txt`: 0): 232 valid, 0 invalid, **0 skipped by the time
guard**, guard not tripped, all 232 return codes 0, all 20 A/A pairs, 10
planted pairs and 30 primary pairs complete, 11 units seen.

- Before timing: K600 and M38 tables re-verified by the pinned pure-Python
  oracle (`log-table-check.json`), planted closure corruptions rejected.
- One scalar per point across every IC process and rT, replayed in the
  oracle; one relation and one probe count per point and base.
- One index and layout digest set per base, equal to the frozen one; Q0 equal
  to the archived identities; rank tables equal to the frozen verified
  tables; per rank seed, identical relation digests, probe vectors, root
  calls and counters across kM38I, kM38Iaa and kM38IX (0 rows without gain).
- Probe law gate: kM38I 0.9883 [0.8754, 1.1164] over 480 attempts (30
  blocks), inside the frozen band [0.80, 1.20] (pass).
- Runner identity equals the frozen files, binaries unchanged
  (`binaries.sha256`), CPU record unchanged start to end, every process placed
  on CPU 0 (`Cpus_allowed_list` 0), `receipt_matches_schedule`, no contention
  flags, no problems.

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

Improvement iff the 95% lower bound of R = sum E2E(A) / sum E2E(B) over the 30
alternating pairs exceeds 1, with a two-stage paired bootstrap (points, then
pairs within points; 10,000 draws), and both A/A ratios lie in [0.97, 1.03]
and the planted lower bound exceeds 1. A = kPI + cPI (the baseline), B = kM38I
+ cM38I (closure + index lift).

| Statistic | Estimate [95%] | Reading |
| --- | --- | --- |
| **R = E2E(A) / E2E(B)** (30 pairs, 10 points) | **7.4133 [7.1999, 7.6362]** | **improvement** (lower bound above 1) |
| geometric mean of the 30 pair ratios | 7.4164 [7.2100, 7.6469] | reported |
| A/A E2E B / Baa (20 pairs) | 0.9991 [0.9942, 1.0049] | pass (inside [0.97, 1.03]) |
| A/A cold cM38I / cM38Iaa (20 pairs) | 0.9979 [0.9933, 1.0022] | pass (inside [0.97, 1.03]) |
| planted rank per attempt kM38IX / kM38I (160 attempts) | 1.9418 [1.9072, 1.9747] | pass (lower bound above 1) |
| planted exactness corruptions | rejected before timing | pass |

Mean E2E per side: A 161,165.4 ms (143,551.4 rank stage + 17,614.0 cold),
B 21,740.1 ms (3,744.8 rank stage + 17,995.3 cold). The power check expected
about 7.66 (an estimate, not an input); the measured 7.41 is close. The
parent run (PR #997, run 39335956567) measured 7.6558 [7.2192, 8.1103] with
unpaired cold arms; this paired result is 3.2% lower, its interval lies just
below the parent's estimate and the two intervals overlap.

### Secondaries (none changes the verdict)

**Per-phase breakdown** (means over the 30 pairs; ratio is A over B, below 1 =
B slower):

| Phase | A (kPI + cPI) | B (kM38I + cM38I) | A / B [95%] |
| --- | ---: | ---: | :--- |
| rank stage (ms) | 143,551.4 | 3,744.8 | 38.3338 [34.9034, 42.5698] |
| cold without rank (ms) | 17,614.0 | 17,995.3 | 0.9788 [0.9564, 1.0023] |
| setup (ms) | 17,261.7 | 17,646.0 | 0.9782 [0.9737, 0.9829] |
| index build (ms) | 15,208.5 | 15,630.4 | 0.9730 [0.9683, 0.9778] |
| online (ms) | 352.38 | 349.30 | 1.0088 [0.2789, 3.2201] |
| process CPU time (ms) | 182,200.9 | 43,182.7 | 4.2193 [4.1257, 4.3167] |
| process wall (ms) | 182,222.5 | 43,188.9 | 4.2192 [4.1251, 4.3185] |
| peak RSS (bytes) | 1,875,243,554 | 1,895,542,784 | 0.9893 [0.9893, 0.9893] |

The cold path is not improved by the closure: setup is 2.2% and the index
build 2.7% slower in B, the same direction as the parent. The online phase
shows no difference here (1.0088, interval [0.28, 3.22]); the parent's 1.64x
online gain is not reproduced at this resolution. The process CPU ratio
(4.22) is smaller than the E2E ratio (7.41): E2E counts the rank stage and the
cold time of the side's two processes, while the process CPU and wall columns
are measured over every process of the side, and their composition is not
broken down here.

**Rank-stage share of E2E cold:** A 89.1% (143,551.4 / 161,165.4), B 17.2%
(3,744.8 / 21,740.1). Rank-stage ns per probe: kPI 138.53, kM38I 140.08,
kM38Iaa 139.90, kM38IX 274.55; mean per attempt 239.07, 235.36, 231.55 and
475.10 ms. The per-probe code is the same across arms (B is 1.1% slower per
probe); the planted arm costs 1.96x per attempt (1.94x paired).

**Probe law** (mean probes per relation over the law value):

| Arm | Estimate [95%] | Attempts | Role |
| --- | --- | ---: | --- |
| kM38I | 0.9883 [0.8754, 1.1164] | 480 (30 blocks) | gate, band [0.80, 1.20]: pass |
| kPI | 0.9988 [0.9806, 1.0182] | 18,000 (30 blocks) | reported |

**S** (cost over this run's measured rT770 step, 246.64 ns, per sqrt(r); one
unit is 22,833 ms): end-to-end cold S(A) = 7.0587, S(B) = 0.9522
(delta S = -6.1066); online S(A) = 0.015434, S(B) = 0.015299. The tuned
rho's own S: cold 0.11289 (mean rT770 cold 2,577.6 ms, online 2,368.1 ms).

**Gap to tuned rho rT770** (IC time over rT time, point estimates from
`result.json`; no interval is computed for the gaps, distance remaining, not a
gate):

| Arm | End-to-end cold | Online |
| --- | ---: | ---: |
| A = kPI + cPI (baseline) | 62.53 | 0.1488 (352.38 / 2,368.15 ms) |
| B = kM38I + cM38I (candidate) | 8.434 | 0.1475 (349.30 / 2,368.15 ms) |

**Per-pair ratio spread** (30 pairs): minimum 6.758, median 7.337, mean
7.429, maximum 8.465, standard deviation 0.4526, quartile positions (8th and
23rd of 30 sorted) 7.067 and 7.741. Per point (10 points): 7.007 to 7.881.
By pair position within the point: 7.311 (first), 7.541 (second), 7.388
(third). By order: A first (21 pairs) 7.5546, B first (9 pairs) 7.0985, a 6%
order effect that the alternation balances only approximately (the start was
drawn per point).

### Host and isolation records

From `host-cpu.json`, `allocation.json`, `panel/runner_start.json`,
`panel/runner_end.json` and the 232 per-row records in `panel/runs.jsonl`:

| Record | Observed |
| --- | --- |
| provider, instance | GitHub Actions, run 39359922687 attempt 1, runner `runnervmxehtw` ("GitHub Actions 1000361834"), advertised 4 vCPU / 16 GB, image 20261018.339.1; allocation receipt `allocation.json` |
| CPU | AMD EPYC 9V74 80-Core (family 25, model 17, stepping 1), AVX-512, 4 vCPUs = 2 cores x 2 threads, 1 socket, 1 NUMA node; Microsoft hypervisor |
| microcode | `0xffffffff` (not readable inside the guest), uniform across CPUs, same at start and end |
| frequency | nominal `cpu_mhz` 3698.9 at start, 3692.8 at end; `scaling_cur_freq` not exposed (null), not fixed |
| placement | every process on CPU 0 (`Cpus_allowed_list` 0), 232/232 |
| cgroup | `/system.slice/hosted-compute-agent.service`, `cpu.max` quota none, `isolcpus`/`nohz_full` empty |
| steal | 0 ticks in every row (`/proc/stat` and per-CPU), total 0 |
| throttling | `nr_throttled` 0 and `throttled_usec` 0 in every row |
| memory failures | `memory.events` max and oom_kill deltas 0; 0 major faults |
| scheduling | run-queue wait 1.846 s against 9,070.95 s on CPU (0.020%; worst process 0.097%); 189,733 timeslices; 94,439 involuntary switches in total (at most 1,847 in one process), 2,524 voluntary |
| CPU pressure | `cpu.pressure` some-delta per row 418 to 20,503 us |
| contention flags | none |
| transparent hugepages | `enabled` madvise, `defrag` madvise |

### AGENTS.md Tier 1 assessment

AGENTS.md Tier 1 (cloud instance) requires: a frozen provider allocation
receipt and instance ID; both variants on the same pinned exposed CPU with the
same workload and limits; code and workload hashes, paired order, raw
failures, correctness, process CPU time, memory, cgroup throttling and memory
failures, steal time and scheduling counters; repeated alternating pairs and a
95% paired interval whose lower bound exceeds 1.

**Met:** the allocation record and run ID (`allocation.json`); one pinned CPU
for all 232 processes with the same workload, binaries and no CPU quota; code
and workload hashes (protocol, schedule, arm wrapper, runner, binaries,
log tables); paired alternating order from the frozen schedule; raw failures
(0) and correctness (every gate above); process CPU time, peak RSS, cgroup
throttling (0), memory events (0), steal (0) and `/proc/schedstat` counters per
row; 30 alternating pairs and a lower bound of 7.1999.

**Gaps (named, none changes the verdict, all limit the claim):**

1. No host-wide exclusivity. CPU affinity records placement inside the VM; the
   cgroup is the runner agent's service and the other three vCPUs, the agent
   and the hypervisor's other tenants are not controlled. Steal of 0 in the
   guest does not prove an unshared physical core.
2. CPU 0 shares its core and its L1/L2 with vCPU 1 (cache `shared_cpu_list`
   0-1); the sibling thread was not offlined or shown idle.
3. Microcode is unreadable (`0xffffffff`), so the CPU identity rests on the
   model name, flags and the unchanged record, not on a microcode revision.
4. The frequency is neither fixed nor observable (`scaling_cur_freq` not
   exposed); only nominal `cpu_mhz` is recorded.
5. No IRQ routing control, no `isolcpus`/`nohz_full`, no NUMA memory policy
   beyond the single node.
6. One instance only (instance scope): another runner may differ; this run
   differs from the parent's runner (`runnervm8k3b6`) in host name, kernel and
   image.

The result is a **Tier 1, instance-scoped** paired wall-time comparison, not
host-isolated (Tier 2).

### Limits of this result

- Tier 1, instance scope: one runner, 10 cold points, 3 alternating pairs per
  point, one fresh process per arm per pair. The interval covers points and
  pairs; it does not cover another host class.
- Wall time on one host class. The saving is the number of rank attempts (16
  against 600), not the per-probe cost (140.08 ns against 138.53 ns).
- **Factor-base construction is charged to no arm** (the n = 83 convention),
  so 7.4133 is an upper bound on the every-phase ratio.
- The kM38I probe law is a pooled estimate with a wide interval ([0.8754,
  1.1164]); it passes its band but is not tight.
- Only 10 points: the interval is a point-level resample, so the point
  variation (7.007 to 7.881) is included; the rank seeds and instance are not
  independently varied beyond that.

## Not included

- The M10 secondary is not timed. Its base is still verified before timing,
  because `check_log_table.py` is verbatim.
- Factor-base construction is charged to no arm, as in every n = 83 row.

## Files

| File | Role |
| --- | --- |
| `protocol.json`, `make_protocol.py`, `schedule.json`, `make_schedule.py` | frozen protocol, its builder, frozen run order |
| `restore.py` | restore crypto 770f6a69, derive the producer, regenerate the closure headers, check every parent digest and every local pin |
| `make_online_source.py`, `make_*_source.py`, `online/`, `lift2/`, `make_closure_base.py`, `verify_closure.py`, `arm.py`, `check_log_table.py`, `inputs/factor_logs_*`, `inputs/parent_closure_protocol.json`, `inputs/local_*.json`, `inputs/archived_identities.json` | the parent's files, byte for byte |
| `run_schedule.py` | the parent's runner plus the CPU record, placement and scheduling counters |
| `make_targets.py`, `inputs/cold_targets.json`, `check_panel_disjoint.py`, `inputs/panel_disjointness.json` | the new panel and its disjointness record |
| `make_power_prior.py`, `inputs/power_prior.json`, `power_check.py`, `analysis/power.json` | power prior (run 39335956567), simulation, result |
| `verify_receipt.py`, `test_verify_receipt.py` | gates, statistics, fail-closed decision rule; its tests |
| `run_github_39359922687/` | the archived receipt: `panel/result.json`, `panel/result_table.md`, `verify-stdout.json`, host and allocation records, 232 per-row records |
| `figures/result.*`, `figures/make_result_figure.py` | result figure (TikZ source, PDF, SVG, PNG), drawn from `result.json` |
| `figures/design.*`, `figures/power.*`, `make_figures.py` | design diagram (TikZ source, PDF, PNG); power and runtime figure (SVG, PDF, PNG) |
| `smoke/` | local correctness smoke |
| `README.pdf` | this report: `pandoc README.md -o README.pdf --pdf-engine=pdflatex -H report_header.tex --lua-filter report_filter.lua -V geometry:margin=2cm -V fontsize=10pt -V colorlinks=true` |
