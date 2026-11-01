---
title: "n = 83 K899: the nested 899-column factor base under the rank-probe producer, end-to-end cold"
date: 2026-10-19
---

# n = 83 K899: the nested 899-column factor base under the rank-probe producer, end-to-end cold

**Status (2026-10-19): Tier 1 run landed, verdict improvement.** The
[protocol](protocol.json) (frozen 2026-10-19T18:48:09Z) and the
[schedule](schedule.json) were committed before any Tier 1 timing. The Tier 1
run ([39306394645](https://github.com/aburan28/cryptanalysis/actions/runs/39306394645),
archived in [`run_github_39306394645/`](run_github_39306394645/)) gave
R = 1.1873 [1.1247, 1.2523]; see [Result](#result). The go/no-go diagnostic
ran on a GitHub runner
([run 39292460576](https://github.com/aburan28/cryptanalysis/actions/runs/39292460576),
archived in [`diag/run_github_39292460576/`](diag/run_github_39292460576/)).
It is one process per arm with one rank seed, on Q0. It is a diagnostic,
not timing evidence. Numbers from the cloud-agent VM are labelled
**local**.

## Question

The n = 83 a = 1 one-target index-calculus baseline is the rank-probe
producer, `koblitz-n83-rankprobe-20261019` (PR #980, run 39214027289). It
runs at K600: end-to-end cold 166.0 s, of which the rank stage is 143.7 s.
Its rank stage makes 600 attempts. Each attempt probes the root table until
the first hit, and the mean number of probes follows the law r / (166 E),
where E ≈ 83 K² root-table entries. So K moves two terms in opposite
directions:

- the rank stage, K x r / (166 x 83 K²) probes, which falls like 1/K;
- the index build and its self-tests, which grow like K².

A pre-registration cost model put the optimum near K ≈ 900:
E2E(K) ≈ 146.9/a + 21.6 a² + 0.31 a + 0.38/a² s with a = K/600. That
predicts K899 at about 151 s [142, 165], about 1.10x. K899 is the largest K
whose folded root table keeps 2^27 16-byte slots (2 GiB); K900 needs 2^28.
The nested base `n83-compact-orbit-k899-20261012/runs/K899/base.jsonl`
holds B's K600 base as an exact prefix: the same 600 representatives,
99,600 points and labels.

Does K899 lower the **end-to-end cold** cost of the rank-probe producer,
against K600, on new targets and new rank seeds, with every answer verified
and the factor-log table of each K verified? This is an iteration under
AGENTS.md "Success criterion". A promoted result becomes the new n = 83 row.

![Relative cost: the cost model (blue, a model) and the runner diagnostic
(orange, one process per arm). Source: [figures/design.tex](figures/design.tex),
rendered by [`make_figures.py`](make_figures.py); vector:
[figures/design.pdf](figures/design.pdf).](figures/design.png)

## Does the producer support K other than 600? (yes, with no code change)

The producer is the rank-probe producer, unchanged. `restore.py` derives it
with the rank-probe experiment's own `make_online_source.py` and five
parents, verbatim, and checks the frozen digest `d4394df3...`. K is an
input: the base file. Checked in the source
(`snapshots/r770/examples/koblitz_orbit_dlp_fast_online_rankprobe.rs`):

- **Hard-coded 600s.** They appear only in two unit tests: the Feistel
  bijection on 29,880,000 states, and `Fold128::new(600, 83)` against
  14,940,300 stored states. Neither runs in a process.
- **Slot capacity.** The table is `CompactRootTable128::with_capacity(2 x
  states)`, so it has (4 x stored states).next_power_of_two() slots:
  2^26 at K600 and 2^27 at K899 (4 x 33,540,791 = 134,163,164 < 2^27).
- **Packed fields.** The 16-byte slot stores the four `pack` fields in 11
  bits each, so K < 2048 is fine. Keys are 83 bits.
- **Folded-index sizes.** `Fold128::new(columns, n)` takes them from the
  base. The echelon, the rank target (full rank = columns) and the
  factor-log table width come from the base's orbit columns too.
- **What was K600-specific.** Only the experiment wrapper. The rank-probe
  `arm.py` hard-codes the stored states, the slot count, the table entries
  and B's index digests. Here `arm.py` reads them per arm from
  `protocol.json` `online.k.<K>`.

The runner diagnostic confirms this. At K899: 899 columns, 67,080,683
logical and 33,540,791 stored states, 2^27 slots (2,147,483,648 bytes),
67,077,932 entries, full rank in 899 attempts with 0 failures and 0 rows
without gain, peak RSS 3.88 GB (K600: 1.88 GB).

## Go/no-go diagnostic (runner, run 39292460576)

The host was an AMD EPYC 9V45 GitHub runner with transparent huge pages
`madvise`. That is a different and faster host class than run 39214027289's
(K600 rank stage 105.6 against 141.5 ns per probe). One pinned CPU. Order:
cP600, kP899, kP600, cP899, cP600, cP899, cPI600, cPI899. Rank seed 8991,
used by no frozen run. Source:
[`diag/run_diag.py`](diag/run_diag.py),
[`diag/run_github_39292460576/diag.json`](diag/run_github_39292460576/diag.json).

| | K600 | K899 | K899 / K600 | gate |
| --- | ---: | ---: | ---: | --- |
| index build, cold (mean of 2) | 15.70 s | **37.92 s** | 2.42 | K899 ≤ 55 s: **pass** |
| index build, lift_scan (cPI) | 12.74 s | 31.07 s | 2.44 | |
| setup, cold (mean of 2) | 17.23 s | 39.01 s | 2.26 | |
| cold (setup + online, mean of 2) | 17.56 s | 39.12 s | 2.23 | |
| rank stage | 111.71 s | 85.70 s | 0.767 | |
| rank ns per probe, all attempts | 105.6 | **121.5** | 1.150 | K899 ≤ 150 ns: **pass** |
| rank ns per probe, first 50 attempts | 103.7 | **120.0** | 1.157 | K899 ≤ 150 ns: **pass** |
| first 50 attempts | 10.23 s | 4.46 s | | |
| mean probes per attempt / law | 1.019 | 1.016 | | |
| online ns per probe (S3 loop, Q0) | 158.7–171.3 | 181.1–238.7 | | |
| single-process E2E (rank + cold) | 129.3 s | 124.8 s | **0.966** | |

**Verdict: GO.** Both thresholds are met on the runner. The per-probe
cost rose 15%, though, where the cost model assumed 1.0. That is the
2 GiB table, and it moves the predicted end-to-end ratio from about 1.10
to **about 1.036** (this host, one seed).

**Local (cloud-agent VM, contended, THP `madvise`):** the per-probe ratio
K899/K600 was 1.22 (405 against 496 ns, with glibc's
`glibc.malloc.hugetlb=1` tunable, back to back) and 2.56 under heavier
load. The index ratio was 2.0–2.5. These are not used. The VM inflates
lookups into the 2 GiB table, as expected, and the runner is the
instrument. The local records are in [`smoke/`](smoke/).

## Exactness at K899

K899 cannot reproduce K600's probes, since it is a different index.
Exactness here means four things, each a frozen gate:

1. **The factor-log table is self-consistent and verified.** The producer
   checks [L_j]G = R_j for every column before any target.
   `check_log_table.py` re-checks every log of both frozen tables in the
   pinned pure-Python oracle in every Tier 1 job. The K899 table
   ([`inputs/factor_logs_n83_K899.json`](inputs/factor_logs_n83_K899.json),
   logs sha256 `c6652350...`) was written by the diagnostic's rank stage.
   It passed the oracle on all 899 columns on the runner and locally; the
   two runs wrote the same logs. The K600 base is an exact prefix of the
   K899 base, and discrete logs of fixed points are unique mod r, so the
   first 600 K899 logs must equal B's K600 table, and they do. Every Tier 1
   rank process must write its K's table log for log (B's at K600).
2. **Same scalar everywhere.** For every target, the scalar is the same in
   every K600 process, every K899 process and rT, and it replays as
   [d]G = Q in the oracle. At Q0, K899 gives scalar 3141592653589793 with
   relation [69918, 46431, 52870, 61057] and 486,779 probes. K600 gives
   1,987,852 probes with B's archived relation. Both are frozen identities.
3. **Within K899, the rank arms agree attempt for attempt.** kP899,
   kP899aa and kPX899 must give one relation digest, one per-attempt probe
   vector, one root-call total and one set of point-addition counters per
   block. The planted arm kPX899 also checks the frame keys against the
   rank-cut keys on every candidate at K899.
4. **The probe law holds.** Per K, the mean probes per rank attempt pooled
   over the four blocks, divided by r / (166 E_K), must fall in **[0.90,
   1.10]**. This band was frozen before any timing. With 2,400 (K600) and
   3,596 (K899) attempts the standard error is about 2.0% and 1.6% (CV
   0.97 per attempt). The archived Feistel-order K600 ratios were 0.978 and
   1.036, and the diagnostic gave 1.019 and 1.016. ±10% is about five
   standard errors.

## Frozen Tier 1 design

One GitHub `ubuntu-24.04` runner, one pinned CPU, Tier 1 counters, one
fresh process per run (`.github/workflows/n83-k899.yml`). Every IC arm runs
`ic_online_rankprobe_r770` with lift_scan target keys, the Feistel order,
prefetch, and the 16-byte compact table over the folded index.

| Arm | Kind | K | Role |
| --- | --- | ---: | --- |
| `cP600` | cold | 600 | **baseline** cold (the rank-probe producer's cP) |
| `cP899` | cold | 899 | **candidate** cold |
| `cP899aa` | cold | 899 | A/A: a second cold process of cP899 |
| `cPI600`, `cPI899` | cold | 600, 899 | pre-registered secondaries: lift_scan in the index build (`KIC_INDEX_CANON=lift`); never decide |
| `rT` | rho | | tuned rho rT770, same points |
| `kP600` | rank | 600 | **baseline** rank stage (`KIC_RANK_SOLVE=frame`) |
| `kP899` | rank | 899 | **candidate** rank stage |
| `kP899aa` | rank | 899 | A/A: a second process of kP899 |
| `kPX899` | rank | 899 | planted positive control: `frame_plant` at K899 (redoes the rank-cut key derivation on every candidate and compares; a known extra cost, about 1.97x per probe in run 39214027289) |

**Baseline choice.** The index-lift run (`claude/n83-indexlift`, run
39290913632) had not landed at freeze time. So the baseline is the
rank-probe producer, and the lift_scan index build runs as the cPI pair at
both K.

- **Panel.** 20 new public points, role `k899-cold-v1`
  ([`inputs/cold_targets.json`](inputs/cold_targets.json),
  `make_targets.py`). They are disjoint from Q0, B's panel and every
  earlier n = 83 panel of B's law. That includes `rankprobe-cold-v1`
  (which the rotation-key draft reuses) and `indexlift-cold-v1`. It was
  checked against the committed panel files too.
- **Rank blocks.** Four new blocks K1–K4, rank seeds 401–404, on units
  s000–s003. Every rank arm of a block runs the same seed, so K600 and K899
  draw the same scalars [a]G for their rank targets. Cold arms are paired
  by point.
- **Order.** O1 (Q0), then C1–C5, K1, C6–C10, K2, … K4. Arms are shuffled
  within each segment with fixed seeds.

### Frozen rule

- **Primary.** R = E2E(kP600, cP600) / E2E(kP899, cP899). Here E2E(k, c)
  is the mean of k's `timing_ms.rank_stage` over the rank blocks plus the
  mean of c's `cold_in_process_ms` over the 20 points, so it covers setup,
  index build, rank stage, linear algebra and one-target online.
- **Bootstrap.** 10,000 draws. The rank blocks are resampled with the same
  drawn ids for both arms. Within each drawn block, each arm's attempts are
  resampled independently: the two K run different attempts, so they
  cannot be paired. Each process keeps its non-attempt time. The cold
  points are resampled, paired across cP600 and cP899.
- **Decision.** Improvement iff the 95% lower bound of R is above 1.
  Regression iff the upper bound is below 1. Otherwise not separated.
- **Invalid.** The verdict is invalid if any gate or control fails, or any
  scheduled row is missing (time-guard skips included).
- **Controls.** A/A: E2E(kP899, cP899) / E2E(kP899aa, cP899aa), attempts
  paired, and cold cP899 / cP899aa must both be inside [0.97, 1.03].
  Planted: kPX899 / kP899 per attempt (paired) must have its 95% lower
  bound above 1.
- **Gates.** As listed in the protocol: per-K layout and digests in
  `arm.py`; one scalar per point plus oracle replay; one relation and one
  probe count per point and K; the Q0 identities; the rank tables; the
  in-block K899 agreement; the frame counters; the law band.
- **Secondaries** never decide. They are: the whole rank stage kP600 /
  kP899; ns per probe (all attempts and the first 50); cold, setup, index,
  online and RSS ratios; the cPI pair; and S and the gaps to rT.
- **Time.** Job limit 350 min, guard 300 min. The diagnostic's process
  walls with a 1.5x margin give segment upper estimates of C 232 s, K 881 s
  and O 88 s: 157.5 min with a 20-min build allowance, 111.4 min expected.
  On run 39214027289's slower host class (about 1.34x per probe) the
  expected total is about 150 min.

### Power (before freezing)

Source: [`power_check.py`](power_check.py) on
[`inputs/power_prior.json`](inputs/power_prior.json). The prior is run
39214027289's kP / kPaa attempts (seeds 301–304) and its cP / cR / cPI
cold. A simulated K899 block draws 899 K600 attempts rescaled: the
probes-to-first-hit are geometric, so the shape of the per-attempt
distribution is kept and only its mean moves. Its cold is cR times the
diagnostic's cold ratio, 2.227. The frozen bootstrap is applied, with 400
simulations of 400 draws ([`analysis/power.json`](analysis/power.json)).

| end-to-end effect R | 1.00 | 1.03 | 1.036 (diagnostic) | 1.05 | 1.07 | 1.10 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| power, 4 blocks (the design) | 0.018 | 0.14 | **0.16** | 0.375 | 0.65 | **0.91** |
| 8 blocks (information only) | 0.005 | | 0.34 | 0.63 | | |
| 12 blocks (information only) | 0.005 | | 0.48 | 0.81 | | |

**Reading.** The interval is set by the rank stage's own randomness, not by
timing noise. Probes per attempt are geometric (CV 0.97), and the two K
run different attempts. Four blocks resolve the model's 1.10 but not the
diagnostic's 1.036. If the runner's 15% per-probe penalty holds, a
`not_separated` verdict is the likely outcome. The design keeps the four
blocks it was asked for.

## Result

**Verdict (frozen rule, applied as written): improvement.** R = E2E(kP600,
cP600) / E2E(kP899, cP899) = **1.1873 [1.1247, 1.2523]** (20 points, 4 rank
blocks); the 95% lower bound is above 1. Every gate and both controls pass.
The run is valid.

The [run](https://github.com/aburan28/cryptanalysis/actions/runs/39306394645)
([archive](run_github_39306394645/), artifact digest
`c5ef1991...c18b3`) finished with conclusion `success`: 138 scheduled rows,
138 valid, 0 invalid, 0 skipped by the time guard, guard not tripped. One
runner (`runnervm8k3b6`, AMD EPYC 7763, 4 vCPUs, one pinned CPU, kernel
6.17.0-1022-azure), the same host and kernel as the rank-probe run
39214027289; the go/no-go diagnostic ran on another host
(`runnervmxehtw`, kernel 7.0.0-1017-azure). No contention flags.

**Power caveat, stated before and kept.** The frozen design had power 0.16 at
the diagnostic's expected R of about 1.036 and 0.91 at the model's 1.10, so a
`not_separated` verdict was the likely outcome and would have been an honest
one. It did not happen: the measured effect is larger than both. The reason
is the rank stage, not the cold path (see below). The diagnostic's 1.036 came
from a single process on a different host (121.5 ns per probe at K899 there,
146.5 ns here). This is one run on one runner; the interval is over points,
blocks and attempts, not over hosts.

### Gates and controls

| Gate or control | Result |
| --- | --- |
| every scheduled row present and valid; no time-guard skip | pass (138 / 138) |
| one scalar per point across every IC process of both K and rT, oracle replay | pass |
| one relation and one probe count per point and K | pass |
| Q0 equal to the archived K600 identity and the frozen K899 identity | pass |
| every rank table equal to its K's frozen table (K899 table re-verified in the oracle, first 600 logs equal B's) | pass |
| kP899, kP899aa, kPX899: identical relations, probe vectors, root calls and counters per block | pass |
| probe law band [0.90, 1.10], both K | pass (K600 1.0256, K899 0.9798) |
| A/A E2E kP899+cP899 / kP899aa+cP899aa | 0.9988 [0.9966, 1.0008], inside [0.97, 1.03] |
| A/A cold cP899 / cP899aa | 0.9997 [0.9966, 1.0026], inside [0.97, 1.03] |
| planted kPX899 / kP899 per attempt (paired) | 1.9353 [1.9321, 1.9397], lower bound above 1 |
| rank A/A kP899 / kP899aa per attempt | 0.9984 [0.9957, 1.0012] |

Every rank arm resolved all of its attempts (600 per block at K600, 899 at
K899; 0 fallback states, 0 irregular inputs). kP899, kP899aa and kPX899 have
the same swapped-pair counts per block; kPX899 compared 326 to 358 million
inputs per block with the rank-cut keys, the others none.
`verify_receipt.py` re-run on the archive reproduces `panel/result.json` and
`panel/result_table.md` byte for byte.

![Frozen ratios with 95% bootstrap intervals, all from `result.json`
([source](figures/result.tex), [vector](figures/result.pdf), rendered by
[`make_figures.py`](make_figures.py)).](figures/result.png)

### Primary and secondaries (none of the secondaries decides)

End-to-end cold means (mean rank stage over four blocks + mean cold over 20
points): kP600+cP600 151.31 + 22.48 = 173.79 s; kP899+cP899 99.70 + 46.67 =
146.38 s. The K600 arm's rank stage is 87.1% of its end-to-end cost, the
K899 arm's 68.1%.

| Quantity | K600 | K899 | Ratio [95%] |
| --- | ---: | ---: | :--- |
| **E2E cold R = kP600+cP600 / kP899+cP899** (s) | 173.79 | 146.38 | **1.1873 [1.1247, 1.2523]** |
| rank stage, whole (mean per block, s) | 151.31 | 99.70 | 1.5176 [1.4149, 1.6235] |
| rank stage per block (s) | 143.7, 148.0, 156.5, 157.1 | 100.0, 97.3, 96.3, 105.3 | |
| attempts per block / mean probes per attempt | 600 / 1,772,065 | 899 / 754,089 | |
| ns per probe (all attempts) | 142.19 | 146.52 | 0.9705 |
| ns per probe, first 50 attempts per block | 141.4 to 142.8 | 145.9 to 146.8 | |
| cold without rank stage (s) | 22.476 | 46.674 | 2.0766 [2.0555, 2.0954] |
| setup (s) | 22.040 | 46.464 | 2.1081 [2.1012, 2.1157] |
| index build (s) | 19.660 | 44.263 | 2.2515 [2.2461, 2.2577] |
| one-target online (ms) | 436.0 | 210.4 | 0.4825 [0.2688, 0.8733] (cP899 / cP600) |
| peak RSS (MiB) | 1,788 | 3,704 | 2.0713 [2.0711, 2.0716] |
| probe law, probes per attempt over r / (166 E) | 1.0256 (se 0.0214) | 0.9798 (se 0.0168) | band [0.90, 1.10] |

- **Probe law.** Mean probes per attempt fall from 1.772 million at K600 to
  754 thousand at K899, as the law r / (166 E) with E ~ 83 K^2 predicts
  (ratios 1.026 and 0.980). The rank stage is faster because each attempt
  needs 2.35 times fewer probes, 899 attempts instead of 600 cost 1.50 times
  more, and the per-probe cost rises only 3% (142.19 to 146.52 ns). The
  slot cliff is not crossed: 4 x 33,541,591 stored states fit in 2^27 slots.
- **The cold path pays for K899.** Cold without rank, setup, index build and
  RSS all about double (2.08, 2.11, 2.25, 2.07). The cold path is 12.9% of
  end-to-end cost at K600 and 31.9% at K899. Online time falls to 0.48
  (more factor-base columns, fewer probes).
- **Pre-registration model.** The model's 1.10x end to end (K899 about 151 s
  [142, 165]) was below the measured 146.4 s and its 1.187. The point
  estimate of R is also helped by the probe-count draw: the two arms ran
  different attempts (K600 at 1.026 of the law, K899 at 0.980), a 4.7%
  spread in the rank stage's probe counts that would lower R by roughly 4% if
  both were at the law. The bootstrap carries that sampling noise in
  its interval; the seeds 401-404 K600 arm also reads 173.8 s against the
  archived 166.0 s (seeds 301-304, 1,690,645 probes per attempt).
- **S** (cost over this run's rT770 step, 280.43 ns, per sqrt(r)):

  | Arm | E2E cold | cold without rank | online |
  | --- | ---: | ---: | ---: |
  | kP600+cP600 | 6.694 | 0.8658 | 0.016793 |
  | kP899+cP899 | 5.639 | 1.7979 | 0.008104 |
  | kP600+cPI600 | 6.475 | 0.6467 | 0.016741 |
  | kP899+cPI899 | 5.145 | 1.3044 | 0.008038 |

  Delta S end-to-end cold K600 to K899 = -1.056. The tuned rho's own S in
  this run: cold 0.10352, online 0.09316 (mean rT770 cold 2,687.5 ms,
  online 2,418.4 ms).
- **Gap to the tuned rho rT770** (IC / rho, 20 points; distance remaining,
  not a gate). End-to-end cold: kP600+cP600 64.67 [53.80, 81.28]; kP899+cP899
  54.47 [45.31, 68.20]; kP600+cPI600 62.55 [51.60, 78.47]; kP899+cPI899
  49.70 [41.46, 62.08]. Online: cP600 / rT 0.1803 [0.0978, 0.3116]; cP899 /
  rT 0.0870 [0.0583, 0.1265].
- **cPI pair** (lift_scan in the index build; pre-registered, never
  decides). Cold without rank cP600 / cPI600 1.3389 [1.3340, 1.3437]; cP899 /
  cPI899 1.3783 [1.3734, 1.3833]. E2E kP600+cPI600 / kP899+cPI899 1.2586
  [1.1888, 1.3330] (168.10 s to 133.57 s); kP600+cP600 / kP899+cPI899 1.3011
  [1.2304, 1.3747]. The last is a cross-arm figure (it changes both K and the
  index build); it is not a promoted pipeline.
- **Planted control.** kPX899 / kP899 per attempt 1.9353 [1.9321, 1.9397]
  (283.55 against 146.52 ns per probe); whole stage 1.9318.

### Limits of this result

- Tier 1, instance scope: one runner, one pinned CPU, 20 cold points, four
  rank blocks, one fresh process per arm per point. It was not replayed on
  another host class. The diagnostic's host ran about 1.2x faster per probe.
- The effect is a wall-time ratio. The probe count falls with K by the law;
  the saving is real work, not per-probe speed (ns per probe rose 3%).
- The two K draw different attempts, so R carries probe-count sampling noise
  (above); the interval is the frozen bootstrap's and is wider than the
  K600-versus-K600 comparisons of earlier runs because of it.
- Factor-base construction is charged to neither arm (both load a base file);
  it is larger at K899, so the ratio is an upper bound on the every-phase
  ratio.
- The producer is the rank-probe producer. The index-lift producer
  (run 39290913632, now the n=83 baseline row) was not run at K899 as a
  primary; only its index build is in the cPI secondaries.
- The power caveat above stands: the design could not have promised this
  verdict; it is reported as measured.

## Files

| File | Role |
| --- | --- |
| `protocol.json`, `schedule.json` | frozen protocol and run order (`make_protocol.py`, `make_schedule.py --check`) |
| `restore.py`, `make_online_source.py` + five parents, `online/`, `lift2/` | the unchanged rank-probe producer, digest-checked |
| `arm.py`, `run_schedule.py` | one arm per process, with K-specific gates; the pinned schedule runner |
| `verify_receipt.py` | gates, controls, primary and secondaries |
| `check_log_table.py` | both tables in the oracle, the prefix and the first 600 logs |
| `inputs/k899_identity.json` | frozen K899 facts and the diagnostic summary (`diag/make_identity.py`) |
| `inputs/factor_logs_n83_K899.json` | the K899 factor-log table |
| `diag/` | the go/no-go diagnostic script, workflow `.github/workflows/n83-k899-diag.yml`, archived runner output |
| `smoke/` | local records: the contended VM diagnostic, the THP rank pair, the O1 smoke through `run_schedule.py` (correctness only) |
| `run_github_39306394645/` | the archived Tier 1 artifact: allocation, builds, raw runs, `panel/result.json`, `panel/result_table.md` |
| `make_figures.py`, `figures/` | design figure and result figure (`figures/result.*`, from `result.json`) |
| `README.pdf` | this report: `pandoc README.md -o README.pdf --pdf-engine=pdflatex -H report_header.tex --lua-filter report_filter.lua -V geometry:margin=2cm -V fontsize=10pt -V colorlinks=true` |
