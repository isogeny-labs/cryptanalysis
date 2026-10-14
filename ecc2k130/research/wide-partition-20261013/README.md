# Wide-partition rho: raising the branch count of the ECC2K-130 walk

## The technique

The shipping iteration function is the orbit-equivariant Koblitz walk

    R' = R + sigma^j(R),    j = 3 + ((HW(x_R) >> 1) & 7),

with eight branches. Every per-step optimization in this repository keeps that
eight; the branch count itself has never been measured. It is an r-adding
walk, and the expected number of iterations to a collision carries the r-adding
penalty of the branch count (Teske, *On random walks for Pollard's rho
method*): walks with few branches mix slower, and the collision time carries a
constant above the ideal random-map value that shrinks as r grows.

The proposal: raise r to 16 or 32, j = 3 + ((HW(x) >> 1) & (r-1)), so the walk
mixes faster and the expected iterations-per-collision falls, at a marginal
kernel cost that is close to zero because:

* HW stays the branch selector, so the walk remains constant on
  {+/- sigma^a(R)} orbits and the quotient-walk argument of codegen/cycles.py
  is unchanged — sigma^a(+/- R) maps to sigma^a(+/- R') for every widened j,
  and no fruitless-cycle machinery is added.
* The extra branch values cost one more Frobenius composition on part of the
  steps. sigma^(3+b) for b >= 8 is the b&7 network composed with sigma^8,
  and sigma^8 is a fixed index permutation — ALU work that co-issues under
  the CLMAD-bound kernel (the ALU pipe runs at 36-39% while carry-less is at
  63-71%, ONE-BLOCK-GEOMETRY.md 6).

The multiplier view makes the mechanism explicit: on the order-ell subgroup
the step is R -> [1 + lambda^j] R, so the walk in exponent space multiplies by
(1 + lambda^j) drawn from the branch set. Eight multipliers mix the exponent
slower than sixteen; the birthday constant over the 2m = 262 orbits is what
the campaign pays for.

## Outcome (2000-trial panel, see RECEIPT.md)

The walk-quality gate **failed**: widening the branch count does not reduce the
expected work of this walk family.

| config | mean fleet work to first cross-walk collision | ratio vs shipping | 95% CI |
| --- | --- | --- | --- |
| r8-shift (shipping rule) | 327.8 | 1.000 | — |
| r16-shift | 338.1 | 1.032 | 0.999–1.065 |
| r16-plain (HW mod 16) | 354.3 | 1.081 | 1.048–1.116 |
| r8-ideal (orbit-key selector) | 327.2 | 0.998 | 0.968–1.030 |
| r16-ideal | 322.3 | 0.983 | 0.953–1.015 |

Three readings:

1. **The shipping selector is already ideal-quality.** An orbit-key
   selector — a perfectly balanced, perfectly mixed branch function — gains
   nothing at r = 8 (0.998) and 1.7% (not significant) at r = 16. The
   r-adding penalty Teske measures for walks with few branches does not
   manifest here: lag-1 branch autocorrelation is within ±0.02 for every
   config, and the HW(x)/2 partition is effectively uniform at the cells
   that are live.
2. **Widening the HW-based rule is neutral to harmful.** (HW>>1) mod 16
   is +3.2% (tail-driven; medians identical); HW mod 16 is +8.1%
   significant, driven by 4754 self-cycle restarts in 2000 trials — the
   plain form creates genuinely shorter rho cycles. At m = 23 the HW range
   truncates below 2r, which exaggerates this, but the ideal-selector
   controls rule out the mechanism by which full-range widening at m = 131
   would have helped.
3. **The structural excess is real and lives elsewhere.** Every config,
   including ideal selectors, measures ~1.2x the iid birthday bound
   sqrt(pi*M/2) = 267.5 for the fleet's first cross-walk collision. That
   excess is a property of the step map's orbit transition — R + sigma^j(R)
   does not induce a uniform transition on x-orbits — and no branch rule
   fixes it. This ~20% is the honest target for a future walk-quality
   technique, and it is not addressable by widening.

The widened exponent sets are cycle-clean where it matters: at m = 131, no
multiset of up to 5 step multipliers multiplies to +/- lambda^i (0 hits,
0.000 expected by chance), and no sigma^j(R) = +/- R degeneracy exists for
j in 3..34. At m = 23 the widened sets carry 13 and 243 excess short-cycle
hits against 1.6 and 60.6 expected by chance — m = 23-coincidences in a
2^21 subgroup, consistent with its size.

## What is measured here

`walk_quality.py` is the empirical panel on the client's own GF(2^23) test
curve (same field, basis, and walk form as the generated eccF23
configuration):

1. **Work to first orbit repeat** for r in {8, 16, 32} against an
   ideal-branch control (branch = orbit key mod r, a perfectly mixed
   orbit-invariant selector), single-walk runs, N trials, bootstrap
   confidence intervals on the ratios.
2. **Partition balance**: the cell probabilities of (HW >> 1) mod r and
   HW mod r under HW ~ Binomial(m, 1/2), exact and sampled, because the
   m=23 branch range truncates below 2r.
3. **Short-cycle recheck inputs**: the widened exponent sets {3..18} and
   {3..34} for codegen/cycles.py (a step-multiplier product equal to
   +/- lambda^i would create a cycle; the eight-branch set is checked there
   today).

The m=23 panel bounds what m=131 gains: at m=23 the branch range truncates
(HW <= 23), so widened r is tested with a partly-collapsed partition — the
measured gain is a lower bound on the full-range m=131 gain.

## Gates

* Walk quality: r=16 or r=32 mean work-to-repeat below the r=8 mean by more
  than twice the bootstrap half-width of the ratio, with the ideal control
  bracketing the result from below.
* Kernel: a widened build screens within 2% of the control rate on one
  RTX PRO 6000 allocation (paired alternating runs, same discipline as
  TUNING.md), and the reference walk replay (host scalar) is byte-identical
  on records.
* Identity: a widened walk is a new campaign identity; records never merge
  with the 8-branch tables (DP-RECONCILIATION.md rule).

## Files

* `walk_quality.py` — the panel; run `python3 walk_quality.py --trials 400`.
* `RECEIPT.md` — written by the run with its configuration and results.
