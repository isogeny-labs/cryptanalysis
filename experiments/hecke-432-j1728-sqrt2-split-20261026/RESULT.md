# Frobenius-swapped √2 factors in the level-432 C–E resolvent

The exact quartic and octic factors of the source-`j=1728` C–E resolvent each split over `K(√2)` into a pair exchanged by `√2↦−√2`: two irreducible quadratics and two irreducible quartics, respectively. Each pair is coprime over characteristic zero. At a rational C point modulo a prime where `2` is nonsquare, the same factor exchange becomes Frobenius on `F_{p²}`. When the specialized pair remains coprime, a root fixed by Frobenius would have to lie in both factors, which is impossible. This gives a conditional arithmetic explanation for the zero rational C–E rows in the tested `p ≡ 11 (mod 24)` class.

The certificate and its independent replay passed on 12 earlier C rows. A separate prospective source-only holdout at 8123, 8147, and 8171 passed on all six new C rows; an independent exhaustive check evaluated every one of the 48,882 candidate `x_E` values in those six fields and found zero resolvent roots.

## Exact relative-field certificate

[`protocol.json`](protocol.json) fixes the [degree-18 coordinate field and quartic–octic certificate](../hecke-432-j1728-resolvent-field-20261026/factor_certificate.json) by hash. Write `K=Q[x]/(f(x))`, with `a` the image of `x`, for the source-coordinate field and `L=K[s]/(s²−2)`. [`export_sqrt2_sage.py`](export_sqrt2_sage.py) exports every coefficient of both factor pairs in the relative basis `1,s`; the full vectors are in [`sqrt2_factor_certificate.json`](sqrt2_factor_certificate.json). Its exact product checks are

`Q₄ = u₄ q₂ q₂′`, with `q₂′` the monic conjugate of `q₂`, and

`Q₈ = u₈ q₄ q₄′`, with `q₄′` the monic conjugate of `q₄`.

Here each displayed factor is irreducible over `L`, and each conjugate pair has gcd one and nonzero resultant. [`check_certificate_sage.py`](check_certificate_sage.py) independently reconstructs all vectors, exact products, irreducibility, conjugacy, and coprimality. Its [`certificate_check.json`](certificate_check.json) receipt has status `PASS_EXACT_AND_FINITE_SQRT2_CONJUGACY_CHECK`. Sage's relative element `.list()` is used for the `K ⊕ Ks` coefficients; the absolute `.polynomial()` representation has degree 36 and is unsuitable for the sign-change map. All local Sage runs used the repository's checked launcher; [`sage-runtime-info.txt`](sage-runtime-info.txt) records the accepted runtime.

## Finite-field Frobenius gate

The independent checker also reduces the exact certificate at all 12 C points from the earlier `11 mod 24` and `23 mod 24` controls. At six `11 mod 24` points, `2` is nonsquare, Frobenius sends `s` to `−s`, both specialized pairs stay coprime, and neither base factor has an `F_p` root. At six `23 mod 24` points, `2` is square and the pairs reproduce four rational roots of the degree-12 resolvent per C point. The [previous factor-parity result](../hecke-432-j1728-ce-factor-20261026/RESULT.md) records the base-polynomial patterns and C points.

The new [`holdout_protocol.json`](holdout_protocol.json) froze an ascending source-only scan from `8000 ≤ p < 20000` before reading the resolvent at the selected primes. [`select_holdout_sage.py`](select_holdout_sage.py) chose the first three `11 mod 24` primes with two rational source-`j=1728` C points: 8123, 8147, and 8171. [`test_holdout_sage.py`](test_holdout_sage.py) checked Frobenius exchange, pairwise gcd, product recovery, and root exclusion at each of the six points. Its status is `PASS_PROSPECTIVE_SQRT2_FROBENIUS_HOLDOUT` in [`holdout_result.json`](holdout_result.json). [`audit_holdout.py`](audit_holdout.py) separately rebuilt each specialized resolvent from the frozen terms and exhaustively tested all `x_E∈F_p`; [`holdout_audit.json`](holdout_audit.json) records `PASS_INDEPENDENT_EXHAUSTIVE_HOLDOUT_AUDIT` and 48,882 checked values.

## Proof map and scope

The mathematical implication is elementary once the exact factorization and its reduction are available. Let `q,q′∈F_{p²}[z]` be a pair exchanged by coefficient Frobenius, assume they are coprime, and let `r∈F_p`. If `q(r)=0`, Frobenius fixes `r` and sends that equation to `q′(r)=0`; a Bézout relation for `q,q′` then gives `1=0`. The same applies with the two factors interchanged. [`FrobeniusSwapGate.lean`](formal/FrobeniusSwapGate.lean) proves this structural implication for a field endomorphism and an explicit Bézout identity. The pinned Lean build succeeded; [`lean-check.txt`](formal/lean-check.txt) reports only `propext`, `Classical.choice`, and `Quot.sound` under `#print axioms`.

The exact relative-field products and six fresh finite reductions are certificate checked. A uniform good-reduction theorem for all `11 mod 24` primes remains open: the denominator and resultant primes at which the conjugate factors can collide modulo `p` have not been completely enumerated. Lean formalization of the full degree-18/36 field coefficients and reduction maps is partial; the checked Lean declaration covers the Frobenius/Bézout implication with all of its hypotheses explicit. The next experiment is to compute the relative pair resultants and their rational norms so the exceptional-prime set can be stated and audited.
