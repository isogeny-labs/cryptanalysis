# Complete splitting at 7, 11, 23, and 31 in the two relative quartic fields

Both degree-four factors over the degree-36 field `L = K(sqrt(2))` have the following complete prime decompositions. Each resulting field has absolute degree 144. The exact degree-18 defining polynomial of `K`, the two quartics, and their coefficient encodings are fixed by the hashed certificates in the protocols.

| Rational prime | Left quartic: absolute residue degrees | Right quartic: absolute residue degrees | Degree sum per side |
| ---: | --- | --- | ---: |
| 7 | 72 primes of degree 2 | 72 primes of degree 2 | 144 |
| 11 | 72 primes of degree 2 | 72 primes of degree 2 | 144 |
| 23 | 4 primes of degree 1; 70 of degree 2 | 4 primes of degree 1; 70 of degree 2 | 144 |
| 31 | 72 primes of degree 2 | 72 primes of degree 2 | 144 |

`final_result.json` retains every base place, its relative degrees, and the evidence route for that place. The source screen has `sum_P f(P|p) = 36` at each selected prime, so all base ramification indices are one and rational `p` is a local uniformizer. The maximal relative discriminant ideal is supported only above 2 and 3 by the exact direct `rnfdisc` ideal certificate in the parent experiment. Thus every selected odd place is unramified in the maximal relative order. The right quartic's discriminant support follows by the verified `s -> -s` conjugation.

## Local resolution

Squarefree reductions give their residue degrees directly. The other patterns are resolved as follows:

1. **One doubled linear factor.** There are 42 place/side cases with reduction degrees and multiplicities `[(1,1),(1,1),(1,2)]`. After lifting the two simple linear factors, the remaining quadratic has discriminant with valuation 2. Its discriminant differs from the quartic discriminant by a square unit. All 42 normalized residues `disc(g)/p²` have quadratic character `+1`; hence the remaining quadratic splits. The `all_square_result.json` rows record every residue and character. Independently, both quartic discriminants have exact square roots in `L`, serialized in `global_disc_result.json` and checked again from their coefficients in `root_replay.json`.
2. **Two doubled linear factors.** There are 12 place/side cases with reduction `[(1,2),(1,2)]`. For each doubled residue root `a`, `double_linear_sage.py` checks that `g(a)` has valuation at least 2 and `g'(a)` at least 1, then computes the integral quadratic Taylor reduction `g(a+pt)/p² mod P`. Its leading coefficient and discriminant are nonzero, and all 24 discriminants have quadratic character `+1`. Each simple root in the scaled `t` polynomial lifts by Hensel to a root of `g`, resolving both clusters into two local degree-one factors. The root lifts, three Taylor coefficients, discriminants, and characters are retained in `double_linear_result.json`.
3. **One doubled irreducible quadratic.** The two remaining places, at `p=23`, have reduction `h(z)²` with irreducible `deg(h)=2` over the base residue field. A local degree-one factor is excluded by that reduction. Unramifiedness leaves `[2,2]` or `[4]`. The exact global discriminant square forces even Frobenius sign, while a 4-cycle is odd, so both places have relative degrees `[2,2]`.

`final_aggregate.py` combines these cases, requires all 42 and 12 frozen sites to be consumed exactly once, checks the two parity cases at their exact place indices, and verifies degree 144 for each side and prime. `audit.py` checks input hashes, result links, serialized-root replay, per-phase counts, final rows, and the direct PARI terminal receipt.

## Proof map

| Mathematical step | Lean declaration | Status |
| --- | --- | --- |
| A quadratic over a field with `2 ≠ 0` splits exactly when its discriminant is a square | `J1728QuarticLocalFactor.quadratic_split_iff_discriminant_square` in `formal/QuadraticSplit.lean` | checked |
| Removing a nonzero square factor preserves square status | `J1728QuarticLocalFactor.square_scaled_iff_square` in `formal/QuadraticSplit.lean` | checked |
| Every 4-cycle has odd sign | `J1728QuarticLocalFactor.every_four_cycle_odd` in `formal/FourCycleParity.lean` | checked |
| Coprime Hensel factor lifting, scaled Taylor lifting, discriminant square to Frobenius sign, and the exact Sage/PARI number-field bridge | mathematical proof above and frozen certificates | formalization partial; these Lean bridges remain open |

Both theorem modules build with the pinned Lean 4 and mathlib revisions; `formal/lean-check.txt` retains commands, output, and `#print axioms` results. No research-result axioms or proof placeholders are used in the checked declarations.

The full Lean theorem remains open. Its missing definitions and obligations are an exact `L/K` and quartic-polynomial encoding, the selected prime ideals and residue maps, the local Hensel factorization and scaled Taylor bridge, and the theorem identifying Frobenius sign with discriminant square status for the unramified quartic extension. The computational certificates and the written argument above retain the full statement while those bridges are formalized.

## Bounded independent PARI route

The saved 9,260,825-byte PARI `rnfinit` checkpoint was loaded and one specified base prime above 31 was passed to `rnfidealprimedec`. That call reached the frozen 900-second cap before returning a prime row. `attempt.json` retains the phase times and `TIME_LIMIT`; the earlier relative-ideal API correction is retained in `attempt_api_error.json`. The parent experiment's `.artifacts.json` stores the checkpoint hash and size, and its bytes must be hydrated from that artifact store for replay. The local factorization evidence above resolves the selected prime tables without expanding the degree-144 absolute number field in this direct route.
