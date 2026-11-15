---
title: "n = 83: closure base D4 (K' = 4, 400 orbits) against M38 (K' = 16, 608 orbits), one producer binary (Tier 1 design)"
date: 2026-11-07
---

# n = 83: closure base D4 (K' = 4, 400 orbits) against M38 (K' = 16, 608 orbits)

**Status (2026-11-08): result in. Verdict: improvement; every gate and control passes and the run is
valid** `[pcc:unverified]`. R = E2E(M38) / E2E(D4) = **2.0014 [1.8777, 2.1308]** over 60 alternating pairs, run
[42425640847](https://github.com/isogeny-labs/cryptanalysis/actions/runs/42425640847), Tier 1, instance scope. The
design sections below are the frozen text, unchanged; they were frozen before any timing on the Tier 1 runner (commit
`ebef3b260`). Every figure in them that comes from the shared cloud-agent VM is a local diagnostic, used only to size the
design. The result section is added with the archived receipt.

## Owner ruling, 2026-11-07 (recorded verbatim)

> Owner ruling, 2026-11-07, given in chat: a closure base with K' >= 4
> unknown-log columns counts as an index-calculus row. K' = 0 stays a
> known-log reference row.

So D4 (K' = 4) is an index-calculus row, and this measurement is judged by the
success criterion: a measured gain over the current n = 83
row. A K' = 0 base would be a known-log reference row (`koblitz-n83-knownlog-20261019`)
and is not measured here. The ruling is also in `protocol.json` (`owner_ruling`)
and in `docs/ic/BASELINES.md`, beside the known-log ruling-pending note.

## Result

Run [42425640847](https://github.com/isogeny-labs/cryptanalysis/actions/runs/42425640847) (workflow `n83-k4c400.yml`,
push trigger, head `36866ad3c`, attempt 1, conclusion success) on one GitHub-hosted `ubuntu-24.04` runner
(`GitHub Actions 1000197724`, image 20261101.360.1, **Intel Xeon Platinum 8370C**, execution CPU 0; the field-ops and
field-ops-2 runs were on AMD EPYC 9V74). The schedule ran 50.7 minutes. The receipt is archived in
[`run_github_42425640847/`](run_github_42425640847/) (`panel/runs.jsonl`, 2.4 MB, in the artifact store). The protocol and
schedule are those of the frozen commit `ebef3b260`; commit `36866ad3c` changed only the workflow file (the artifact path and
the store-pull step).

**Verdict: improvement** `[pcc:unverified]`. R = sum E2E(A) / sum E2E(B) = **2.0014 [1.8777, 2.1308]** over 60
alternating pairs (20 points x 3 pairs; two-stage paired bootstrap, 10,000 draws), A = M38 (K' = 16, 608 orbits), B = D4
(K' = 4, 400 orbits), the same binary `ic_online_fieldops_r770`. All 462 scheduled rows ran and are valid, none was skipped
by the time guard, and every gate passes (`verify-stdout.json`): per base one index and layout digest set equal to its frozen
one; Q0 equal to each base's frozen identity; identical relation digests, probe vectors, root calls and counters per D4 rank
seed across kD4FO and kD4FOaa; rank tables equal to the frozen pre-checked tables; every IC row's pipeline names equal to its
arm's; one scalar per point across both bases and rT, replayed in the oracle; placement, host identity and binaries
unchanged. `verify_receipt.py` and `band_model.py` re-run on a copy of the receipt reproduce `panel/result.json`,
`panel/result_table.md` and `band/band_model.json` byte for byte.

![Frozen ratios with 95% bootstrap intervals, from result.json (`figures/make_result_figure.py`,
[SVG](figures/result.svg)).](figures/result.svg)

### Primary, stages and controls (frozen rule)

| stage (A = M38, B = D4) | side A mean (ms) | side B mean (ms) | A / B [95%] |
| --- | ---: | ---: | --- |
| index build (cold process) | 5,116 | 2,138 | 2.3928 [2.3794, 2.4065] |
| scan self-test | 1,093 | 220 | 4.9689 [4.8934, 5.0602] |
| rank stage (rank process) | 3,815 | 2,182 | 1.7485 [1.5039, 2.0287] |
| online, one target | 298 | 460 | 0.6487 [0.3347, 1.1395] |
| cold process | 6,888 | 3,166 | 2.1757 [2.0530, 2.2975] |
| **end to end (rank + cold)** | 10,703 | 5,348 | **2.0014 [1.8777, 2.1308]** |

The four stage rows are stage secondaries and never decide. The saving is in the setup (setup A / B 2.4353
[2.4198, 2.4516]: the index build over 2.4x fewer stored states, and the self-test 5.0x faster on the smaller Feistel
domain) and in the rank stage (4 attempts instead of 16, each 2.4x more probes). The online stage is slower on D4 (A / B
0.6487, interval spanning 1: one target, one exponential sample per process). Process CPU time A / B 2.0715
[1.9855, 2.1626], process wall 2.0713; peak RSS 1,898 MB against 915 MB (A / B 2.0740) `[pcc:unverified]`.

- **A/A** (B against Baa, 40 pairs): end to end 1.0022 [0.9982, 1.0064] (interval contains 1), cold 1.0007
  [0.9960, 1.0053] (inside [0.97, 1.03]), CPU time 1.0016 [0.9991, 1.0043].
- **Planted:** cD4FOX / cD4FO index build 2.6961 [2.6802, 2.7099] (lower bound above 1); the planted processes kept the
  frozen layout digests and checked 2 x stored states roots.
- **Probe law** (estimate, band [0.80, 1.20], both gated over at least 64 attempts): kD4FO **1.0999** over 240 attempts
  (bootstrap interval [0.9383, 1.2634]; its upper end is above the band, the gated estimate is inside), kM38FO 1.0018
  [0.9233, 1.0897] over 960 attempts. The risk named before the run (the prototype's 1.154) did not materialise as a failure,
  but D4's point estimate is 10% above the law and its interval reaches 1.26: the true law ratio on D4 is not tight.
  kD4FO ns per probe 121.4.
- **Order and spread:** A first 2.0361, B first 1.9691; pair positions 2.0007, 2.0307, 1.9736; per-point ratios from 1.58 to
  2.38 (20 of 20 above 1). Geometric mean of the per-pair ratios 2.0242 [1.9049, 2.1519].
- **Observed variance against the power check** (`observed_cv_per_side`, per pair): D4 rank stage 0.415 (modelled 0.50),
  online 0.79 (1.2), E2E 0.176 (0.23); M38 rank stage 0.222 (0.21), online 1.08 (1.2), E2E 0.090 (0.076). The model
  over-stated the D4 spread, so the design had at least the power `analysis/power.json` gives (0.998 at a true 1.20x).

### The first run of the same frozen design (log only)

Run [42420993318](https://github.com/isogeny-labs/cryptanalysis/actions/runs/42420993318) (head `ebef3b260`, the frozen
commit) ran the same protocol and schedule and finished its whole schedule. Its job log printed the verifier's output: decision
`improvement`, E2E(M38) / E2E(D4) = **1.964 [1.841, 2.091]**, every check true (including the probe law and the 64-attempt
gate), A/A and planted controls passing. This is as reported from the job log by the coordinator `[pcc:unverified]`: its
artifact step named the field-ops receipt directory, so **no receipt was uploaded and nothing from that run is archived or
re-verified here**. It is reported beside the archived run, not combined with it. The two estimates (1.964 and 2.0014) have
overlapping intervals; they are two draws of the same design (same points, same seeds, same schedule, two runner instances),
so the run-to-run difference is the instance-to-instance noise of this measurement.

### Distance to rho

In this run's own matched rT770 rho (20 processes, mean cold 2,610.5 ms, step 275.68 ns), the end-to-end cold gap is
**4.0999 for side A (M38) and 2.0485 for side B (D4)** (point estimates, no interval computed for the gaps in this run); S
end to end cold is 0.4194 for A and **0.2095 for B** in rT770 steps `[pcc:unverified]`. These are in-run gaps on an Intel Xeon
Platinum 8370C. The field-ops run read 4.096 for the same M38 code on AMD EPYC 9V74 and the field-ops-2 run 3.165 for R1 on
another panel and runner: gaps do not compose across runs (the matched rho's cold mean is a mean of random-length
processes and moves with panel and host), only paired deltas within one run are deltas. Wall time, one host class, factor-base
construction charged to neither side, so cold S is a lower bound.

### Section 5a (priced native work; a model band)

`band_model.py` (frozen) with rho counted in this run and the IC arms modelled from the archived counted run 39882571652
(per-probe and per-attempt composition, this run's measured probes and attempts, each base's exact entries): at 0, 0.1
and 1 GAE per unpriced native operation, the gap to rT is A (M38) 0.000332, 1.136 [0.8876, 1.518], 4.527 and B (D4)
**9.771e-05, 0.7272 [0.5657, 0.9728], 2.897**. **D4 is cheaper than M38 at every weight** (the order holds at both
ends of every bound); **against the matched rho both are unresolved**: the order flips inside the band (D4 is below rho at
w = 0 and w = 0.1, and above it at w = 1; M38 is below at w = 0 and above at w = 0.1 and 1). This is a derived model, not a
counted run of the field-ops producer; the counts it uses are exact per (point, seed, base) so the band is the same in
the first run; the linear algebra and factor-base construction are not charged and the intervals carry no model
uncertainty `[pcc:unverified]`.

### Limits of this result

- Wall time on one GitHub-hosted runner (Intel Xeon Platinum 8370C), one pinned CPU, Tier 1 instance scope, no host-wide
  exclusivity; not replayed on another host class (the field-ops and field-ops-2 runs were on AMD EPYC 9V74).
- **Not stacked on R1.** D4 was measured against the field-ops producer on the M38 base, the row that preceded field-ops-2
  (R1, `koblitz-n83-fieldops2-20261107`, run 42424680756, 1.0256 [1.0236, 1.0278] over the same field-ops M38 reference). R1 x
  D4 was not run, and ratios from different runs do not compose.
- Per-base identities of D4 were frozen from local runs of the same producer (reproducibility, not independent proof); the
  independent checks are the pinned-oracle verification of header and table and the oracle replay of every recovered
  scalar.
- The narrowed panel scan, the reseed and the A/A rule change are disclosed above.
- Factor-base construction is charged to neither side, as in every n = 83 row.

## Files (result)

`run_github_42425640847/` (receipt, `band/`), `figures/make_result_figure.py`, `figures/result.svg`, `figures/result.png`,
`figures/make_report_pdf.py`, this report as `README.pdf`.

## Question

The current n = 83 baseline row is the field-ops producer
(`koblitz-n83-fieldops-20261104`, run 41869146827) on the M38 closure base: 16
unknown-log columns (K' = 16), 608 orbits in the root index. Its end-to-end cold
cost splits (that run's side B, ms): index build 4,439, scan self-test 899, other
setup 307, rank stage 3,160, online 171; E2E 8,976 `[pcc:unverified]`.

**Is the end-to-end cold cost of the D4 closure base lower than the M38 row's, with the
SAME frozen merged producer binary on both sides, on new held-out points and new
rank seeds?** Two levers move together (shortlist `algo_levers.md`, levers 1 and 2):

| | M38 (row) | D4 |
| --- | ---: | ---: |
| `make_closure_base.py` flags | `--columns 16 --norm 64` | `--columns 4 --norm 165` |
| unknown-log columns K' = rank attempts | 16 | 4 |
| multipliers per column / orbits | 38 / 608 | 100 / 400 |
| logical states 83 K_orb^2 | 30,682,112 | 13,280,000 |
| Feistel self-test domain | 2^26 | 2^24 (logical states < 2^24 = 16,777,216) |
| stored (folded) states | 15,341,360 | 6,640,200 |
| table entries E | 30,366,551 | 12,618,968 |
| lost to within-column coincidences | 1.03% | 4.98% |
| table slots | 2^26 | 2^25 |
| probes per relation, law r / (166 E) | 1.700 M | 4.091 M |

Fewer columns mean fewer relations (the rank stage needs K' of them); fewer orbits
mean a smaller index to build and to self-test; the price is a smaller table, so each
relation and each target costs 2.41 times more probes. `inputs/local_identity.json`
holds the frozen D4 identity (digests, layout, Q0 identity), obtained from five local
processes of the frozen producer; it is a reproducibility identity, not an independent
proof. The independent checks of D4 are `verify_closure.py --base --table --planted`
in the pinned pure-Python oracle (header, every orbit and label; table: every
[L_c]G = R_c and [w L_c]G = P; three planted corruptions rejected), the table equal
log for log to the first four logs of the oracle-checked M38 table, and, in the run, the
oracle replay of every recovered scalar and the equality of every rank process's
own produced table with the frozen one.

## Local prototype (diagnostic)

A local prototype (loaded 4-core VM, one pinned core, 65 runs; `inputs/local_profile.json`,
`inputs/local_prototype_rows.jsonl`, `profile/prototype_driver.py`) measured four candidate
headers against M38. D4 is its header (d): mean process total over 10 rank seeds 5,221 ms (sd
595) against 9,669 ms for M38 (sd 879), a 1.85x local E2E ratio. That figure has no interval,
one online target per cold run is a single exponential sample, the D4 rank stage is
heavy-tailed, nothing is matched to rho, and the host was loaded: it is the reason to run the
Tier 1 measurement, not a result `[pcc:unverified]`.

## Design

One GitHub-hosted `ubuntu-24.04` runner is the Tier 1 instance; one pinned CPU, one fresh
process per run (`run_schedule.py`, the template's, byte for byte).

- **One binary on both sides:** `ic_online_fieldops_r770`, the field-ops crate
  (`../koblitz-n83-fieldops-20261104/online-b`) built unchanged with `-C target-feature=+pclmulqdq`;
  every environment variable, pipeline name and gate of an IC process is the field-ops
  experiment's. Only the base header and its factor-log table differ (`arm.py` gates every IC process
  against ITS arm's base: base hash, columns, orbits, orbits per column, the multiplier list, states,
  slots, entries, digests, layout digests, and the cached table's own digest). `restore.py` runs the
  field-ops `restore.py` with its pin check (every digest of that protocol), regenerates the M38
  and D4 headers to their frozen SHA-256 and pins the field-ops files this experiment builds and runs.
- **Panel:** 20 new held-out points (`inputs/cold_targets.json`, role `k4c400-cold-v1`, disjoint
  from every earlier n = 83 panel including the field-ops and field-ops-2 panels:
  `inputs/panel_disjointness.json`).
- **Pairs per point:** three alternating primary pairs (A = M38 side, B = D4 side, same point and same
  rank seed, ABAB or BABA with a seeded start), two A/A pairs (B against Baa, the D4 arms twice), one
  planted pair (cD4FO against cD4FOX, `KIC_INDEX_CANON=lift_plant`) and one tuned-rho process.
- **Rank seeds:** 2501-2560, 60 distinct seeds (`inputs/seed_disjointness.json`; the first choice, 2301-2360, collided with `koblitz-n83-onlineframe2-20261021/schedule.json` on main and three branches, was caught by `check_seed_disjoint.py` (`new: false`) and replaced before any timing): 240 D4 attempts and
  960 M38 attempts for the probe-law gates.
- **Primary:** R = sum E2E(A) / sum E2E(B) over the 60 primary pairs, E2E = rank stage + cold process.
  Decision: improvement iff the 95% two-stage paired bootstrap lower bound of R exceeds 1
  (10,000 draws, points then pairs, A and B of a pair drawn together) `[pcc:unverified]`.
- **Per stage** (stage secondaries, never deciding): index build, scan self-test, rank stage, online.
- **Q0:** one cold process of cM38FO and cD4FO on the validation point; each must reproduce its
  base's frozen identity.

Arms: side A `kM38FO` + `cM38FO` (verbatim from the field-ops protocol); side B `kD4FO` +
`cD4FO`; A/A `kD4FOaa` + `cD4FOaa`; planted `cD4FO` / `cD4FOX`; matched rho `rT` (the tuned rT770).

### Gates

The field-ops verifier's gates with these changes (`verify_receipt.py`): two bases, each against its
own frozen identity (the digest sets must be exactly {M38, D4}); rank-seed identity (relation digest,
probe vector, root calls, counters) across kD4FO and kD4FOaa; **probe law for both kD4FO and kM38FO inside
[0.80, 1.20] over at least 64 attempts each** (a new gate: 240 and 960 attempts are scheduled); every
scalar replayed in the oracle; placement, host identity, binary identity, pipeline names, rank tables
equal to the frozen pre-checked tables.

### Controls

- **A/A:** B against Baa. The cold ratio's point estimate must be inside [0.97, 1.03]; the end-to-end ratio's
  95% interval must contain 1. The field-ops template required the end-to-end *point estimate* inside
  [0.97, 1.03]; with independent rank and online draws on D4 that rule fails a true null about half the time
  (`analysis/power.json`: `e2e_point_inside_0.97_1.03_rate` 0.47), so it is replaced here by the interval.
- **Planted:** cD4FOX / cD4FO index build, lower bound above 1, layout digests unchanged, 2 x stored
  states roots checked.
- **Exactness before timing:** the planted corruptions rejected on both closure bases, the crate tests.

### Power and variance (a sizing simulation, not a result)

`power_check.py` draws simulated receipts from the field-ops archive (the M38 side) and models D4
(index build x 0.399 from the local cold ratio, self-test x 0.25 from the domain step, online and each
of 4 rank attempts x 2.406 from E_M38 / E_D4, ns per probe unchanged; the rank stage is a sum of 4
archived attempt times, so its heavy tail is kept). Per-pair coefficients of variation in the model:
D4 rank stage 0.50, online 1.2, E2E 0.23 (M38: rank 0.21, online 1.2, E2E 0.076). Because A and B run
different bases their noise is independent, so the design resolves a large effect, not a small one:

| true E2E ratio | 1.00 | 1.05 | 1.10 | 1.20 | 1.50 | modelled (1.95) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| power, 12 x 3 pairs | 0.03 | 0.15 | 0.47 | 0.94 | 1.00 | 1.00 |
| power, 16 x 3 pairs | 0.02 | 0.16 | 0.53 | 0.98 | 1.00 | 1.00 |
| **power, 20 x 3 pairs (frozen)** | 0.01 | 0.21 | 0.70 | 1.00 | 1.00 | 1.00 |

The frozen 20 x 3 design separates an E2E ratio of 1.2 or more with power above 0.99, and will
not separate 1.05 (0.21) or reliably 1.10 (0.70): a smaller true effect is reported as not separated, not
as a regression. More seeds help the heavy-tailed rank stage but the 60 seeds also fix the probe-law
gate: at a true law ratio of 1.00 it passes with probability 0.998; at 1.15 (the local prototype's
40-attempt point estimate) 0.83. The modelled schedule is about 43 min (job about 62 min; about 92 min
on a 1.5x slower host; guard 165 min).

## Section 5a (priced native work against the matched rho)

AGENTS.md section 5a prices every arm's unpriced native work, the matched rho's included, at 0, 0.1 and 1
GAE per operation and ranks two arms only where the order holds across that band. `band_model.py` runs
the opcounts experiment's `band.py` unchanged. **rho is counted in this run** (every rT process's own
`charges_setup_and_solve`). **The field-ops producer emits no operation counts**, so the IC arms are a
**model**: the archived counted run 39882571652's per-probe and per-attempt composition, applied to this
run's measured probes and attempts per side and point, and to each base's exact stored entries. It is a
derived model band, labelled model wherever it is quoted, not a counted run of this producer; the linear
algebra and factor-base construction are not charged and the intervals carry no model uncertainty.

## Disclosures made before timing

- **Narrowed panel scan.** The field-ops `check_panel_disjoint.py` scans every origin branch's changed files. Here that
  was about 1,270 branches and did not finish in a 30-minute background limit. This copy scans origin/main in full and
  only the 90 origin branches whose name contains `n83` (2,808,268 files; 0 hits), plus the local worktree's
  `experiments/` (65,679 files; 0 hits); `refs_filter` in `inputs/panel_disjointness.json` says so. `make_targets.py` also
  regenerates every known role of the law and found no shared point. The scanner is no longer byte-identical to the
  field-ops file and is pinned separately.
- **Reseed.** Rank seeds 2301-2360 collided with `koblitz-n83-onlineframe2-20261021/schedule.json`; 2501-2560 are used.
- **A/A rule.** The end-to-end A/A rule is the interval containing 1 (above); the template's point-estimate band is kept
  for the cold ratio.
- **Local smoke** of segments O1 and P1 through `run_schedule.py` and `arm.py` (25 rows, all valid, every correctness check true
  except the 64-attempt law gate that a partial receipt cannot meet): a correctness check, never timing evidence.

## Not in scope

The producer, the probe loops, the rank-stage algorithm, the self-test's predicate and the factor base
are unchanged. Headers a (K' = 8, 624 orbits), b (K' = 4, 612) and c (K' = 8, 448) of the prototype are not
measured here. Factor-base construction is charged to neither side, as in every n = 83 row.

## Trigger

`.github/workflows/n83-k4c400.yml`, on a push to `claude/n83-k4c400` restricted by path filters (as the
field-ops workflow; `workflow_dispatch` was refused for earlier n = 83 integrations). It clones crypto
770f6a69 from the public `isogeny-labs/crypto`.

## Files

`restore.py`, `make_log_table.py`, `local_identity.py`, `make_local_profile.py`, `make_targets.py`,
`check_panel_disjoint.py`, `check_seed_disjoint.py`, `make_power_prior.py`, `power_check.py`,
`make_protocol.py`, `make_schedule.py`, `run_schedule.py`, `arm.py`, `check_log_table.py`,
`verify_receipt.py`, `test_verify_receipt.py`, `band_model.py`; `protocol.json`, `schedule.json`;
`inputs/`, `analysis/power.json`, `profile/`.
