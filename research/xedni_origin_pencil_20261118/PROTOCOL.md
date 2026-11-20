# Prospective target-origin-pencil Xedni protocol

Date: 2026-11-18

Status: prospectively specified before implementation or natural outcomes.  No
natural row may be generated until this protocol, the runner, analyzer, source
hashes, release-binary hash, master seed, and `FREEZE.json` are committed and
the repository resume-checkpoint gate passes. [pcc:unverified]

## Correction and research question

A chord-origin change is a coefficient-coordinate change, not a new source of
relations.  If `n` is a relation with chord origin through endpoints `u,v`,
and `S = sum(n)`, its coefficients in the fixed flex-origin group are

```text
r = n + S e_u + S e_v,                 sum(r) = 3 S.
```

Conversely, a fixed-origin vector whose coefficient sum is divisible by three
has the unique chord-origin representation

```text
n = r - (sum(r)/3) e_u - (sum(r)/3) e_v.
```

When `u` is the designated target, the fixed-origin target coefficient is
therefore `r_u = n_u + S`.  This is the effective target coefficient used for
recovery.  In particular, changing origins cannot turn a fixed-origin relation
with target coefficient zero into one carrying target information.
[pcc:unverified]

The useful bounded-search consequence is different: an `d`-coordinate box
`|n_i| <= B` maps to endpoint coefficients as large as `(d+1)B`, because
`|S| <= dB`.  This experiment asks whether the union of target-dependent
chord-origin boxes finds exact target-bearing relations missed by one fixed
known-only origin box on the same lifted cubic. [pcc:unverified]

## Paired algorithms

Each row constructs exactly one source instance and one optimized lifted
cubic using the frozen November 17 path.  It designates the final lifted point
as target and preserves the frozen coefficient bound `|n_i| <= 2`, auxiliary
prime selection, exclusions, and exact group checks. [pcc:unverified]

The baseline is the already-frozen target-first selector at the deterministic
known-only chord origin.  It orders that origin's auxiliary-field candidates
by `(effective coefficient not invertible modulo source order, L1, vector)`.

The candidate searches a pencil consisting of the baseline origin plus every
admissible chord origin through the target and one non-target lifted point.
Auxiliary candidates are tagged by origin, then globally ordered by
`(effective coefficient not invertible modulo source order, L1, origin tag,
vector)`.  For a target-origin tag the effective coefficient is `n_target +
sum(n)`; for the baseline tag it is obtained by the general transport formula
to the fixed origin.  Every candidate is exact-checked in its own group law.
The first exact relation is transported to fixed-origin coefficients and
independently replayed against the source multipliers. [pcc:unverified]

The candidate arm includes the complete baseline candidate set.  It may not
change the lift, coefficient bound, auxiliary prime, admitted points, or
source instance.  Work accounting charges construction of every origin table,
every modular candidate, every exact candidate check, every transport, and
the final source replay. [pcc:unverified]

## Fresh panel and budgets

The master seed is `xedni-origin-pencil-20261118-v1`.  The prospectively fixed
grid is primes `{31,67,127,251}`, curve families `{generic,j0}`, coordinate
lifts `{balanced,wide}`, ranks `{6,7,8,9}`, and 25 trials per cell: 1,600
paired rows.  Execution is sequential with a 7,200-second external cap.
Every row and failure is retained. [pcc:unverified]

The exact post-freeze commands will be:

```sh
timeout 7200 python3 research/xedni_origin_pencil_20261118/runner.py run \
  --binary suite/target/release/ca-icx \
  --output research/xedni_origin_pencil_20261118/run/rows.jsonl \
  --master xedni-origin-pencil-20261118-v1 \
  --primes 31,67,127,251 --families generic,j0 --lifts balanced,wide \
  --r-values 6,7,8,9 --trials 25
python3 research/xedni_origin_pencil_20261118/analyze.py \
  research/xedni_origin_pencil_20261118/run/rows.jsonl \
  research/xedni_origin_pencil_20261118/run/summary.json
```

## Estimands and decision boundary

Primary counts are paired correct target recoveries among valid rows, overall,
by rank, and by full cell.  Secondary measurements are relations certified,
origins admitted, modular candidates, exact checks, transports, source
replays, and wall time per arm.  Fixed controls must prove the coefficient
transport identities, exhibit the existing zero-explicit-target chord
relation with nonzero effective coefficient, and show that a zero
fixed-origin target coefficient remains zero under target-origin transport.
[pcc:unverified]

A stage-level improvement requires at least one candidate-only recovery, zero
baseline-only recoveries, no lift/certificate/source-replay failures, and
complete work accounting.  The report must state the exact gain and added
work.  This is not an end-to-end ECDLP breakthrough: such a claim still needs
a named complete pipeline, all phases, fresh single targets, matched Pollard
rho, independent scalar replay, and the repository measurement gates.
[pcc:unverified]

## Execution gate and sources checked

The 2026-11-18 checkpoint attempt reached the configured S3 `PutObject` after
local self-tests and immutable-source verification, but the bucket returned
`AllAccessDisabled`.  Therefore this protocol may be implemented and frozen,
but no natural panel may run until transport is restored and the exact
checkpoint gate passes. [pcc:unverified]

- `LEAD-ICP-char0-lifting-xedni-smoothness`: closed-known; revisit only after
  a certified bounded dependent lift. [pcc:unverified]
- `KR-IC-cd159a`: classical negligible-probability obstruction; the bounded
  pencil does not remove it. [pcc:unverified]
- `LEAD-TRF-global-lift-small-height`: closed-known global-lift direction.
  [pcc:unverified]
- `LEAD-EXO-global-lift-height`: open height-control successor; this bounded
  coordinate-coverage test is narrower. [pcc:unverified]
- `crypto-autoresearcher:analysis/xedni-cheon/20261007-certificates/REPORT.md`:
  earlier two-point-lift baseline and bounded-search null. [pcc:unverified]
- The shared research-KB wrapper was checked, but no executable is available
  in this environment; the lead atlas and cited repository records are the
  documented fallback. [pcc:unverified]
