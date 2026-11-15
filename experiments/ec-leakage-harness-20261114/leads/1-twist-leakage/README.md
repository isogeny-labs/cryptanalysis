# Lead 1: Twist leakage in x-only scalar multiplication [pcc:unverified]

Everything below is from this session's own run (seed values given per
control). No independent verifier has checked these numbers yet; cite as
`[pcc:unverified]`. This is a known attack (the classic invalid-point /
invalid-curve attack applied to an unvalidated x-only Montgomery ladder) —
the deliverable is a working, debugged demonstration in this harness plus a
smoothness census, not a novelty claim.

## Question

`f(k) = x([k]P)` via an x-only (Montgomery) ladder accepts any field element
as `x`. The ladder's xDBL/xADD recursion for a Montgomery curve
`B*y^2 = x^3 + A*x^2 + x` depends only on `A`, never on `B` — so the same
ladder code computes correctly whether the input `x` lies on the curve
`E = M_{A,1}` or on its quadratic twist `E' = M_{A,d}` (any fixed
non-residue `d`), without ever checking which. If `E'` has smooth order,
feeding the ladder x-coordinates of small-order points on the twist leaks
`k mod q` for each small factor `q` of the twist order, via Pohlig-Hellman,
even when `E` itself has (near-)prime order. Does this recover `k` in
practice, and does it fail on a twist-secure curve?

## Preregistration

- **Prediction.** On a curve built so the twist order is `B`-smooth
  (`B = 2^16`), the attack recovers the secret scalar `k` completely via
  CRT across the recovered small-factor residues plus a short search. On a
  twist-secure control curve (twist order has a large prime factor), the
  same procedure recovers correct residues mod the few available small
  factors but **cannot** complete the recovery of `k` because the CRT
  modulus is too small relative to `n` (search space `n/M` in the millions).
- **Kill criterion.** If the recovered Pohlig-Hellman residues do not match
  `k mod q_i` exactly on the weak curve, the implementation is wrong — debug
  before reporting.
- **This kill criterion fired twice during development** (see Caveats /
  implementation bugs below) and both bugs were found and fixed before any
  result was reported.

## Method

1. **Curve construction** (`search_curves.py`). Montgomery form is required
   because the x-only ladder's B-independence is a property of that
   parameterization specifically (a general short-Weierstrass twist rescales
   the x-coordinate, which does *not* match this property — see Caveats).
   For a 40-bit prime `p`, search random `A` until `#E(F_p) = 4*q` with `q`
   prime (Montgomery curves `y^2=x^3+Ax^2+x` always have `4 | #E`, exactly
   like Curve25519's cofactor 8 and X448's cofactor 4 — this is forced by
   the curve shape, not a choice). Twist order `t = 2p+2-#E` is computed via
   PARI (`cypari2.ellcard`) and fully factored via PARI (`factor`).
   - **weak** curve: accept when `t` is fully `B`-smooth (`B = 2^16`).
   - **secure** curve: accept when `t` is *not* fully `B`-smooth (has a
     prime factor `> B`) — the realistic twist-secure case.
2. **Unvalidated x-only ladder** (`attack.py:ladder`). RFC 7748-style
   projective Montgomery ladder, `a24 = (A-2)/4 mod p`, operating purely on
   `(X:Z)` — no input validation, no check that `x1` corresponds to a point
   on `E`.
3. **Attack.** For each small odd prime factor `q` of the twist order
   (`q ≤ B`): find an x-coordinate on the twist of order exactly `q`
   (Legendre-symbol test to confirm "not on E", then the ladder itself to
   project a random twist element down to order `q` — no square roots or
   affine arithmetic needed anywhere). Feed that x-coordinate to the
   victim's ladder with the real secret `k`; brute-force the small discrete
   log in the order-`q` subgroup to recover the canonical residue
   `min(k mod q, -k mod q)` (x-only loses the sign, independently per
   factor — see Caveats). CRT-combine residues across factors, trying all
   `2^(#factors)` sign assignments (the sign ambiguity is independent per
   factor since no two small-order points share a y-coordinate reference),
   then verify each CRT candidate `v + j*M` against a real ladder output
   `x([k]P)` from a genuine on-curve base point `P`, up to `n/M` extensions,
   capped at 200,000 verification tries.
4. **Controls.**
   - *Positive*: the weak-twist curve, 5 random secrets (seed 777).
   - *Negative*: the twist-secure curve, 5 random secrets (seed 888), same
     code path.
   - *Repeat* (A/A-style): the weak-twist curve again with a different seed
     (31415) and fresh random staging points, 5 more secrets.
