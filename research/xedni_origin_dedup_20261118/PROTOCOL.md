# Prospective fixed-coordinate deduplication of the Xedni origin pencil

Date: 2026-11-18

Status: prospectively specified after the deterministic overlap control and
before implementation or natural outcomes. No natural row may be generated
until this protocol, runner, analyzer, source hashes, release-binary hash,
master seed, and a separate `FREEZE.json` are committed and the repository
resume-checkpoint gate passes. [pcc:unverified]

## Question

The full target-origin pencil constructs 99,622 origin-local modular
candidates but only 25,694 distinct fixed-coordinate vectors on its retained
nine-point control. This protocol tests the cost optimization suggested by
that aliasing: after applying the already-frozen global ordering, retain only
the first (therefore best ordered) representative of each fixed-coordinate
vector before exact characteristic-zero checks. [pcc:unverified]

This arm does not assert new relation information and does not choose origins
from observed natural outcomes. It constructs every origin table and every
modular candidate exactly as the full pencil does, transports all candidates,
and charges all of that work. It can save only duplicate exact checks and
their associated group-law work, plus later source replays if an
implementation performed those redundantly. [pcc:unverified]

## Paired algorithms and semantic invariant

Each row reconstructs the same source instance and optimized lift used by the
frozen full-pencil protocol. The reference arm is the full pencil with global
priority

```text
(effective target coefficient noninvertible, local L1, origin index, vector).
```

The dedup arm builds that identical ordered list, then keeps the first row for
each transported fixed coefficient tuple. It exact-checks retained rows in
their own origin group. A selected row must pass source replay and a separate
baseline-chart exact check. [pcc:unverified]

For every row, the runner records the ordered full digest, ordered retained
digest, first-representative mapping digest, total and unique fixed vectors,
duplicates removed, construction/transports/hash probes/exact checks/source
replays, memory-relevant peak retained entries, and diagnostic wall
nanoseconds. Wall values are ordinary host diagnostics rather than isolated
timing evidence. [pcc:unverified]

The semantic invariant is exact equality of full-pencil and dedup selected
fixed coefficients, recovered target, and success status. A mismatch is an
implementation or geometric-transport failure, never an optimization win.
The deterministic control additionally exact-checks every alias class and
requires exactness to be constant within each class. This audit is a control
cost and is not included in the optimized arm's claimed work. [pcc:unverified]

## Fresh panel and execution gate

The master seed remains `xedni-origin-pencil-20261118-v1` so this is a paired
algorithm comparison on the exact same prospectively fixed source instances,
not a post-hoc sample. The grid remains primes `{31,67,127,251}`, families
`{generic,j0}`, lifts `{balanced,wide}`, ranks `{6,7,8,9}`, and 25 trials per
cell: 1,600 paired rows. Execution is sequential under a 7,200-second external
cap, and every row/failure is retained. [pcc:unverified]

The exact commands will be frozen after implementation. The mandatory
checkpoint currently has no supported upload transport. Therefore only
source, formalization, and deterministic controls may proceed; no natural row
may be generated until `scripts/checkpoint.sh gate` exits zero without a
bypass. [pcc:unverified]

## Decision boundary

A valid optimization result requires all 1,600 rows, zero semantic mismatches,
zero certificate/source-replay/internal failures, identical full candidate
digests to the frozen pencil construction, and strictly fewer aggregate exact
checks. The report must include modular construction, transport, hashing,
memory, and wall diagnostics, not only exact-check savings. Equality or higher
complete work is a null optimization. [pcc:unverified]

Even a valid stage optimization is not an end-to-end ECDLP improvement. It
still requires the full pencil to produce a target-recovery advantage, and a
complete pipeline must beat matched Pollard rho with all phases and
independent replay. [pcc:unverified]

## Sources and controls

- The prospectively frozen parent protocol and runner in
  `../xedni_origin_pencil_20261118/`.
- The reproducible deterministic overlap decomposition in
  `../xedni_origin_pencil_20261118/COVERAGE_CONTROL.json`.
- Jacobson, Koblitz, Silverman, Stein, and Teske, “Analysis of the xedni
  calculus attack,” *Designs, Codes and Cryptography* 20 (2000), 41–64.
- The open checkpoint blocker in
  `../../problems/xedni-affine-cvp-checkpoint-access.md`.

These sources motivate a cost optimization only. The retained control does
not estimate natural recovery frequency or authorize partner selection.
[pcc:unverified]
