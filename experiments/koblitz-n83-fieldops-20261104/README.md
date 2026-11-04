---
title: "n = 83: inlined field operations, exact changes only (Tier 1 design)"
date: 2026-11-04
---

# n = 83: inlined field operations, exact changes only (Tier 1 design)

**Status (2026-11-04): frozen design, run pending.** The design sections below
are frozen before any timing on the Tier 1 runner. Every profile figure in
them comes from the shared cloud-agent VM; those figures are local
diagnostics, used only to rank candidates and size the design. The result
section is added with the archived receipt.

## Why this run

The n = 83 a = 1 baseline row is the **rank-finder producer**
(`koblitz-n83-rankfinder-20261021`, on main, run 39527997793, frozen
`rankfinder_source_sha256` `301615b3...`). In that run its end-to-end cold
cost was **3.924x** the matched rT770 rho (point estimate; online 0.0933x).
That gap is the distance remaining `[pcc:unverified]`. Side B of that run
(this run's side A) spent, per process (medians over the run's rows, ms):

| stage | ms |
| --- | ---: |
| root-index build (cold process) | 3,231 |
| full scan-order self-test | 840 |
| online, one target | 193 |
| base load | 176 |
| rank stage (rank process) | 2,528 |

So the cold path is setup-bound. A local Callgrind profile of side A's cold
process (this VM, `--cache-sim=yes`) puts **21.7%** of all instructions in
`Gf2_128::mul` and its callees, and the rank process **25%**
`[pcc:unverified]`. The library's product calls `clmul_u64`, which is not
`#[inline]` and lives in the library crate, out of line six times per product:
about 150 instructions per GF(2^83) product. Round 2's rejected candidate C8
(`koblitz-n83-indexbuild2-20261020`) enabled the carry-less multiply in the
producer's state loop, but that cannot inline a non-`#[inline]` function of
another crate, so C8 never removed those calls.

## 1. The change and its proof

Side B's producer is derived from side A's by `make_fieldops_source.py`:
counted, exact edits plus one counted call replacement inside `mod wide`
(57 products and 24 squarings). `check_inverse()` undoes every edit back to
side A's bytes. None of them changes what is computed:

- **F1, inlined field products and squares** (`fast_field`, `fmul`, `fsqr`).
  The same polynomial product (four carry-less 64 x 64 products; the
  library's Karatsuba uses three, and both form the one product of the two
  polynomials) and the library's two folds by the tail t = irr - z^n,
  statement for statement. A reduced field element is unique, so every
  product and square is the library's. Side B is built with
  `-C target-feature=+pclmulqdq` (`online-b/.cargo/config.toml`).
  `fast_field::check` runs before any use and fails closed. It checks that the
  CPU has the instruction, that the field meets the library's fold
  conditions, and that the inlined product and square equal the library's on
  edge cases and 65,536 pseudo-random pairs.
- **E1, the state loop's three squarings by the inlined square.** The table
  map `solver.square` is the GF(2)-linear map with images `gf.sqr(e)` of the
  unit vectors, so it equals squaring on every element. Its 45 KB of tables
  leave the state loop.
- **E2, byte-image lookups in every linear map** (`Linear128::apply`). The
  same eleven lookups of the same tables, the bytes read from
  `v.to_le_bytes()`.
- **S4, the scan self-test evaluated from per-round tables** (`RoundTables`).
  `apply` calls `round(right, key)` only with right < 2^half, so table r
  holds `round(v, keys[r])` for every v < 2^half, filled by `round` itself.
  The table-evaluated `apply` is `apply` on every index. The self-test makes
  the parent's three checks of the same function over the same domain in the
  same order, with the parent's eight-image loop.

The appended test module `fieldops_tests` (run by the workflow's
`cargo test --bins`) checks these equalities:

- the inlined product and square against the library on all 2^20 pairs of a
  1,024-element sample;
- the square map against the inlined square on 2^18 elements;
- the byte-image lookup against the parent's shift loop for all four maps;
- the table permutation against `apply` on every index of the M38 and M10
  domains, for both self-test keys.

## 2. Candidates and local ranking (diagnostic)

Ranked on this VM: alternating fresh pinned processes of side A and the
candidate, the M38 base and point Q0. Layout, index, relation and probe
identities were compared on every run.

| candidate | local effect (B/A) | status |
| --- | --- | --- |
| F1 alone | index build 0.954 | in the stack |
| F1 + E1 | index build 0.903 | in the stack |
| F1 + E1 + E2 | index build 0.884, rank stage 0.84, online 0.79 | in the stack |
| S4 (microbenchmark of the self-test alone) | 0.65 | in the stack |
| nibble tables (5.4 KB per map) instead of E2 | index build 0.97 | rejected (E2 better) |
| self-test with the marks bucketed by image | 1.2 | rejected (slower) |
| self-test with images computed ahead and their bitmap words prefetched | 1.25 | rejected (slower) |

