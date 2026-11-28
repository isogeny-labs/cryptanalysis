# Norm-one torus factor-base M31 screen

Question: with the same 384 base columns and signed m2 pair-index algorithm,
does a norm-one torus x-trace fiber produce more useful first-witness graph
rows or cheaper cold solves than an interval base or a size-matched random
base? The torus construction is already in `FactorBase::torus`; this screen
does not propose a new curve transport or a new asymptotic relation law.

Prior work checked: the repository's `FactorBase::torus` construction and
`m31-fast` path, `m31-full-rust-comparison` explicit-pair collector, and KB
source `source:703208c6bf5a5d11e00b1310f71bf07f` (which points to mean-yield
conservation and previous auxiliary-base accounting). The KB revision was
`0ebe094eb6054cb8ae9da01c6a8f25c4`, last refreshed 2026-11-25; inspect
newer local work directly. Equal base size alone does not imply equal pair
sum diversity or row-rank trajectory, so preserve these counters.

Use `m31-fast` at source commit `48306253e` with the five previously
published public M31 targets in `fresh-public.json`, seeds 0,1,2, m2,
384 columns, 64 lanes, 4M query and 5s online caps. The three IC arms are
`--base interval`, `--base torus`, and `--base random --base-seed 1`; include
the archived C++ rho on each same target/seed. Each arm is a fresh process
with 20s deadline. Rotate arm order within each block, shuffle blocks with
seed 2026112748. Compile before timing. Charge parent-plus-child CPU and wall
from before process launch through exit, result parsing and independent public
group-equation verification. Basis generation, index construction, relation
search, elimination and certificate replay remain inside. Preserve failed,
incomplete and censored arms, and never infer a scalar from an incomplete
arm. Report basis digest, torus depth, pair entries, queries, relations,
rank and phase times. OS caches and other host load are uncontrolled.

Pilot gate: first run target 0, seed 0 for the three IC arms. Proceed to the
full 60-arm panel if all three solve within their caps and torus charged CPU
is within 2x interval; otherwise record the pilot and investigate that exact
failure or cost. A performance-breakthrough claim requires same-target torus
to beat interval, random and rho in charged wall and CPU on at least four of
five target-level medians, plus rigorous proof of any new mathematical claim.