5. **Census** (`census.py`). Over the 60 curves in
   `results/followup_population.json` (20 each of smooth/anomalous/prime,
   short Weierstrass form) and 60 fresh independently-sampled random 40-bit
   curves: compute `t = 2p+2-n` (this identity holds for any Weierstrass
   model, so no Montgomery form is needed for the census) and tabulate the
   fraction fully smooth to `B ∈ {2^12, 2^16, 2^20}`.

## Results [pcc:unverified]

**Found curves** (`curves_found.json`, seed 20261114):

| | p | A | n = #E | twist order t | twist factorization |
|---|---|---|---|---|---|
| weak | 1095770551103 | 945790977153 | 1095771260588 | 1095769841620 | 2²·5·197·6703·41491 (all ≤ 2^16) |
| secure | 767933589691 | 409243423677 | 767932846684 | 767934332700 | 2²·3·5²·11579·**221071** (221071 > 2^16) |

**Positive control (weak-twist curve), seed 777:**

| trial | k | recovered | success | time |
|---|---|---|---|---|
| 0 | 490611254148 | 490611254148 | True | 0.22s |
| 1 | 133114593045 | 133114593045 | True | 0.25s |
| 2 | 340203023575 | 340203023575 | True | 0.45s |
| 3 | 578002174253 | 578002174253 | True | 0.33s |
| 4 | 889822707202 | 889822707202 | True | 0.01s |

**5/5 full recovery.** Used twist factors {5, 197, 6703, 41491}
(M = 273,942,460,405 ≈ n/4), with ≤ 16 sign candidates and a short search of
at most tens of extensions per candidate.

**Negative control (twist-secure curve), seed 888:**

| trial | k | success | used factors | M | n/M (search space) |
|---|---|---|---|---|---|
| 0 | 184729526231 | False | [3, 5, 11579] | 173685 | 4,421,411 |
| 1 | 487044951620 | False | [3, 5, 11579] | 173685 | 4,421,411 |
| 2 | 568474137500 | False | [3, 5, 11579] | 173685 | 4,421,411 |
| 3 | 675173901813 | False | [3, 5, 11579] | 173685 | 4,421,411 |
| 4 | 276891632352 | False | [3, 5, 11579] | 173685 | 4,421,411 |

**0/5 full recovery** — the Pohlig-Hellman residues mod 3, 5, 11579 were
still recovered correctly every time (confirming the attack mechanics are
sound), but the usable modulus M is only ~2.3e-6 of n, leaving a ~4.4-million
candidate search per sign assignment (≥ 200,000-try cap hit every time), so
`k` was not recovered within the capped search budget.

**Repeat control (weak-twist curve, seed 31415, independent staging
points):** 5/5 success — same curve, different secrets and different random
small-order points constructed from scratch, full recovery every time.

**Census, 40-bit curves, fraction of twist orders fully B-smooth:**

| population | B=2^12 | B=2^16 | B=2^20 |
|---|---|---|---|
| followup_population.json (60 curves) | 2/60 (3.3%) | 10/60 (16.7%) | 23/60 (38.3%) |
| — smooth (20) | 1/20 (5.0%) | 2/20 (10.0%) | 4/20 (20.0%) |
| — anomalous (20) | 1/20 (5.0%) | 5/20 (25.0%) | 12/20 (60.0%) |
| — prime (20) | 0/20 (0.0%) | 3/20 (15.0%) | 7/20 (35.0%) |
| fresh random 40-bit (60 curves) | 0/60 (0.0%) | 2/60 (3.3%) | 16/60 (26.7%) |

Plots: `attack_success.png` (recovery rate, positive vs negative control),
`census_smoothness.png` (smoothness fraction vs bound, population vs fresh
sample).

## What this does and does not show

- **Does show**: a correctly-functioning, verified invalid-point/invalid-curve
  attack against an x-only Montgomery ladder that performs no input
  validation, when the curve's quadratic twist has smooth order. Full
  scalar recovery in all 10/10 trials (positive + repeat) at ~40-bit scale,
  with sub-second-to-second runtimes.
- **Does show**: on a twist-secure curve (large prime factor in the twist
  order), the same unvalidated-ladder code path yields Pohlig-Hellman
  residues for only a handful of tiny factors — not enough to make
  exhaustive recovery of `k` tractable (search space in the millions here;
  scales to astronomically infeasible at real key sizes).
