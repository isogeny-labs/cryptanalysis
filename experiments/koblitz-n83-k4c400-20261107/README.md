---
title: "n = 83: closure base D4 (K' = 4, 400 orbits) against M38 (K' = 16, 608 orbits), one producer binary (Tier 1 design)"
date: 2026-11-07
---

# n = 83: closure base D4 (K' = 4, 400 orbits) against M38 (K' = 16, 608 orbits)

**Status (2026-11-07): design frozen, no timing yet.** The design sections
below are the frozen text. They were frozen before any timing on the Tier 1
runner; every figure in them comes from the shared cloud-agent VM and is a
local diagnostic `[pcc:unverified]`, used only to size the design. The result
section is added with the archived receipt.

## Owner ruling, 2026-11-07 (recorded verbatim)

> Owner ruling, 2026-11-07, given in chat: a closure base with K' >= 4
> unknown-log columns counts as an index-calculus row. K' = 0 stays a
> known-log reference row.

So D4 (K' = 4) is an index-calculus row, and this measurement is judged by the
success criterion: a verified, measured improvement over the current n = 83
row. A K' = 0 base would be a known-log reference row (`koblitz-n83-knownlog-20261019`)
and is not measured here. The ruling is also in `protocol.json` (`owner_ruling`)
and in `docs/ic/BASELINES.md`, beside the known-log ruling-pending note.

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
log for log to the first four logs of the verified M38 table, and, in the run, the
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
equal to the frozen verified tables.

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

| true E2E speed-up | 1.00 | 1.05 | 1.10 | 1.20 | 1.50 | modelled (1.95) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| power, 12 x 3 pairs | 0.03 | 0.15 | 0.47 | 0.94 | 1.00 | 1.00 |
| power, 16 x 3 pairs | 0.02 | 0.16 | 0.53 | 0.98 | 1.00 | 1.00 |
| **power, 20 x 3 pairs (frozen)** | 0.01 | 0.21 | 0.70 | 1.00 | 1.00 | 1.00 |

The frozen 20 x 3 design separates a speed-up of 1.2 or more with power above 0.99, and will
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
