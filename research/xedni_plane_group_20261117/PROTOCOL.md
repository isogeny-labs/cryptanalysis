# Full-rank Xedni plane-cubic relation trial protocol

Date: 2026-11-17

Status: prospectively specified; no outcome rows may be generated until the
runner, analysis, digests, and `FREEZE.json` are committed and the repository
checkpoint gate passes. [pcc:unverified]

## Question

Can the ten-coefficient Xedni lift with `r` in `{7,8,9}` produce an exact
rational dependence that survives a source-faithful chord-origin reduction,
and does the per-trial success rate show a materially different scaling from
the frozen `r=3..6` sweep? [pcc:unverified]

## Required construction

Each trial must generate its source curve, base point, target logarithm,
known multipliers, and coordinate lifts before inspecting any rational
relation outcome.  It must solve all ten cubic coefficients in the prescribed
residue class, optimize the same affine coset with the existing exact Xedni
optimizer, and retain every reject and cap exhaustion. [pcc:unverified]

The lifted origin is selected by enumerating known-multiplier point pairs in
lexicographic index order and taking the first chord residual that is distinct
from every selected point.  If the selected pair has multipliers `m_j,m_k`,
the relation search may still use all `r` points.  Every candidate relation
must be verified twice by exact projective group arithmetic and must satisfy
`sum n_i(m_i+m_j+m_k)=0 mod ord(G)`.  Target recovery is counted only when the
target coefficient is invertible and the recovered scalar equals the planted
scalar. [pcc:unverified]

## Controls

The runner must pass deterministic positive controls for a nine-point planted
curve, a non-flex chord origin, shifted source-relation recovery, mutation
rejection, a singular cubic, and an off-curve origin.  It must also compare
the plane-cubic arithmetic with the existing rational Weierstrass arithmetic
on models where both apply. [pcc:unverified]

## Fixed panel and budgets

The master seed is `xedni-plane-r6789-20261117-v1`.  The prime panel is
`{31,67,127,251}`, curve families are `{generic,j0}`, coordinate-lift laws are
`{balanced,wide}`, and `r` is `{6,7,8,9}`.  `r=6` is an internal
same-implementation control; the new target regime is `r=7..9`.  Each of the
64 cells has 25 trials, for 1,600 scheduled rows. [pcc:unverified]

Curve pools and source instances use the deterministic laws inherited from
`research/xedni_lift_success_20261112/sweep.py`, pinned by SHA-256 in
`FREEZE.json`.  The new runner is `sweep.py`.  The coefficient box is
`|n_i|<=2`; auxiliary search primes are `2^61-1`, `2^89-1`, and `2^107-1`;
the affine optimizer uses radius one and at most `3^(10-r)` exact objective
evaluations.  The run is sequential and has a 1,800-second external cap.
[pcc:unverified]

Rows with statuses `small_order`, `no_point`, `identity`,
`no_integer_solution`, or `rank_deficient` are reported and excluded from the
`ok` denominator.  Any certificate, group-arithmetic, or subprocess failure
is reported and counts as a pipeline failure, not an exclusion.  Cap expiry
leaves a censored suffix and is not interpreted as zero success.
[pcc:unverified]

The exact reproduction command after the freeze and checkpoint gate is:

```sh
timeout 1800 python3 research/xedni_plane_group_20261117/sweep.py run \
  --binary suite/target/release/ca-icx \
  --output research/xedni_plane_group_20261117/run/rows.jsonl \
  --master xedni-plane-r6789-20261117-v1 \
  --primes 31,67,127,251 --families generic,j0 --lifts balanced,wide \
  --r-values 6,7,8,9 --trials 25
python3 research/xedni_plane_group_20261117/analyze.py \
  research/xedni_plane_group_20261117/run/rows.jsonl \
  research/xedni_plane_group_20261117/run/summary.json
```

The primary estimands are certified exact relations and correctly recovered
target logarithms among `ok` rows, reported by `r` and by full cell.  The
necessary finite-field relation rate is also reported.  This toy feasibility
panel does not fit an asymptotic slope or support a timing claim.
[pcc:unverified]

## Decision boundary

A certified `r=7..9` relation with correct shifted target recovery is an
implementation and feasibility success.  Zero certified relations is the
bounded null.  Any certificate failure invalidates the affected result and
requires repair before interpretation.  A research lead still requires a
fresh larger panel whose success-rate scaling or complete charged work
materially improves on the existing baseline; a large ECDLP-breakthrough
claim additionally requires matched end-to-end comparison with Pollard rho
and independent verification. [pcc:unverified]

