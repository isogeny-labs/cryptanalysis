# Blind review A: centered Nat interval

## Scope and sources_read

- Read only `/tmp/cryptanalysis-hasse-center-20261027/reports/hasse-interval-bridge-20261027/blind-brief.md` as task material.
- Read no Lean or Nat documentation. I used elementary arithmetic and an independently written bounded Python enumeration; the enumeration read no task files.
- I did not read the review plan, Lean source or proof, proof map, README, receipts, sibling reports, or parent conversation, and did not edit the repository. **Forbidden-access attestation:** none of those forbidden materials was accessed.

## joints_owned

1. Convert the two centered interval memberships into both directed separation bounds, in particular `m ≤ n + 2*radius`.
2. Use positivity of `r` and separation of distinct natural multiples: if `k < l`, then `k*r + r ≤ l*r`.
3. Cancel `n` to contradict `2*radius < r`.
4. Check satisfiability, zero boundaries, and exact sharpness of the strict inequality.
5. State the additional facts needed before applying this Nat result to an elliptic-curve order.

## Verdict and independent derivation

**Holds.** Write `R = radius`. The assumptions `m ≤ center + R` and `center ≤ n + R` yield

`m ≤ center + R ≤ n + R + R = n + 2*R`.

The symmetric pair also yields `n ≤ m + 2*R`. The strict bound `2*R < r` implies `r > 0`.

Suppose `k < l`. For natural numbers, `k + 1 ≤ l`. Multiplication by `r` preserves this inequality, so

`n + r = k*r + r = (k+1)*r ≤ l*r = m ≤ n + 2*R`.

Cancel `n` from the outer inequality to get `r ≤ 2*R`, contradicting `2*R < r`. Thus `k < l` is impossible. Repeating the argument with `k,l` and `n,m` swapped rules out `l < k`; natural-number trichotomy gives `k = l`, hence `n = m`. Equivalently, a centered interval of diameter `2*R` contains at most one multiple of a positive `r` when `2*R < r`.

## Controls and boundary cases

- **Premises satisfiable:** for every `r > 0` and `R` with `2*R < r`, take `center=n=m=k=l=0`. A positive-order example is `r=5, R=2, center=n=m=5, k=l=1`; all four interval inequalities hold and `4 < 5`.
- **`r=0`:** impossible, since no natural `2*R` is less than zero. The argument does not rely on a hidden `r=0` case.
- **`R=0`:** interval membership forces `center=n=m` directly. For example `r=1, center=n=m=1, k=l=1` is admissible.
- **One endpoint zero:** if `n=0`, then `m ≤ center+R ≤ 2*R < r`; because `m=l*r` and `r>0`, this forces `l=0` and `m=0`. The case `m=0` is symmetric. `center=0` likewise gives `n,m ≤ R < r`, forcing both multiples to zero.
- **Sharpness / break when relaxed:** with `r=2, R=1, center=1, n=0, m=2, k=0, l=1`, every premise except the strict bound holds and `2*R=r`; yet `n≠m`. More generally, for every `r>0` and `2*R≥r`, choose `center=R, n=0, m=r, k=0, l=1`. Both values meet all four centered inequalities, while `n≠m`. Thus the strict diameter threshold is exact for a universal uniqueness statement of this form.
- **Independent finite control:** enumerated `0≤r,R≤8`, `0≤center≤16`, and `0≤k,l≤4`, setting `n=k*r`, `m=l*r`. There were 181 tuples satisfying the strict premises and no failures of `n=m`. This is a diagnostic check, not the proof above.

## Concrete elliptic-curve order interpretation

For a concrete nonsingular elliptic curve `E` over a finite field of size `q`, the intended center can be `q+1`. To use this lemma for a candidate order `N`, one must independently establish: (i) the actual cardinality `M = #E(F_q)` is a natural number and satisfies the centered inequalities with a rigorously chosen integer `R` (for example, via Hasse's bound and a justified rounding bound for `2√q`); (ii) both `N` and `M` are multiples of the same positive `r`; (iii) `N` satisfies those centered inequalities; and (iv) `2*R<r`. Then instantiate `n=N, m=M` to conclude `N=M`.

An exact-order-`r` point or subgroup can establish `r | M` through the group-order divisibility theorem, once its order and the group hypotheses have been verified. Merely checking `[r]P=O` only shows that the order of `P` divides `r`; by itself it does **not** establish `r | M`. The Nat implication proves neither Hasse's theorem nor any particular curve's nonsingularity, field size, point order, primality, candidate divisibility, candidate interval membership, or existence of a suitable `r`. It is a conditional uniqueness step, not a standalone curve-order certificate. The abstract zero-order witnesses are mathematically valid but do not represent a finite elliptic-curve group, whose order is positive.

## Holds / breaks / inconclusive

- **Holds:** the stated Nat implication; nonvacuity; zero-case behavior; exact strict-threshold sharpness.
- **Breaks:** replacing `2*radius < r` with `2*radius ≤ r`, or allowing `2*radius ≥ r` without another restriction, permits the explicit distinct-multiple construction above.
- **Inconclusive from permitted sources:** whether any particular Lean theorem correctly encodes or proves the statement, and whether any specific elliptic-curve certificate supplies the independent premises. Neither artifact was inspected under the blind-access restriction.
