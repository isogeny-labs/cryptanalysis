# Maximal-order local index for the j=1728 relative quartic factors

The degree-four factors of the j=1728 octic over `L=K(√2)` are **unramified at every place above 7, 11, 23, and 31**. Their repeated reductions and positive polynomial-discriminant valuations at these primes come entirely from nonmaximal monogenic orders. The exact local order-index exponents are `v_P(Disc(g))/2`, taking values 1 or 2 where positive.

| Rational prime | Repeated-reduction / positive-index places, each factor | Index-exponent pattern, each factor | Residue-degree-weighted index exponent |
| ---: | ---: | --- | ---: |
| 7 | 9 | six places with 1; three with 2 | 24 |
| 11 | 6 | six places with 1 | 12 |
| 23 | 10 | six places with 1; four with 2 | 24 |
| 31 | 3 | three places with 1 | 6 |

[`run_sage.py`](run_sage.py) first reconstructed both monic irreducible quartic factors, checked coefficient integrality at every selected place, factored their reductions, and computed exact prime-ideal polynomial-discriminant valuations. The reduction is repeated exactly where the valuation is positive. The full patterns and valuations are in [`result.json`](result.json); the checked-Sage runtime and bounded execution are recorded in [`sage-runtime-info.txt`](sage-runtime-info.txt) and [`attempt.json`](attempt.json).

For the first quartic factor, direct PARI `rnfdisc` computed the **maximal-order relative discriminant ideal** of the degree-144 field over `L`; see [`direct_rnfdisc_side0.json`](direct_rnfdisc_side0.json) and its 223-second [`receipt`](direct_rnfdisc_attempt_side0.json). The ideal contains the rational integer `96`. As an integral discriminant ideal, it therefore has prime support only above 2 and 3. Direct valuation checks for the first factor give zero maximal-order discriminant valuation at every selected place.

The two quartic factors are exact conjugates under `s=√2 ↦ −s`, coefficient by coefficient; their polynomial discriminants are conjugate as well. Discriminant ideals of the corresponding field extensions transport under this base-field automorphism. Since the integer `96` is fixed, it also belongs to the conjugate discriminant ideal. The [conjugation certificate](conjugate_support_result.json) verifies the factor identities, the fixed generator and every saved polynomial valuation in about 33 seconds. It gives zero maximal-order discriminant valuation and the displayed index exponents for the second factor. The independent second-side `rnfdisc` attempt reached its 360-second cap; the earlier Sage wrapper overflowed its PARI stack during polynomial reduction. Those attempts remain explicit [receipts](direct_rnfdisc_attempt_side1.json) and [receipts](relative_discriminant_attempt_side0.json), respectively. The later generator-by-generator transport attempts also timed out; they are retained separately. The second-side conclusion is the exact Galois-transport consequence, not an independently completed `rnfdisc` run.

[`audit.py`](audit.py) independently checks the saved coefficient conjugation with rational arithmetic, reconciles the direct first-side ideal valuations and conjugate-support certificate with every local screen row, and verifies `v_P(Disc(g)) = 2 v_P(index)` at all selected places. Its exact output is [`audit.json`](audit.json).

## Proof map

[`formal/IdealSupport.lean`](formal/IdealSupport.lean) proves that an automorphism-fixed ideal member remains in the transported ideal and excludes a prime that omits that member. It also checks that 7, 11, 23 and 31 do not divide 96. [`formal/QuarticLocalTables.lean`](formal/QuarticLocalTables.lean) kernel-checks all four saved local index tables and weighted sums. [`formal/lean-check.txt`](formal/lean-check.txt) records the builds and `#print axioms`; only standard Lean foundations occur. Formalization of the concrete degree-36 field, its quartic extensions, the exact `rnfdisc` ideal, and the identification of the two extensions under conjugation remains **partial**. The written transport proof above and checked Sage supply that bridge; it is not hidden inside the finite table theorems.

The next local step is to determine split and inert residue behavior for these unramified degree-four extensions. Their reduction patterns alone do not give the complete factorization because the polynomial orders are nonmaximal at the repeated places; a maximal-order residue computation or local Hensel factorization is needed.