- **Does show**: at 40-bit scale, among curves in the existing harness's
  40-bit population, a minority (10/60, 16.7%, at B=2^16) have twist orders
  that are fully smooth to a bound this small; a visibly larger fraction
  becomes smooth at a looser bound (23/60, 38.3%, at B=2^20). Among the
  anomalous-population curves specifically, the smooth-twist rate is
  noticeably higher (25% at B=2^16, 60% at B=2^20) than the fresh-random
  baseline — anomalous curves (#E=p) were not selected for twist structure,
  so this looks like it could be coincidental to this specific
  sample/seed rather than a property of j=0/anomaly; it is reported as an
  observation only, not tested against a null here.
- **Does NOT show**: anything about real-world curve choices at
  cryptographic sizes (256-bit+); standard curves (Curve25519, P-256,
  secp256k1) are specifically vetted to have twist-secure, non-smooth twist
  orders, and this harness's 40-bit toy curves are not representative of
  that vetting process's statistics.
- **Does NOT show**: any new attack, improvement over Pollard rho, or
  improvement over the index-calculus baseline. This is a textbook
  invalid-point attack (Biehl–Meyer–Müller style), reimplemented and
  verified in this harness.
- **Does NOT show**: how the census smoothness numbers would change with a
  different smoothness-search sieve bound, more samples, or a rigorous
  statistical test against the expected smooth-number density (Dickman's
  function) — the census here is a raw tabulation, not a hypothesis test.

## Caveats

- **Two implementation bugs were caught by the preregistered kill criterion**
  during development and fixed before reporting:
  1. An early version of the twist model used the general short-Weierstrass
     twist-coefficient rescaling (`a2' = A*d, a4' = d^2`), which changes the
     x-coordinate of corresponding points (`x' = d*x`) and is genuinely a
     *different* curve model from the Montgomery (A, B)-family twist
     (`B*y^2=x^3+Ax^2+x`, same x-line, only B changes) that the x-only
     ladder actually needs. Using the wrong model made "small-order twist
     points" not actually have the claimed order under the ladder.
  2. The ladder's `a24` constant was initially coded as `(A+2)/4` (a
     plausible-looking but wrong sign); the correct RFC 7748 constant is
     `(A-2)/4`. This was caught by cross-checking `ladder()` output against
     independently-written affine group-law arithmetic on the curve
     (`B*y^2=x^3+Ax^2+x`, implicit-differentiation doubling formula with
     the `B` factor kept explicit) and the closed-form single-doubling
     formula `X2=(x1²-1)², Z2=4x1(x1²+Ax1+1)`; both of the latter are
     independent of the loop-based ladder code and agreed with each other
     but not with the buggy ladder, which pinpointed the bug.
- Curves here use cofactor-4 "near-prime" order (`n = 4q`, `q` prime), as is
  standard for Montgomery curves (Curve25519 is cofactor-8, X448 cofactor-4)
  — not literally prime order, though this is the realistic case for any
  real Montgomery-ladder deployment, not a weakening introduced for this
  demo.
- The per-factor sign ambiguity in the x-only leak (`k mod q` vs `-k mod q`)
  is independent across different small-order points, not a single global
  sign bit, because no y-coordinate or orientation information is ever
  passed between the different points constructed for different factors;
  the search over all `2^(#factors)` sign assignments accounts for this.
- `is_probable_prime` (Miller-Rabin with fixed bases) is deterministic only
  below ~3.3e24; all primes used here (~2^40) are comfortably inside that
  range.
- The negative-control "search space" cap (200,000 tries) is a practical
  budget cap, not a cryptographic hardness proof; it is chosen so the
  negative control finishes in seconds while still being many orders of
  magnitude short of the ~4.4 million candidates needed, consistent with
  the real-world infeasibility this control is meant to illustrate.
- Census numbers are for this harness's specific 60-curve population file
  and one fresh independent sample of 60 curves (seed 20261115); no
  replication across multiple independent samples was done given the time
  budget, so sampling noise on the reported percentages (especially the
  smaller subgroups, n=20) is not small.

## Next step

- Repeat the census at cryptographic sizes (e.g. 128-bit, 256-bit) to check
  whether the smooth-twist rate at B=2^16 or 2^20 falls toward the
  Dickman-function-predicted rate for random integers of that size, as a
  sanity check that nothing in the curve-generation procedure biases toward
  (or away from) smooth twists.
- If the anomalous-vs-smooth-twist-rate observation above is worth
  following up, test it properly: generate many more anomalous curves (fresh
  seeds) and a matched-size random-curve null, and run a controlled
  comparison (binomial or permutation test) rather than reporting the raw
  counts from one run.
- Extend the attack beyond the recoverable modulus `M` using a slightly
  smoother curve (or combining several moderately-smooth curves/subgroups)
  to see how large `M/n` needs to be in practice for the short search to
  stay tractable, mapping out the "near miss" boundary between the two
  controls shown here.