The frozen stack against side A, from `inputs/local_profile.json`: four
alternating cold rounds and three rank rounds. The rank rounds used the first
side-B build, whose rank-stage code is the frozen one.

| stage | side A (ms) | side B (ms) | B/A |
| --- | ---: | ---: | ---: |
| index build | 6,575 | 5,609 | 0.853 |
| scan self-test | 1,410 | 1,277 | 0.906 |
| online | 685 | 537 | 0.784 |
| rank stage | 4,750 | 4,424 | 0.931 |

The first side-B build computed the self-test's round count with a runtime
division and ran the self-test slower (1.15). The frozen derivation iterates
a fixed array of four tables. Every run reproduced side A's stored-state,
slot-layout, logical-state and table-map digests, and every rank run
reproduced its relation digest, per-attempt probe vector and root calls.

## 3. Not in scope

The index keys' linear run finder (about 14% of the cold process's
instructions, now the largest non-field cost of the build) and the root
table's layout are unchanged. So are the probe loops, the rank-stage
algorithm, the factor base and the self-test's predicate.

## 4. Frozen design

The design, pairing, bootstrap, A/A control, Tier 1 records and fail-closed
verifier are the parent's (`protocol.json`, `verify_receipt.py`):

- **Panel:** 12 new held-out points (`inputs/cold_targets.json`, disjoint from
  every earlier n = 83 panel: `inputs/panel_disjointness.json`).
- **Pairs per point:** three alternating primary pairs, two A/A pairs, one
  planted pair and one tuned-rho process.
- **Rank seeds:** 2101-2136, new on n = 83 (`inputs/seed_disjointness.json`).
- **Primary:** R = sum E2E(A) / sum E2E(B) over the 36 primary pairs, with
  E2E = rank stage + cold.
- **Decision:** improvement iff the 95% two-stage paired bootstrap lower bound
  of R exceeds 1 `[pcc:unverified]`.

Arms:

- **Side A** (the row, `online/`, built as landed): kM38RF + cM38RF.
- **Side B** (`online-b/`, +pclmulqdq): kM38FO + cM38FO.
- **A/A:** B against kM38FOaa + cM38FOaa.
- **Planted:** cold pairs cM38FO / cM38FOX. cM38FOX uses
  `KIC_INDEX_CANON=lift_plant`, so every index key is also checked against
  lift_scan. Its layout digests are unchanged and its index build is slower.
- **Q0:** run on K600, M10 and M38 by both producers.

The gates are the parent's plus one. Every IC row's summary must name its
arm's `field_ops_pipeline`: absent on side A's binary, and
`fmul_clmul_inline+sqr_clmul_inline+state_square_clmul+maps_le_bytes+selftest_round_tables`
on side B's.

## 5. Power and runtime

`power_check.py` (`analysis/power.json`) uses the parent's run as the prior
and the four local stage factors as the modelled cell. It gives:

| quantity | value |
| --- | --- |
| expected R at the prior means | 1.12 |
| power at a 1.01 effect | 0.975 |
| type I error at 1.00 | 0.0075 |
| A/A point estimates inside [0.97, 1.03] | every time |
| planted control detected | every time |
| modelled schedule | about 31 min |
| modelled job | about 50 min |

## Local smoke of the frozen schedule

`run_schedule.py --one-per-arm` on this VM ran the first process of every arm
in every segment through `arm.py`'s gates: 102 processes, all valid and
verified, none with an issue `[pcc:unverified]`. The verifier passes every substantive gate on
that partial receipt (`smoke/README.md`, `inputs/local_exactness.json`). The
crate tests of `online-b` pass, 38 of 38.

## Trigger

`.github/workflows/n83-fieldops.yml`, on a push to `claude/n83-fieldops`
restricted by path filters, as the parent's (`workflow_dispatch` is refused
for this integration). It clones crypto 770f6a69 from the public
`isogeny-labs/crypto`.

## Result

Pending.

## Files

- **Derivation:** `make_fieldops_source.py` (side B), plus the parents' chain
  (`make_rankfinder_source.py` and earlier, verbatim).
- **Crates:** `online/` (side A and the tuned rho) and `online-b/` (side B,
  `.cargo/config.toml`).
- **Experiment scripts:** `restore.py`, `make_targets.py`,
  `check_panel_disjoint.py`, `check_seed_disjoint.py`, `make_power_prior.py`,
  `power_check.py`, `make_protocol.py`, `make_schedule.py`, `run_schedule.py`,
  `arm.py`, `verify_receipt.py` and `test_verify_receipt.py`.
- **Local diagnostics:** `profile/run_cold.sh`, `profile/run_rank.sh`,
  `profile/raw/` and `inputs/local_profile.json`.
