---
title: "n = 19 tau6 native per-shift solve, protocol v3 (run 39387473809: improvement)"
date: 2026-10-20
---

# n = 19 tau6 native per-shift solve, protocol v3 (run 39387473809: improvement)

**Status (2026-10-20): run, valid, improvement.** The first run,
39384735073, was invalid: a workflow defect failed its first job before any
experiment code ran. Commit `4ef371544` fixed the defect and the workflow was
launched again as [run 39387473809](https://github.com/aburan28/cryptanalysis/actions/runs/39387473809). All 24 gates passed, both
controls passed and the time guard skipped nothing: cold CPU B / N is
141.02 [136.75, 144.95]. See [Result](#result-run-39387473809); the first run's
record is kept under [History](#history-the-first-run-39384735073-invalid). Protocol v3 was frozen before any timing. v3 replaces
[v2](../volcano-n19-native-tau6-v2-20261019/README.md). v2's Tier 1 run,
[39376405326](https://github.com/aburan28/cryptanalysis/actions/runs/39376405326),
was invalid: S0 on 2,682 systems, O1 and the field check passed, but every
timed IC row (B, N, Naa and NX on all 16 points) crashed after its interval
in `arm.sage`'s `relation_digests`. v1's and v2's protocols and archives are
unchanged. The workflow is
[`n19-native-tau6-v3.yml`](../../.github/workflows/n19-native-tau6-v3.yml).

## Root cause of v2's crash

**Confirmed in Sage** by run 39387473809's smoke job (see
[the result](#root-cause-of-v2s-crash-confirmed)). See [`diagnosis/README.md`](diagnosis/README.md) for the full account. In
short, the Sage preparser turns the literal `0` in
`row.get(col, 0)` into a Sage `Integer`. Every value of the relation-rows
digest was therefore an `Integer`, and `json.dumps` refused it:
`TypeError: Object of type Integer is not JSON serializable`.

- The run's traceback places the failure at `h(rows)`, after the `ordered`
  and `canonical` digests succeeded. This holds in all 64 IC logs.
- A local emulation on v2 point p00
  ([`diagnosis/emulate_preparser.py`](diagnosis/emulate_preparser.py)) runs
  v2's own function. In plain Python it succeeds. With integer literals made
  `Integer`, it fails exactly as on the runner.
- The smoke job reran v2's `arm.sage` on rows p00-N and p00-B in the pinned
  image ([`diagnosis/digest_repro.sage`](diagnosis/digest_repro.sage)): both
  failed with the same `TypeError` (run 39387473809, below).
- v2's local checks were pure Python, and no Sage check before the timed
  rows ever wrote an IC row.

![Root cause. Source: [make_figures.py](make_figures.py); vector:
[figures/crash_diagnosis.svg](figures/crash_diagnosis.svg).](figures/crash_diagnosis.png)

## What v3 changes

| | v2 | v3 |
| --- | --- | --- |
| relation digests | in `arm.sage` (preparsed) | [`relation_digest.py`](relation_digest.py), plain Python, `operator.index` on every input; same definitions |
| row serialization | `json.dump(..., default=jplain)`, falls back to `str()` | `relation_digest.plain`, strict: Sage Integer → int, reals → float, anything else raises |
| raw record | row file only | row bytes also on stdout as `raw_b64` + SHA-256; the verifier checks them against the row file and the schedule |
| relations | digests only | each IC row and O1 instance records its raw relations, and the verifier recomputes every digest |
| Sage smoke gate | none (the local smoke ran pure Python) | **job `sage-smoke`, untimed**: S0, O1, and v2 points p00 and p01 through B, N, Naa, NX and rho in the pinned image; 20 gates; the timed job `needs` it and uses its library |
| O1 | counts and logs | also the relation digests of all ten archived ECDLPs (the crashing path, before any timed row), and the archived λ |
| S0 | 7 v1 systems + 300 + 2,375 multi = 2,682 | + v2's 300 re-derived from v2's seed + 300 new (v3 seed) = 2,982; the detail digest is recomputed |
| design | 1 process per arm per point, 16 points | **20 points × (3 alternating B/N pairs + 3 N/Naa pairs + 1 NX/N pair + 1 rho)**, seeded ABAB/BABA starts, shuffled block order |
| interval | one-stage bootstrap over points (numpy) | **two-stage paired bootstrap** (points, then pairs), 10,000 draws, `random.Random(2026102003)` |
| isolation records | affinity only | per run: `Cpus_allowed_list`, the arm's affinity, `/proc/schedstat`, `/proc/stat`, `getrusage`, `isolated_bench` counters and noise, library digest before and after; `host_cpu_record` at start and end |
| verifier | gate names free-form | fixed gate set, equal to `protocol.json` `gates_required`; a missing, unknown or non-boolean gate makes the verdict invalid; 12 planted-corruption tests |
| trigger | dispatch (main); path-limited push (branch) | dispatch, and push limited to branch `claude/n19-native-v3` and this experiment's frozen paths (owner-approved pattern of v2) |

The solve (`native/src/lib.rs`), the binding (`native_binding.py`), the
question, the arms, the intervals (setup, online, cold) and the field check
are v2's, byte for byte where they are code.

## Frozen design

![Frozen v3 design and run order (not a result). Source: [make_figures.py](make_figures.py);
vector: [figures/design.svg](figures/design.svg).](figures/design.png)

- **Primary.** R = Σ cold CPU(B) / Σ cold CPU(N) over the 60 primary pairs,
  where cold = setup + online, `time.process_time()` inside each fresh
  pinned Sage process. The interval is a two-stage paired bootstrap at 95%.
  Improvement iff the lower bound is above 1, regression iff the upper bound
  is below 1, otherwise not separated.
- **Controls.**
  - A/A: N/Naa over 60 pairs, estimate inside [0.95, 1.05].
  - Planted: NX/N over 20 pairs, lower bound above 1. NX redoes the Sage
    solve on every shift system and compares it with the native one.
- **Gates.** There are 24 (20 in smoke):
  - schedule identity, raw digests, recomputed relation digests and one
    library digest;
  - pinning, CPU identity and the Tier 1 counters;
  - S0, O1 and the field check in every native process;
  - identical counts, logs, rows, canonical and ordered decompositions
    across every IC process of a point;
  - NX comparing every call, the archived generator, rho 64/64 and the warm
    batch;
  - the smoke gate and complete pairs.

  Every gate is listed in `protocol.json` `gates`.
- **Panel.** 20 new scalars (`inputs/panel.json`, role
  `n19-native-heldout-v3`, seed `volcano-n19-native-tau6-v3-20261020:panel`).
  None is equal to, the negative of, or a Frobenius image of an archived,
  v1 or v2 panel scalar. The order, S0, power and bootstrap seeds are all
  new.
- **Power** ([`analysis/power.json`](analysis/power.json)).
  - Model: per-process log-normal noise σ = 0.10 or 0.20, and per-point
    costs from v2's B processes or from the archived rows.
  - Power at a true ratio of 1.20 is at least 0.98. At 1.10 it is 0.995
    (σ = 0.10) or 0.52 (σ = 0.20).
  - The rejection rate with no effect is at most 0.015.
  - The A/A window fails with no effect in 1–2% of panels at σ = 0.10 and
    18–23% at σ = 0.20. v2's N launcher walls varied from 1.8 to 2.2 s,
    which points to the lower σ.
  - The expected effect is far larger: in v2's run, B processes took 57–99 s
    and N processes 1.8–2.2 s, Sage start-up included.
- **Runtime and time guard.**
  - The smoke job takes about 10 min. The timed job takes about 2 h, and
    about 2.6 h if every B process takes 100 s.
  - Before each segment, the guard skips it if the elapsed time plus
    max(its upper estimate, 1.1 × the longest point segment so far)
    exceeds 175 min. A skip makes the verdict invalid.
  - The job timeout is 200 min.
- **Tier.** Tier 1 as AGENTS.md defines it. The run uses one fresh
  GitHub-hosted ubuntu-24.04 runner and one pinned exposed CPU, and the
  image is `sagemath/sagemath:10.10@sha256:310dfe23…`. It is CPU-only, has
  one host class and is not replayed. A container affinity mask records
  placement, not host-wide exclusivity.

![Power of the frozen primary (simulated). Vector: [figures/power.svg](figures/power.svg).](figures/power.png)

## Local checks before freezing (cloud-agent VM, no Sage; not timing evidence)

- **`cargo test --release --locked`.** 7 of 7 pass (rustc 1.97.0 locally;
  the runner pins 1.99.0).
- **[`smoke/local_v3.py`](smoke/local_v3.py)** runs a pure-Python tauDlp with
  the v3 binding and digests ([`smoke/local_v3.json`](smoke/local_v3.json)).
  - The ten archived scalars give counts and logs equal to run 38520305068.
  - All logs verify on the two smoke points and the 20 v3 points.
  - On the 20 v3 points, gb_calls average 5,446 (range 3,673 to 7,095); v2's
    panel averaged 5,653.
- **[`diagnosis/emulate_preparser.py`](diagnosis/emulate_preparser.py)**
  reproduces v2's error and shows that v3's digests are equal and type-safe.
- **`tests/test_verify_receipt.py`.** 12 of 12 pass on synthetic receipts:
  - a clean receipt passes;
  - each of these fails closed: a tampered row file, a digest that does not
    recompute, a schedule mismatch, a command mismatch, a raw record of
    another point, an unpinned process, an unknown, missing or non-boolean
    gate, a protocol gate list that differs, a failed A/A, counts that
    differ between arms, a time-guard skip, and a missing smoke receipt.
- **[`smoke/dryrun_fake_sage.py`](smoke/dryrun_fake_sage.py)** checks the
  mechanics of the runner and verifier, with a stand-in `sage` that emits
  synthetic records ([`smoke/dryrun_fake_sage.json`](smoke/dryrun_fake_sage.json)).
  - The real `run_schedule.py` launches every smoke run pinned and records
    the isolation fields. The real verifier passes 19 of 20 smoke gates.
  - The exception is `tier1_counters_recorded`: this VM has no
    `/proc/schedstat`. GitHub runners have it (n = 83 run 39359922687 records
    it).

## Launch

The workflow is
[`.github/workflows/n19-native-tau6-v3.yml`](../../.github/workflows/n19-native-tau6-v3.yml).

- **Dispatch was tried first and refused.** `gh workflow run` returned
  404, because the workflow is not on the default branch, and the GitHub
  integration returned 403 ("Resource not accessible by integration").
- **The push trigger launched it.** It is path-limited to this branch and
  this experiment's non-report paths, the owner-approved pattern from v2.
  The push of commit `92d85f14` started
  [run 39384735073](https://github.com/aburan28/cryptanalysis/actions/runs/39384735073):
  first job `sage-smoke`, then job `timed`, which needs it.
- **First run invalid, then fixed.** Run 39384735073 failed in step 3 of
  `sage-smoke` (a `KeyError`, below). Commit `4ef371544` added the missing
  `export` of `N19_RD` in the step that sets it, in both jobs. It changed one
  file, `.github/workflows/n19-native-tau6-v3.yml` (2 lines added), and **no
  frozen file**: `protocol.json`, `schedule.json`, `inputs/`, the sources
  and `diagnosis/digest_repro.sage` are the ones the receipt's
  `frozen.sha256` lists, and the gate `runner_identity_matches_frozen_files`
  passed. Its push started [run 39387473809](https://github.com/aburan28/cryptanalysis/actions/runs/39387473809) on
  `4ef371544`.
- This README, the figures and the smoke and diagnosis files do not
  trigger a run.

## Result (run 39387473809)

**Verdict: improvement.** Cold CPU of the Sage Groebner solve (B) over the
native solve (N) is **R = 141.02 [136.75, 144.95]** over 60 alternating
pairs on 20 points (two-stage paired bootstrap, 10,000 draws, seed
2026102003). The lower bound is far above 1, both controls passed, all 24
gates passed and the time guard skipped no segment.

![Result. Source: [figures/make_result_figure.py](figures/make_result_figure.py);
vector: [figures/result.svg](figures/result.svg).](figures/result.png)

- **What ran.** Run
  [39387473809](https://github.com/aburan28/cryptanalysis/actions/runs/39387473809)
  on `4ef371544`, a push-triggered re-launch. Job `sage-smoke` queued about
  26 min, ran 08:01 to 08:08 UTC and passed all 20 smoke gates. Job `timed`
  ran 08:24 to 09:43 UTC (the timed step took 76 min, inside the 2 to 2.6 h
  estimate) and its 302 rows are all valid.
- **Archive.** [`run_github_39387473809/`](run_github_39387473809/) holds both
  artifacts, unpacked: `smoke/` (the smoke receipt, `lib/libtau6native.so`,
  `diagnosis/`) and `timed/` (`panel/` with `result.json`, `result_table.md`,
  302 rows and logs, `allocation.json`, `host-probe.json`, the workflow's
  verifier output). The first run's archive is unchanged.
- **Receipt re-verified.** `verify_receipt.py --part timed` was run on a
  copy of both artifacts, with the copy's `result.json` and
  `result_table.md` deleted first. It regenerated both files, and both are
  **byte-for-byte identical** to the CI's (`result.json` sha256
  `b4abac3037b3b6a4...`). The smoke part also re-verifies on a copy.
- **Hosts.** The timed job ran on runner `GitHub Actions 1000365175`
  (AMD EPYC 9V74, Hyper-V, kernel 7.0.0-1017-azure, 4 vCPU). The smoke job
  ran on another host (EPYC 9V45); its times are never used and the library
  it built is the one the timed job ran (one sha256, `d92534fa...`, before
  and after every process).

### Frozen rule, as applied

| item | outcome |
| --- | --- |
| primary R = sum cold CPU(B) / sum cold CPU(N), 60 pairs, 95% two-stage paired bootstrap | **141.02 [136.75, 144.95]**; improvement iff the lower bound exceeds 1: **yes** |
| geometric mean of the pair ratios (secondary) | 140.05 [135.85, 144.13] |
| A/A N / Naa in [0.95, 1.05] | **1.0003 [0.9964, 1.0035]** over 60 pairs: inside |
| planted NX / N lower bound above 1 | **140.8 [136.6, 144.6]** over 20 pairs: 136.6 above 1 |
| gates | **24 of 24 true**; gate-name audit: none unknown, missing, non-true or differing from `protocol.json` |
| smoke gate | 20 of 20 true, `smoke_exit=0` |
| time guard | 0 segments skipped, guard not tripped |
| verdict | **improvement** |

### Controls

- **A/A** (N against an identical Naa arm, 60 pairs): 1.0003 [0.9964,
  1.0035]. The launcher wall ratio is 1.0047 [1.0004, 1.0113]. The arms and
  the harness add no bias at this resolution.
- **Planted** (NX redoes the Sage solve on every shift system and compares
  it with the native one, 20 pairs): NX / N = 140.8 [136.6, 144.6]. The
  detector sees a Sage-sized cost inside the N arm, and NX's cold CPU
  (48.22 s) equals B's (48.22 s).
- **Correctness.** S0 held on 2,982 systems (all set- and order-equal to the
  brute force, 2,375 of them multi-solution, 607 third-checked), O1 passed,
  the field check ran in every native process, and every B, N, Naa and NX
  process of a point has the same counts, logs and relation digests (the
  digests were recomputed by the verifier). rho 64/64.

### Secondaries

| quantity | estimate [95%, two-stage paired bootstrap] |
| --- | --- |
| online CPU B / N | 206.7 [203.3, 209.8] |
| setup CPU B / N | 1.29 [1.279, 1.297] |
| cold wall B / N | 141.2 [137.1, 145.2] |
| Groebner CPU B / N (`gb_cpu`) | 911.3 [908.9, 913.7] |
| launcher wall B / N (includes Sage start-up) | 12.96 [12.39, 13.52] |
| child CPU B / N | 12.81 [12.20, 13.42] |
| N cold gap to the matched rho (geometric mean of pairs) | 117.9 [113.4, 122.6] |

- **Online `S`, setup, and `S` per arm** (the unit is this run's rho group
  operation, 3.0095e-5 s of CPU; `S` = CPU per ECDLP in that unit per
  sqrt(r)):

  | arm | cold | online | setup |
  | --- | ---: | ---: | ---: |
  | B (Sage Groebner) | 4,429.3 | 4,416.4 | 12.96 |
  | N (native) | 31.42 | 21.40 | 10.02 |
  | Naa | 31.42 | 21.43 | 9.99 |
  | NX (planted) | 4,428.8 | 4,415.7 | 13.05 |
  | matched rho | 0.2661 | not separable | none |

  In seconds of CPU per process (means): B cold 48.22 (setup 0.141, online
  48.08), N cold 0.3421 (setup 0.1091, online 0.2330).
- **Gap to the matched rho.** N's cold gap is 117.9 [113.4, 122.6] (60
  pairs). The ratio of the means is 31.42 / 0.2661 = 118.1. B's, from the
  same run's means, is 16,647 (no interval); the first ledger row read
  1.94e4 in another run, host and unit. The gap is not closed: the rho is a
  Python/Sage walk at 0.997 of the floor in steps, not tuned for wall time.
  An online gap is not computed: online `S` 21.40 against the rho's 0.2661 is
  about 80 as a ratio of point estimates, with no interval.
- **The solve's share.** B's Groebner solve is 99.1% of its cold CPU
  (47.79 of 48.22 s; 8.775 ms per call over 5,446 calls per point). N's native
  solve is 0.0525 s, 15.4% of N's cold CPU (0.0096 ms per call). The rest of
  N is setup 31.9% (0.1091 s) and the remaining online stage 52.7% (relation
  assembly and linear algebra). Past this change the solve is not the cost.
- **Per-pair spread.** The 60 pair ratios run from 114.8 to 161.0 (mean
  140.4, sd 9.5). The spread is between points: the 20 per-point means run
  from 115.3 (p14) to 158.4 (p11), sd 9.6, while the three pairs inside a
  point differ by sd 1.2 on average (0.8%; at most 3.4). N's cold CPU per
  pair is 0.286 to 0.402 s.
- **Order effect.** The start order (B first or N first) is fixed within a
  point: 9 points start with B and 11 with N, so it is confounded with the
  point. The ratio is 143.1 when B was first against 139.2 when N was first
  (2.8%); the between-point sd of 9.6 over 9 and 11 points gives a standard
  error near 4.3, so this is not separable and the receipt computes no
  interval. By position within the point's three pairs the ratio is 141.6,
  140.5, 141.0: flat.

### Root cause of v2's crash: confirmed

`diagnosis/digest_repro.sage` **ran, in Sage 10.10 (release 2026-09-28) in
the pinned image, and exited 0**
(`{"v2_reproduced": true, "mechanism_ok": true, "fix_ok": true, "ok": true}`).
It reproduced v2's TypeError and it recorded these types:

- **v2's calls.** v2's own `arm.sage` was run on rows p00-N and p00-B. Both
  exited 1 at the relation digest, after `through_relation_digests` and
  before any row file was written (`row_file_written: false`), with the last
  line `TypeError: Object of type Integer is not JSON serializable`. The
  traceback ends in the `json.dumps` inside `h = lambda o: hashlib.sha256(...)`.
- **The mechanism.** The literal `0` in a Sage file has type `Integer`
  (the preparser rewrites `row.get(col, 0)` to `row.get(col, Integer(0))`),
  and `Integer(0) + sg * pow(int, int, int) % int` is again `Integer`. So
  every element of the relation rows was an `Integer`, which `json.dumps`
  refuses.
- **v3's strict conversion** (`relation_digest.plain`): `Integer` becomes
  `int` (7), a real literal becomes a float (`RealLiteral` 0.5) and a
  `bool` stays a `bool`; it rejects, by design, a GF(2^19) element
  (`FiniteField_ntl_gf2eElement`), a `Rational` and a `RealDoubleElement_gsl`.
- **The fix is neutral.** The relation digests computed from Sage `Integer`
  rows and from plain `int` rows are equal (rows
  `26f65746...`, canonical `72d9c7de...`, ordered `fe85060d...`).

This confirms the root cause stated above. It is no longer an inference from
a traceback and an emulation without Sage.

### Tier 1 isolation assessment

**What the receipt establishes.**

- Every one of the 302 timed processes was pinned (`Cpus_allowed_list` 0
  inside a 4-CPU container affinity), the host CPU identity is unchanged
  from start to end, and `/proc/schedstat`, `/proc/stat`, `getrusage` and
  the `isolated_bench` counters were recorded for each process.
- No process raised a contention flag.
- The library digest is the same before and after every process, and the
  frozen files match.
- The comparison is repeated alternating pairs, with an A/A and a planted
  control, on one host class.

**Gaps, all of them.**

1. **Placement, not exclusivity.** A container affinity mask pins a vCPU; it
   does not make the host exclusive. The runner is a Hyper-V VM
   (`virtualization: microsoft`) whose other vCPUs and neighbours on the
   physical host are not observed. No CPU is isolated (`cgroup_isolated_cpus`
   and `nohz_full_cpus` are empty) and the whole job sits in one cgroup
   (`hosted-compute-agent.service`).
2. **One runner, one host class, no replay.** The timed job ran on one
   EPYC 9V74 runner. No second machine or host class has reproduced it.
3. **Two different hosts.** The smoke job ran on an EPYC 9V45 and the timed
   job on a 9V74. The library is digest-pinned across them and the smoke
   times are not used, but the smoke gate did not run on the timing host.
4. **Microcode unreadable.** The record shows `0xffffffff`, which is what a
   VM exposes; the CPU model and flags are uniform across the vCPUs.
5. **CPU only.** No GPU arm, and the numbers are CPU time of a pinned Sage
   process; they exclude Sage start-up. Seen from the launcher, the ratio
   is 12.96 [12.39, 13.52]: start-up (about 2.2 s per N process) dominates
   N's wall time, so the 141 is a CPU-in-process ratio, not what a user waits.
6. **Order is confounded with the point** (above), so an order effect cannot
   be separated.
7. **The matched rho is not wall-time tuned**, so the gap of 117.9 compares
   a native IC with a Python/Sage walk.
8. **The B arm is this protocol's tau6 arm**, with counts, logs and relations
   checked equal to N's at every point; it is not the first ledger row's
   run, host or unit.

None of these is closed. The improvement stands as a Tier 1 result with these
gaps named.

### Frozen files and the workflow fix

The workflow fix (`4ef371544`) changed **no frozen file**. It changed only
`.github/workflows/n19-native-tau6-v3.yml` (an `export` of `N19_RD` in the
step that sets it, in both jobs). `protocol.json`, `schedule.json`,
`inputs/panel.json`, `inputs/multi_systems.json`, `arm.sage`,
`native_binding.py`, `relation_digest.py`, `run_schedule.py`,
`verify_receipt.py`, `stats.py`, the native sources and
`diagnosis/digest_repro.sage` are the ones in the receipt's `frozen.sha256`,
and `runner_identity_matches_frozen_files` passed.

### Ledger

The verdict is an improvement, so `docs/ic/BASELINES.md` and `baselines.json`
apply the ratchet to the n = 19 row: the native-solve producer replaces the
tau6 Sage-Groebner row, carrying this run's paired R as its Tier 1
qualification. The old row moved to Other verified records, a ratchet-history
row was added, the n = 19 open note was updated (online `S` measured, IC1
manifests exist) and Figure 1 was re-rendered.


## History: the first run (39384735073, invalid)

**Verdict: invalid. No improvement, regression or null result is claimed.**

![First run outcome. Source: [figures/make_invalid_run1_figure.py](figures/make_invalid_run1_figure.py);
vector: [figures/invalid_run1.svg](figures/invalid_run1.svg).](figures/invalid_run1.png)

- **What happened.** Job `sage-smoke` queued about 20 min, started at
  07:29:16 UTC and failed at 07:30:20 in step 3, "Freeze runner and source
  identity". Job `timed` needs it and was skipped. Steps 4 to 9 (planted
  corruptions, toolchain and build, Sage image, `digest_repro.sage`, the
  smoke part and the smoke gate) were skipped. Only the always-run upload
  step ran.
- **Cause.** Step 3 appends `N19_RD` to `$GITHUB_ENV` and, in the same
  step, a Python heredoc reads `os.environ['N19_RD']`. A `$GITHUB_ENV` write
  reaches later steps only, so the lookup raised `KeyError: 'N19_RD'` and the
  step exited 1. This is a defect in
  [`n19-native-tau6-v3.yml`](../../.github/workflows/n19-native-tau6-v3.yml),
  not in the protocol, the solve or the verifier. The heredoc should read
  `$rd` (for example through `os.environ.get('N19_RD', ...)` after export, or
  by passing `rd` as an argument).
- **Archive.** [`run_github_39384735073/`](run_github_39384735073/) holds the
  one artifact (3,040 bytes, `smoke/host-probe.json`, sha256 `d8da435a...`),
  `run-record.json` (jobs, steps, failure) and `verify-local-copy/`. There
  was no `result.json` or `result_table.md` to reproduce. `verify_receipt.py`
  was run on a copy of the archive (parts smoke and timed): both give
  `invalid`, every data gate false, `schedule_and_panel_regenerate` true, and
  `result_table.md` has `n/a` in every row. Those two files are the local
  verifier's output on an incomplete archive, kept for the record; they are
  not a CI receipt.
- **Host seen.** AMD EPYC 7763, 4 vCPU (2 cores, 2 threads each), no AVX-512,
  Ubuntu 24.04.5, kernel 6.17.0-1022-azure, microcode unreadable
  (`0xffffffff`), the whole job in one cgroup of the hosted-compute agent.
  Nothing was timed on it.

### Frozen rule, as applied (first run)

| item | outcome |
| --- | --- |
| primary R = sum cold CPU(B) / sum cold CPU(N), 60 pairs | not computed (0 of 60 pairs) |
| improvement iff 95% lower bound > 1 | not applicable; verdict invalid |
| A/A in [0.95, 1.05] | not measured (0 of 60 pairs) |
| planted NX/N lower bound > 1 | not measured (0 of 20 pairs) |
| gates | sage-smoke failed; all other gates unevaluated, so false |
| time guard | not reached |

### Secondaries (first run)

Online S, setup, S per arm, the gap to the matched rho, the solve's share,
the per-pair spread and the order effect were all not measured. No number is
reported for them.

### Root cause of v2's crash (first run)

**Not confirmed and not refuted.** `diagnosis/digest_repro.sage` never ran,
so there is no Sage output and no recorded types. The standing support is
unchanged: v2's archived tracebacks and the preparser emulation in
[`diagnosis/`](diagnosis/README.md), neither of which ran Sage.

### Tier 1 isolation assessment (first run)

No Tier 1 claim exists, since nothing was timed. The gaps that remain for a
future run are the ones in the frozen design: a container affinity mask
records placement, not host-wide exclusivity; one hosted runner and one host
class (here AMD EPYC 7763); microcode unreadable; no replay on a second
machine; CPU-only. The workflow defect above is a further gap: the smoke
gate has now never executed, so no run has shown that the v3 smoke path
(Sage image, 20 smoke gates) works end to end.

### Next step (done)

Step 3 was fixed in `4ef371544` with nothing re-frozen; the re-launch is run
39387473809, below.

## Files

- **Code.**
  - `arm.sage` (one row per process), `relation_digest.py`,
    `native_binding.py` and `native/`;
  - `run_schedule.py` (the launcher and Tier 1 records), `verify_receipt.py`
    (fail closed) and `stats.py`.
- **Frozen inputs.**
  - `make_protocol.py` → `protocol.json`;
  - `make_panel.py` → `inputs/panel.json`;
  - `make_schedule.py` → `schedule.json`, with the parts smoke and timed;
  - `power_check.py` → `analysis/power.json`;
  - `inputs/multi_systems.json`, v2's 2,375 multi-solution systems.
- **Checks.** `tests/`, `smoke/` and `diagnosis/`.
- **Report.** `make_figures.py`, `figures/`, `README.pdf` and
  `report_header.tex`.
