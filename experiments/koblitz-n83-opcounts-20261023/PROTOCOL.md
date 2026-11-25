# Protocol: n = 83 rank block K1 and cold panel with native work counted

Frozen 2026-10-23, before any run of this protocol. Committed on its own,
after the counted producer and ahead of the workflow that runs it
(`.github/workflows/n83-opcounts.yml`).

## Purpose

Close the open item of `docs/ic/baselines.json`: "the section 5a
0 / 0.1 / 1 GAE band for the IC / rho gap is uncomputable on both n=83 rows:
the frozen producer emits no group-operation counts". This run re-executes
the stacked experiment's rank block K1 (kS, kP) and its cold panel (cS, cP
and the tuned rho rT on the 20 cold points) with the counted producer, and
applies `band.py` to the counts.

This is a counting replay of frozen code, not a new experiment: it measures
no new improvement and cannot promote, demote or replace a baseline row.
Its timing is recorded but not read.

## Frozen inputs

`PINS.sha256` lists the sha256 of every file this run reads that is not
already pinned by the stacked experiment: the derivation
`make_counted_source.py`, the derived counted producer (generated in the job,
checked after derivation), the counted crate's `Cargo.toml` and `Cargo.lock`,
the driver `opcounts.py`, `band.py`, and the stacked experiment's
`protocol.json`, `schedule.json`, `arm.py`, `run_schedule.py` and
`scripts/isolated_bench.py`.

| input | sha256 |
| --- | --- |
| `experiments/koblitz-n83-opcounts-20261023/PINS.sha256` (this commit) | `1465477d3720ddd9a68d3f57d3a6ee6dacdcc619e5f64745124aaba05b50ecf7` |

The frozen stacked producer is restored and built by the stacked
workflow's own steps (crypto `770f6a69`, `restore.py`, derived source
`83b58988...`, Rust 1.99.0). `make_counted_source.py` regenerates that
source, requires the digest `83b58988...`, and writes the counted producer
(`ic_online_stacked_counted_r770`, built with `--features op-counts`). The
tuned rho `rho_tuned_r770` is the stacked crate's, unchanged.

## Runs (one job, one pinned CPU, one fresh process per run, this order)

Every run goes through the stacked experiment's `run_schedule.one()` and
`arm.py` unchanged; only the IC binary name differs.

| serials | arm | point | seed | archived twin (run 38862448935) |
| --- | --- | --- | --- | --- |
| 1 | kS | K1 point `s000` | 101 | serial 42 |
| 2 | kP | K1 point `s000` | 101 | serial 43 |
| 3-62 | cS, cP, rT for each of `s000` ... `s019` in order | the cold point | IC 7, rho 870000 + i | the same arm and point |

## Pass / fail (frozen)

The run's counts are **identical** (verdict `counts_identical`) only if:

1. Every run is `valid` in `run_schedule.one()` / `arm.py` terms (exit 0,
   verified scalar, full rank and factor logs equal to B's archived table
   for kS and kP, index digests equal to B's index).
2. Every output that is not a clock equals the archived twin: for kS and
   kP every attempt's probes, `rank_relations_blake3`, rank probes, root
   calls, attempts, relations, failures and rank; for cS and cP the
   target's relation, x-codes, intermediates, probes, root calls, relation
   checks, skipped states and scalar, and the index digest; for rT the
   scalar and every charge in `charges_setup_and_solve`.
3. Every IC row carries `op_counts` with `enabled: true`, and each point
   has one scalar across every arm.

Any other outcome is `counts_fail`, reported with every row; no band is
quoted from a failing run.

## The band (frozen analysis, `band.py`)

For each arm, a unit is one solved target with all of its work:
IC arm S = kS's rank stage + cS's setup, linear algebra (cached-table load
and verification of every factor log) and online interval at the point,
which is the stacked experiment's end-to-end cold `E2E(kS, cS)`; arm P the
same with kP and cP; rho = rT's setup and solve (`charges_setup_and_solve`).
Priced cost = group operations + w x (unpriced native operations) for
w in {0, 0.1, 1} GAE, with the kind map in `band.py` (`CLASSES`):

- IC group = `ec_add` + `ec_double`; IC unpriced native = root solves,
  root-index probes and inserts, filter queries and inserts,
  canonicalizations, Frobenius applications and fold rotations, relation
  lifts, trivial additions, linear-algebra multiply-subtracts and pivot
  inversions, descent multiplications.
- rho group = `group_additions`; rho unpriced native = canonicalizations,
  partition hashes, table queries and inserts, failed collisions. The
  rho's `scalar_multiplications` are not decomposed by its producer: each
  is priced at both 0 and 2 (53 - 1) = 104 GAE, and every verdict must
  hold at both ends.
- Reported, not priced (inside a priced kind): IC scalar multiplications
  (their doublings and additions are counted), linear-algebra row
  eliminations (a grouping of the multiply-subtracts), field operations.

Read-outs: each arm's mean cost at each weight; the gap S / rT and P / rT
at each weight with a paired bootstrap 95% interval over the 20 points
(10,000 draws); and for each pair of arms either a ranking (the same order
at every weight and both rho bounds, with every interval excluding 1) or
"unresolved at that boundary". Sensitivity, reported beside it and never
instead of it: Frobenius applications priced at 1 GAE as group operations.

## What this does not do

- It does not touch the frozen producer, its binary or any archived
  receipt, and it measures no new speedup.
- It counts the stacked producer (the stacked row and B's lineage). The
  current n = 83 baseline row is the rank-finder producer
  (`koblitz-n83-rankfinder-20261021`), a later derivation of this source;
  its band needs the same counters ported to that derivation and its own
  run. Until then this run gives the band for the stacked row only.
- Wall time is recorded by the runner and not read.

## Outputs

The workflow uploads `host-class.json`, the build, restore and pin
receipts, the panel (`runs.jsonl`, per-run stdout / stderr,
`runner_start.json`), `counts.json` (the band input), `opcounts_result.json`
and `band.md`. Archiving them into this directory, and any update to
`docs/ic/baselines.json`, is a separate commit.
