# Regular affine reduction on known-relation lifts

The thirteen exact known-relation lifts admit 54 consecutive rational additions from their recorded rational point `T` to the multiples needed for `P1` and `P2`. Every step has integral input and output coordinates at its row's prime, a unit slope denominator, and the same result after reduction as finite-field addition. The steps consist of 13 tangents and 41 chords. The source is fixed by SHA-256 in `protocol.json`; `python3 run.py` independently recomputes and asserts each check, with all step-level observations in `result.json`.

The generic mathematical statement is: for a commutative ring `R`, field `S`, and ring homomorphism `f : R →+* S`, an affine chord or tangent with unit denominator in `R` has slope and output coordinates that commute with `f`. The written proof is substitution into the Weierstrass addition formulas. A unit `d` satisfies `f(d) f(d⁻¹)=1`, so the mapped rational slope equals the quotient of mapped numerator and denominator. The output coordinates are polynomials in the inputs and slope, and ring homomorphisms preserve those polynomials.

## Proof map

| Result | Lean declaration | Hypotheses and status |
| --- | --- | --- |
| Unit-denominator slope transfer | `map_regularSlope` | `R` commutative ring, `S` field, `f` ring homomorphism, denominator a unit of `R`; checked by `lake build AffineReductionBridge` |
| Coordinate polynomial transfer | `map_addX`, `map_addY` | Same rings and homomorphism; checked by the same build |
| Chord formula transfer | `regular_chord_reduction` | Chord denominator is a source unit equal to `x₂ - x₁`; checked by the same build |
| Tangent formula transfer | `regular_tangent_reduction` | Tangent denominator is a source unit equal to `2*y`; checked by the same build |
| Exact rational addition paths on 13 recorded lifts | `run.py`, `result.json` | Fraction-level replay, finite-field replay, all 54 steps asserted; computational certificate, not a Lean theorem about the elliptic-curve group |
| Point membership under reduction | `XedniRegularChainReduction.mapPoint` | A short-Weierstrass point over `R` maps to a point on the coefficient-reduced curve over `S` |
| One regular addition step under reduction | `XedniRegularChainReduction.map_regularStep` | A chord or tangent with a source-unit denominator, recorded endpoint point, and exact affine addition formulas maps to a field step |
| Finite regular path under reduction | `XedniRegularChainReduction.map_regularChain` | Every step in the source chain satisfies `RegularStep`; the mapped start, addend, intermediates, and endpoint satisfy `FieldChain` |
| Field step is elliptic-curve addition | `XedniRegularGroupLaw.fieldStep_group_add` | Over a field, with the reduced short curve elliptic, a `FieldStep` is equality to mathlib's point-group addition; covers distinct-x chords and nonvertical doubling |
| Field chain gives a group relation | `XedniRegularGroupLaw.fieldChain_group_relation` | The field endpoint equals its start plus a natural-number multiple of the fixed addend |
| Reduced regular chain gives a group relation | `XedniRegularGroupLaw.reduced_regularChain_group_relation` | Combines the source-chain reduction theorem and field group law; requires ellipticity of the coefficient-reduced short curve |
| Prime-local denominator is invertible | `XedniPrimeLocalReduction.denominator_is_unit` | For a prime ideal `P` of `ℤ`, every integer outside `P` maps to a unit of `Localization.AtPrime P` |
| Prime-local chain gives a group relation | `XedniPrimeLocalReduction.local_chain_group_relation` | Specializes the group-law theorem to the residue field of `Localization.AtPrime P`; assumes the reduced short curve is elliptic |
| Residue matches integer quotient | `XedniPrimeLocalReduction.integer_reduction` | For maximal `P`, the residue field equivalence sends integer `z mod P` to the reduction of its localization image |
| Fraction reduction formula | `XedniPrimeLocalReduction.fraction_reduction` | For maximal `P` and denominator outside `P`, the residue of `z/s` corresponds to `(z mod P)/(s mod P)` |
| Direct integer-prime reduction | `XedniLocalZModReduction.reduce_integer` | For `Nat.Prime p`, the composite map from `Localization.AtPrime (span {(p : ℤ)})` to `ZMod p` sends an integer to its usual residue |
| Direct fraction reduction | `XedniLocalZModReduction.reduce_fraction` | For `Nat.Prime p` and denominator outside its ideal, the composite map sends the localization fraction `z/s` to its quotient in `ZMod p` |
| Rational coordinate witness | `XedniRationalLocalWitness.admissible_iff_not_dvd`, `rational_reconstruction`, `reduce_rational` | Canonical denominator admissibility is equivalent to integer nondivisibility by `p`; an admissible coordinate has an explicit local representative with the expected rational value and `ZMod p` reduction |
| Recorded coordinate denominators | `XedniCoordinateCertificates.row*_m*_{x,y}` in `CoordinateCertificates.lean` | All 134 rational coordinates on the 13 recorded paths satisfy `Admissible p`; each theorem has a `#print axioms` audit, and the file is regenerated from the source digest in `protocol.json` |

The Lean chain theorem transfers a path of curve points and regular affine steps, and the group-law theorem identifies its reduced endpoint with a group multiple. The local-integer modules supply the prime-local ring and direct `ZMod p` residue map, including fraction reduction. All 134 recorded rational coordinates now have checked denominator-admissibility proofs and therefore local representatives. The remaining formal bridge is to prove the recorded curve equations and addition paths as `RegularChain` values, and extend point reduction through infinity and vertical additions. The experiment supplies exact regular paths for these thirteen rows; it does not itself establish the group-level theorem for arbitrary rational points.

## Reproduction

From this directory, run `python3 run.py`, `python3 generate_coordinate_certificates.py --check`, `lake build AffineReductionBridge`, `lake build RegularChainReduction`, `lake build RegularGroupLaw`, `lake build PrimeLocalReduction`, `lake build LocalZModReduction`, `lake build RationalLocalWitness`, and `lake build CoordinateCertificates`. The Lean version is pinned in `lean-toolchain`, mathlib in `lake-manifest.json`; the corresponding `build-output*.txt` files record the theorem builds and `#print axioms` output. The replay and certificate generator need only the Python standard library and the source JSON at the sibling path named in the protocol.
