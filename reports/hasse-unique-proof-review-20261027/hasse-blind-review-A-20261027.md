# Blind arithmetic review A — 2026-10-27

## Scope and sources_read

- Read only `/tmp/cryptanalysis-hasse-review-20261027/reports/hasse-unique-proof-review-20261027/blind-brief.md`.
- No Lean documentation or other source was needed. The reasoning below is an independent derivation from the statement in that brief.

## Forbidden-access attestation

Apart from the assignment addressed to me, I did not read parent messages. I did not read the review plan, repository theorem source or proof text, README, receipts, other reviewers' work, or nearby files. I did not run a build or modify repository files. This report is the sole file I wrote.

## Joints owned

1. Validity of the natural-number implication, including zero-modulus behavior.
2. Satisfiability and sharpness of the strict bound.
3. Logical contribution of each stated hypothesis.
4. The precise scope of any curve-order-certificate interpretation.

## Holds: direct derivation

The hypotheses `width < r` over natural numbers imply `r > 0`, so there is no zero-modulus instance to handle. Suppose `k < l`. Then `k + 1 ≤ l`; multiplying by the nonnegative `r` gives

`m = l*r ≥ (k+1)*r = k*r+r = n+r > n+width`.

This contradicts `m ≤ n+width`. Likewise, if `l < k`, then

`n = k*r ≥ (l+1)*r = m+r > m+width`,

contradicting `n ≤ m+width`. Natural-number trichotomy leaves `k = l`, and hence `n = k*r = l*r = m`. This proof uses no subtraction or cancellation and is valid for every permitted natural-number value.

## Satisfiability, sharpness, and hypothesis controls

- The assumptions are satisfiable, including with a positive order candidate: `r=5`, `width=4`, `k=l=2`, `n=m=10`. Both proximity inequalities hold. Thus the theorem is not vacuous. At `r=1`, the strict bound forces `width=0`, where the proximity inequalities already imply equality.
- The strict inequality is sharp for positive `r`: change it to `width ≤ r` and take `r=5`, `width=5`, `k=0`, `l=1`, `n=0`, `m=5`. Both proximity inequalities hold, but `n ≠ m`. At the original `width=4`, the inequality `m ≤ n+width` fails.
- Each multiplication premise matters in general. If only `n=k*r` is removed, `r=5`, `width=1`, `n=1`, `m=0`, `l=0` satisfies the other premises but not the conclusion. If only `m=l*r` is removed, use `r=5`, `width=1`, `n=0`, `k=0`, `m=1`.
- Both directions of proximity matter without a prior ordering of `n,m`. With `r=5`, `width=1`, `n=0`, `m=10`, the inequality `n ≤ m+width` holds, but the reverse fails. Swap `n,m` to show the other direction alone is insufficient. When one ordering is known, only the proximity inequality constraining the larger number is needed.
- The conclusion is the uniqueness of two multiples of `r` separated by at most `width < r`. The proof supplies no existence claim for a multiple in any specified interval.

## Curve-order-certificate scope

**Holds conditionally:** Let `N` be the *actual*, independently defined cardinality of an elliptic-curve group and let `n` be a proposed order. If a certificate separately establishes natural numbers `k,l,r,width` with `N=l*r`, `n=k*r`, `width<r`, and both `N ≤ n+width` and `n ≤ N+width`, this arithmetic result proves `N=n`. For example, a verified subgroup of exact order `r` may establish `r | N`; a verified Hasse interval containing both `N` and `n`, whose integer diameter is at most `width<r`, may establish the proximity inequalities. Those are separate obligations.

**Does not follow from this statement:** validity of the curve or finite field; the actual group cardinality; a subgroup's exact order; divisibility of the actual cardinality by `r`; the Hasse bound for the curve; membership of the proposed `n` in the Hasse interval; or the width of that interval. In particular, checking merely `r*P=O` does not by itself certify that `P` has exact order `r`. The arithmetic implication cannot alone certify a curve order or any discrete-logarithm claim.

## Verdict

- **Holds:** the stated implication, satisfiability, nonvacuity, and the conditional uniqueness step for a curve-order certificate.
- **Breaks:** the weakened boundary `width ≤ r` (counterexample above), and each omitted multiplication or proximity premise in the general case.
- **Inconclusive from the permitted source:** whether any particular Lean theorem is stated or proved this way, whether its surrounding certificate establishes the required curve facts, and whether any concrete curve-order certificate is correct. Those artifacts were deliberately outside this blind review.
