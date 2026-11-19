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
| Finite regular sum under reduction | `XedniRegularSumReduction.reduce_regularSum` | Any nonempty ordered list of local curve points with a `RegularStep` certificate at each addition; reduced elliptic endpoint equals the group sum of the reduced inputs; checked |
| Equal regular endpoints give equal reduced sums | `XedniRegularSumReduction.equal_regularSums` | Two certified regular sums with equal local endpoints and elliptic coefficient-reduced curve; checked |
| Certified identity and inverse additions | `XedniExceptionalSumReduction.reduce_certifiedStep` | The source point at infinity acts as identity, exact local inverses cancel, and regular unit-denominator affine additions reduce to field group addition; checked |
| Finite sums with certified exceptional steps | `XedniExceptionalSumReduction.reduce_certifiedSum`, `equal_certifiedSums` | Nonempty finite lists of local affine points or infinity; every addition carries an identity, exact inverse, or regular affine certificate; checked |
| Residue-vertical chord and projective limit | `XedniResidueVerticalObstruction.no_integral_chord_x`, `chord_numerators_correct`, `homogeneous_chord_at_infinity`, `residue_inverse_affine_obstruction` | A reduced x-difference of zero and reduced y-difference nonzero exclude an integral affine chord endpoint; the homogeneous chord triple reduces to infinity, and inverse reduced points have zero group sum; checked |
| Residue chord is the projective zero point | `XedniResidueProjectiveZero.chordResidueTriple_projective_zero` | The reduced homogeneous chord triple is a nonsingular projective point equal to the point at infinity; field-valued residue map, reduced x-difference zero, reduced y-difference nonzero; checked |
| Source homogeneous chord lies on its projective curve | `XedniSourceChordEquation.sourceChordTriple_on_curve` | Any two source-ring affine points on the same short-Weierstrass curve; no denominator invertibility; checked |
| Source chord is nonsingular at a residue-vertical boundary | `XedniSourceChordNonsingular.sourceChordTriple_nonsingular` | Source projective curve point, field-valued reduction, reduced x-difference zero and reduced y-difference nonzero; checked |
| Local projective chord derivative is a unit | `XedniLocalChordUnitDerivative.chordZDerivative_isUnit`, `primeLocal_chordZDerivative_isUnit` | Source local ring with its canonical residue field, or the recorded integer prime-local ring; reduced x-difference zero and y-difference nonzero; checked |
| Source chord equals projective addition coordinates | `XedniSourceChordAddition.addXYZ_eq_neg_sourceChordTriple` | Two affine source points on a short-Weierstrass curve over any commutative ring; mathlib's `addXYZ` equals the source chord triple scaled by `-1`; checked |
| Distinct source chord selects addition branch | `XedniSourceChordDistinctAddition.addMap_eq_sourceChordClass` | Distinct source x-coordinates; mathlib's projective `addMap` is the chord class; checked |
| Residue-vertical source addition reduces to zero | `XedniResidueAdditionZero.reduced_source_add_point_zero` | Ring map from a commutative source ring to a field, reduced x-difference zero, reduced y-difference nonzero; reduced source addition is a nonsingular zero point; checked |
| Residue-vertical projective addition commutes with class reduction | `XedniProjectiveClassReduction.mapClass_addMap_residue_vertical` | Same ring map and residue conditions; class map preserves the source `addMap` result in this branch; checked |
| Mapped-distinct projective addition commutes with class reduction | `XedniProjectiveAddMapDistinct.mapClass_addMap_of_mapped_not_equiv` | Any commutative source and target rings and ring map; mapped representatives inequivalent; both additions select the polynomial chord branch; checked |
| Coalescing inputs expose a raw projective class obstruction | `XedniProjectiveAddMapCounterexample.raw_mapClass_not_addMap` | Curve `y²=x³−25x+1` over `ℤ`, points `(0,1)` and `(5,1)`, reduction to `ZMod 5`; reduced curve discriminant `3`, source addition triple maps to the zero vector while reduced addition doubles a nonzero point; checked |
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
| Rational curve point in the local ring | `XedniRationalCurveBridge.localToRat_injective`, `localToRat_fraction`, `localCurvePoint` | The integer localization embeds in `ℚ`; an admissible rational point satisfying the short-Weierstrass equation becomes a `CurvePoint` over the local ring with the same rational coordinates |
| Recorded rational curve equations and local points | `XedniCurveEquationCertificates.row*_m*_curve`, `row*_m*_localPoint` in `CurveEquationCertificates.lean` | All 67 recorded rational multiples have checked curve equations and corresponding prime-local `CurvePoint` definitions; the 134 declarations have `#print axioms` audits and are regenerated from the frozen source digest |
| Rational regular-step bridge | `XedniRationalRegularStep.unit_of_reduction_ne_zero`, `chord_step`, `tangent_step` | A nonzero reduced slope denominator is a unit in the local ring; rational chord and tangent formulas then imply `RegularStep` for prime-local curve points |
| Recorded regular additions and paths | `XedniRecordedRegularSteps.row*_step*`, `row*_chain` in `RecordedRegularSteps.lean` | All 54 recorded additions have checked `RegularStep` proofs, including 13 tangents and 41 chords; 13 checked `RegularChain` proofs reach each row's final multiple. The generator checks the frozen source digest and reproduces the Lean file byte for byte |
| Recorded finite-field ellipticity | `XedniFiniteGroupChains.row*_elliptic`, `row*_reduced_elliptic` in `FiniteGroupChains.lean` | For each of 13 rows, the short curve over `ZMod p` has nonzero discriminant, and its coefficient-reduced local model is elliptic; all 26 declarations are checked |
| Recorded group-law consequences | `XedniFiniteGroupChains.row*_group_relation` in `FiniteGroupChains.lean` | Each checked prime-local `RegularChain` reduces to a finite-field endpoint equal to its start plus a natural-number multiple of its addend; 13 checked declarations. The existential multiplier is not yet identified with the recorded chain index |
| Exact chain multipliers | `XedniExactChainMultipliers.reduced_regularChainN_exact`, `reduced_regularChainN_from_self`, `row*_chainN`, `row*_exact` in `ExactChainMultipliers.lean` | Length-indexed regular chains reduce to exact group multiples; all 13 recorded endpoint multipliers are checked. The generator verifies the frozen source digest and row proofs, and all declarations have axiom audits |
| Selected public-coordinate reduction | `XedniPublicPointReduction.row*_m*_{x,y}_public` in `PublicPointReduction.lean` | All 62 coordinates of the 31 selected rational multiples reduce to their recorded `ZMod p` coordinates; the generator checks the frozen source and the required sign choices against public `R`, `U`, and `V` |
| Signed public relation, initial cases | `XedniSignedPublicRelation.signed_multiple_relation`, `row0_public_relation`, `row1_public_relation` in `SignedPublicRelation.lean` | A generic additive-group identity combines signed scalar multiples. Rows 0 and 1 establish the positive- and negative-`b` proof patterns used for all recorded rows |
| All recorded signed public relations | `XedniAllSignedPublicRelations.row*_public_relation` in `AllSignedPublicRelations.lean` | For each of 13 frozen rows, checked prefix chains prove the selected positive multiples, coordinate certificates identify the signed `U` and `V` points, and the group law yields `a • U + b • V = 0`. All 91 generated declarations have axiom audits |
| Uniform-target relation count | `XedniUniformRelationBound.unique_partner`, `relation_card`, `relation_fraction`, `prime_field_relation_fraction`, `relation_family_card_bound` in `UniformRelationBound.lean` | For a finite field `F` and fixed `b ≠ 0`, one linear relation has exactly `|F|` solutions among `|F|²` ordered pairs. A fixed family `S` of coefficient pairs covers at most `|S|·|F|` pairs. All theorems are checked with axiom audits |
| Adaptive coefficient boundary | `XedniAdaptiveCoefficientBoundary.adaptive_relation_iff`, `adaptive_relation_card` in `AdaptiveCoefficientBoundary.lean` | If `a,b` may depend on the observed pair `(u,v)`, with `b ≠ 0`, a relation exists exactly when `u ≠ 0` or `v = 0`. Over a finite field of size `q`, that is `q²−q+1` of `q²` pairs; checked by Lean and an exhaustive three-field census |

The Lean chain theorem transfers a path of curve points and regular affine steps, and the group-law theorem identifies its reduced endpoint with a group multiple. The local-integer modules supply the prime-local ring and direct `ZMod p` residue map, including fraction reduction. All 134 recorded rational coordinates have checked denominator-admissibility proofs, all 67 recorded multiples have checked curve equations and prime-local `CurvePoint` definitions, and all 54 recorded additions have checked `RegularStep` proofs assembled into 13 `RegularChain` proofs. All 13 recorded short curves have checked finite-field ellipticity, and the length-indexed chain theorem proves each recorded endpoint's exact group multiple. All 31 selected multiples have checked reduction coordinates, with public `R`, `U`, and `V` sign choices verified by the generator. The signed public-point relation is checked for every recorded row. The finite-field counting theorems separate fixed coefficients from coefficients chosen after observing scalar inputs. The finite-sum modules cover regular steps, identity, and exact local inverse cancellation; the residue-vertical theorem identifies the projective boundary of the affine chart. The next proof step is to connect that homogeneous boundary to a local projective group-law reduction, then analyze the lift selector's accessible information and adaptive choices.

## Uniform-target counting proof

Let `F` be a finite field of size `q`, and fix coefficients `a, b ∈ F` with `b ≠ 0` independently of the input pair. For each `u ∈ F`, the equation `a u + b v = 0` has the unique solution `v = -(a u)/b`. Mapping `u` to this pair is a bijection from `F` onto the solution set, so exactly `q` of the `q²` ordered pairs satisfy the relation. Its exact fraction under an independent uniform pair law is `1/q`. For a fixed finite set `S` of `M` coefficient pairs, each with nonzero second coefficient, the union has at most `Mq` pairs; its fraction is at most `min(1, M/q)`. `UniformRelationBound.lean` checks the bijection, exact fraction, prime-field corollary, and union cardinal bound. Applying this bound to a particular lift selector requires a separate input-law or adaptive-selection argument.

## Adaptive coefficient boundary

When coefficients may be chosen after seeing the scalar pair `(u,v)`, the choice `(a,b)=(v,−u)` gives `a u+b v=0` whenever `u≠0`, and `b` remains nonzero. If `u=v=0`, choose `(0,1)`. For `u=0,v≠0`, the equation reduces to `b v=0`, which is impossible with `b≠0`. Thus the exact success condition is `u≠0` or `v=0`, and the finite-field count is `q²−(q−1)=q²−q+1`. `AdaptiveCoefficientBoundary.lean` proves this equivalence and cardinality. The coefficient choice uses the scalar coordinates themselves; deriving those coordinates from elliptic-curve public points is a separate computation.

`AdaptivePublicRelationReduction.lean` identifies the corresponding public-point computation. In any `ZMod q`-module `G` for prime `q`, a valid relation `a • P + b • Q = 0` with `b ≠ 0` certifies `Q = (−a/b) • P`. If `P ≠ 0` and `Q = v • P`, it recovers the unique scalar `v = −a/b`. Conversely, a known scalar gives the relation `(-v) • P + 1 • Q = 0`. The module also proves the integer-scalar version in any additive commutative group: if `P` has additive order `q`, `Q` lies in its generated subgroup, and `a • P + b • Q = 0` for integers `a,b` with `b mod q ≠ 0`, then the target log modulo `q` is `−a/b`. A checked specialization applies this theorem to mathlib's elliptic-curve affine point group. A concrete curve application supplies the point-order and target-membership facts; no ambient `ZMod q`-module instance is required. A procedure returning such a valid relation for an unknown public target therefore returns its discrete logarithm by field arithmetic. These are algebraic reductions, with no runtime claim.

The module now defines a public-input extractor `extractScalar`: given `P`, `Q`, and an optional integer coefficient pair from any deterministic oracle, it checks `b mod q ≠ 0` and `a • P + b • Q = 0`, then returns `−a/b mod q`. For an order-`q` base point and any finite set of target scalars, `extractor_success_set_eq` proves that the extractor returns the correct scalar on **exactly** the targets where the oracle outputs a valid relation. The target input to the oracle and extractor is the point `Q`, while the scalar appears only in the theorem's correctness specification. The set equality also transfers a rate under any declared distribution on that set; measuring total runtime requires charging the oracle, relation check, division, and scalar verification.

`selected_lift_relation_recovers_scalar` closes the algebraic path from a selected lift: an additive reduction map sends lift points `p,t` to public `P,Q`; applying it to `a • p + b • t = 0` yields `a • P + b • Q = 0` and the exact target scalar residue. `selected_lift_family_recovers_scalar` permits a different lift group, reduction map, selected points, and coefficients for every public target in a declared set. Its hypotheses retain the base-point order, target-subgroup membership, additive reduction, and `b mod q ≠ 0` conditions. A concrete lift construction must establish its reduction map and point images to use the theorem.

`CertifiedRelationExtraction.lean` supplies a pathwise implication from local addition certificates to a public relation. For selected local curve points `p,t`, choose two signs and repetition counts `m,n`. If a `CertifiedSum` of those signed points ends at infinity, `certified_sum_public_relation` proves the exact integer relation between their reduced public points. The curve field has prime characteristic `fieldPrime`; the subgroup order is a separate prime `r`. With an order-`r` base, target membership in its subgroup, and a nonzero target coefficient modulo `r`, `certified_sum_recovers_scalar` gives the target log residue modulo `r`. Every step of the `CertifiedSum` carries a regular, identity, or exact inverse-cancellation certificate. `RecordedCertifiedRelation.lean` builds the required certificate for row 0 from its three checked regular additions and one inverse cancellation, deriving `4P−T=0` from the path. A new selected xedni path needs its own signed list and endpoint certificate.

| Result | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| Public relation certificate | `XedniAdaptivePublicRelationReduction.relation_certificate_verifies` | Prime `q`, `ZMod q`-module `G`, `b ≠ 0`, `a • P + b • Q = 0`; proves `Q = (−a/b) • P`; checked |
| Scalar extraction | `XedniAdaptivePublicRelationReduction.relation_certificate_recovers` | Same module, `P ≠ 0`, `Q = v • P`; proves `v = −a/b`; checked |
| Converse and span characterization | `XedniAdaptivePublicRelationReduction.known_scalar_gives_relation`, `relation_certificate_iff_span` | Known scalar yields coefficients `(-v,1)`; a valid relation exists exactly when `Q` lies in the `ZMod q`-span of `P`; checked |
| Integer-scalar group extraction | `XedniAdaptivePublicRelationReduction.integer_relation_recovers_scalar`, `integer_relation_for_subgroup` | Additive commutative group, `addOrderOf P = q`, target in `zmultiples P`, integer relation with `b mod q ≠ 0`; recovers target log residue `−a/b` modulo `q`; checked |
| Elliptic-curve point specialization | `XedniAdaptivePublicRelationReduction.elliptic_relation_for_subgroup` | Smooth Weierstrass curve over `ZMod q`, affine group points `P,Q`, `addOrderOf P = q`, `Q ∈ zmultiples P`, and a valid integer-scalar relation; checked |
| Public-input extractor and exact success transfer | `XedniAdaptivePublicRelationReduction.extractScalar_iff_valid`, `validRelationOutput_iff`, `extractor_success_set_eq` | `DecidableEq` additive group, order-`q` base point, arbitrary point-to-coefficient oracle, and arbitrary finite target set; verified relation outputs and correct extracted scalars occur on identical target sets; checked |
| Selected-lift reduction | `XedniAdaptivePublicRelationReduction.selected_lift_relation_recovers_scalar`, `selected_lift_family_recovers_scalar` | Additive reduction from lift group to public group, selected points reducing to `P,Q`, order-`q` base, target-subgroup membership, valid integer relation with `b mod q ≠ 0`; family theorem allows all lift data and coefficients to depend on public target; checked |
| Certified finite-path extraction | `XedniCertifiedRelationExtraction.certified_sum_public_relation`, `certified_sum_recovers_scalar` | Short Weierstrass curve over a commutative source ring, ring map to `ZMod fieldPrime`, elliptic reduced curve, signed repeated inputs with a `CertifiedSum` endpoint at infinity; scalar theorem adds independent prime subgroup order `r`, target subgroup membership, and nonzero target coefficient modulo `r`; checked |
| Recorded row 0 certified relation | `XedniRecordedCertifiedRelation.row0_certified_sum`, `row0_public_relation_from_certified_sum` | Prime-local curve at field prime 313, three recorded regular additions `T+T=2T`, `2T+T=3T`, `3T+T=4T`, followed by exact cancellation of `4T` with its inverse; yields public `4P−T=0`; checked |
| Row 0 finite base point | `XedniRecordedPointOrder.finiteBase`, `basePoint_ne_zero` | Point `(306,125)` on `y²=x³−x+15961` over `ZMod 313`; point membership and nonzero status checked in Lean. The order-331 theorem remains open |

Run `lake build AdaptivePublicRelationReduction`; `build-adaptive-public-relation-output.txt` records the registered build, direct module check, and `#print axioms` audit. The toolchain and Mathlib revision are pinned beside this module; `lean4checker --fresh` is unavailable on this host.

Run `lake build CertifiedRelationExtraction`; `build-certified-relation-extraction-output.txt` records the registered build, direct module check, and `#print axioms` audit for the pathwise theorems.

Run `lake build RecordedCertifiedRelation`; `build-recorded-certified-relation-output.txt` records the registered build, direct module check, and axiom audit for the concrete row 0 certificate.

`python3 check_row0_point_order.py --check` replays `row0-point-order-result.json` with exact integer arithmetic. Independent square-table and quadratic-character counts both give curve order 331 over `F₃₁₃`; repeated affine addition gives base-point order 331, with `330P=(306,188)=−P`, `331P=O`, and `4P=(1,183)`. This is a computational certificate. `RecordedPointOrder.lean` formalizes membership and nonzero status; the full `addOrderOf P = 331` theorem and the cast from the recorded prime-local point to this explicit finite-field point remain open. Direct `decide` did not normalize mathlib's affine `addX` and `slope` for the first doubling step. The next proof step is a checked finite-field addition chain or an explicit cardinality certificate, then application of `certified_sum_recovers_scalar` with field prime 313 and subgroup prime 331.

The frozen [adaptive census protocol](adaptive-coefficient-protocol.json) admits all ordered pairs over `F₇`, `F₁₁`, and `F₃₁`. [The result](adaptive-coefficient-result.json) compares a fixed `(1,1)` relation, the explicit adaptive rule, and an exhaustive search over every `a` and nonzero `b`:

| `q` | Total pairs | Fixed hits | Adaptive hits | Exhaustive disagreement |
| ---: | ---: | ---: | ---: | ---: |
| 7 | 49 | 7 | 43 | 0 |
| 11 | 121 | 11 | 111 | 0 |
| 31 | 961 | 31 | 931 | 0 |

Run `python3 run_adaptive_coefficient_census.py` to reproduce these rows. The protocol SHA-256 is `0678db96b117e812dcf435c2eef435672070c2c138ec50e5418c2b0d712e5662`; the result retains all three fields and zero disagreement counts.

## Selector-invariant fixed-family bound

Let `q` be prime and `S` a fixed finite family of integer pairs `(a,b)` with `b mod q ≠ 0`. For **each** public pair `uv ∈ (ZMod q)²`, permit a different additive group `L(uv)`, a homomorphism `reduce_uv : L(uv) →+ ZMod q`, and a selector of two points in `L(uv)` reducing to the two coordinates of `uv`. If one selected pair satisfies `a P+b Q=0` for some vector in `S`, the homomorphism gives `(a mod q)u+(b mod q)v=0`. Hence every selected success lies in the union of the public relation lines indexed by `S`. Each line has `q` pairs, so **at most `|S|q` of the `q²` public pairs can succeed**, regardless of how the curve and lift are selected from the public pair. Under the separate assumption that the public pair is uniform over `(ZMod q)²`, the success fraction is at most `min(1, |S|/q)`.

| Result | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| Selected exact relation maps to its public relation | `XedniSelectorRelationBound.selected_relation_implies_public` in `SelectorRelationBound.lean` | Pair-indexed additive groups and homomorphisms; selected points reduce to the public pair; checked |
| Fixed-family cardinal bound for an arbitrary pair-dependent selector | `XedniSelectorRelationBound.selected_relation_card_bound` | Same data, fixed finite integer family, every second coefficient nonzero modulo prime `q`; checked |

The theorem allows a distinct selected rational curve for every public pair through the dependent family `L(uv)`. It assumes the point-level reduction homomorphisms and does not prove that every proposed rational construction supplies one. The previous regular-step Lean modules and concrete audits establish portions of that geometric bridge. The deterministic query laws in the experiments are not uniform draws from all `q²` pairs, so their observed frequencies are not estimates of the uniform fraction.

Run `lake build SelectorRelationBound` in this directory. The checked toolchain is `v4.35.0-rc4`, with Mathlib revision `021c46bdd042f67b538b9f9871d556a93713a9a9`; `build-selector-output.txt` records the build and `#print axioms` output. Both new declarations list only `propext`, `Classical.choice`, and `Quot.sound`. `lean4checker --fresh` is unavailable on this host.

## Shared-target offset relation

For two points `U=(w−t₁)G` and `V=(w−t₂)G` sharing a scalar target, a fixed coefficient vector satisfies `aU+bV=O` exactly when `(a+b)w=a t₁+b t₂` modulo the subgroup order. When `a+b≠0`, that equation has one target scalar in the field. `SharedTargetRelation.lean` proves the field equivalence, uniqueness, and prime-field specialization. The [full input-law census](../xedni-shared-target-hit-law-20261119/README.md) applies the first-16 offset selection and identity exclusions to all 3,310 nonzero target scalars on the frozen eight-field panel.

## Shared-target selected-lift bound

For a prime-order subgroup of order `q`, fix a finite integer coefficient family `S` and a finite set `T` of offset pairs before the target scalar is drawn. Assume `a+b ≠ 0 mod q` for every `(a,b) ∈ S`. A selected lift may depend on each public pair `(w−t₁,w−t₂)`, provided its two selected points reduce to those public coordinates through an additive homomorphism. Then **at most `|T|·|S|` target scalars** in `ZMod q` admit any exact selected relation across those offsets and coefficients. For one offset pair the bound is `|S|`. For a uniform nonzero scalar, the success fraction is at most `min(1, |T|·|S|/(q−1))`. If at least half the nonzero scalars are to succeed, the precommitted product must satisfy `|T|·|S| ≥ (q−1)/2`.

The proof first maps a selected rational relation to `a(w−t₁)+b(w−t₂)=0` modulo `q`. This rearranges to `(a+b)w=a t₁+b t₂`, which has one root because `a+b` is nonzero. Taking unions over `S` and `T` gives the cardinal bounds. The [Lean module](SharedTargetSelectorBound.lean) proves both union steps for an arbitrary public-pair-dependent family of additive lift groups and reduction homomorphisms. The group homomorphism is an explicit hypothesis; the existing prime-local modules establish concrete regular-step cases. The frozen first-16 query law selects from the 56 ordered distinct pairs of its eight offsets, so this bound applies with that precommitted universe. Its `13·56=728` upper bound is loose on the eight measured small subgroups; the exact input-law census supplies their finite counts.

| Result | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| One fixed offset pair | `XedniSharedTargetSelectorBound.selected_shared_target_card_bound` | Prime `q`, fixed finite `S`, nonzero coefficient sums, pair-dependent additive lift groups and reduction homomorphisms; checked |
| Precommitted offset family | `XedniSharedTargetSelectorBound.precommitted_offsets_card_bound` | Same hypotheses and fixed finite `T`; checked |
| Nonzero target restriction | `XedniSharedTargetSelectorBound.precommitted_nonzero_card_bound` | Same hypotheses, with target scalar restricted to `w≠0`; checked |

Run `lake build SharedTargetSelectorBound` in this directory. `build-shared-selector-output.txt` records the actual build and `#print axioms` for all three theorems; each uses only `propext`, `Classical.choice`, and `Quot.sound`. The pinned Lean toolchain and Mathlib revision are the same as the adjacent selector and shared-target modules. `lean4checker --fresh` is unavailable on this host.

## Fixed-family target impossibility theorem

`SharedTargetSelectorImpossibility.lean` turns the capacity bound into a universal-coverage obstruction. Suppose the coefficient pairs `S` and offset pairs `T` are committed before the target scalar is known, and every coefficient sum is nonzero modulo prime subgroup order `q`. A lift selector may choose a different additive group and different points for every public pair, provided its reduction map is additive and the selected points reduce to that pair. If **every nonzero target** has an exact selected relation, then `|T|·|S| ≥ q−1`. Consequently, when `|T|·|S| < q−1`, Lean constructs the logical existence of a nonzero target with no such relation.

The proof counts the `q−1` nonzero scalars in `ZMod q`. Full coverage makes the hit set equal to that nonzero set, while `precommitted_nonzero_card_bound` puts the hit count at most `|T|·|S|`. These inequalities give the lower bound; its contrapositive gives a missed target. This theorem rules out universal coverage by a sublinear fixed coefficient-offset family under its explicit homomorphism premise. It leaves adaptive coefficients, other relation forms, and the construction cost of the selector to their separate analyses.

| Result | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| Universal coverage requires linear family size | `XedniSharedTargetSelectorImpossibility.full_nonzero_coverage_requires_linear_family` | Prime `q`; fixed `S,T`; each coefficient sum nonzero modulo `q`; arbitrary public-pair-dependent additive lift groups, reduction homomorphisms, and correct selectors; every nonzero target hit; checked |
| Subthreshold family misses a nonzero target | `XedniSharedTargetSelectorImpossibility.exists_nonzero_target_without_selected_relation` | Same setup and `|T|·|S| < q−1`; checked |
| Missed-target count lower bound | `XedniSharedTargetSelectorImpossibility.missed_nonzero_target_count_lower_bound` | Same fixed-family and additive-reduction setup; at least `q−1−|T|·|S|` nonzero target scalars are outside the selected hit set, with truncated natural subtraction; checked |

Run `lake build SharedTargetSelectorImpossibility`; `build-shared-selector-impossibility-output.txt` records the registered build, direct module check, and `#print axioms` audit. All three declarations use only `propext`, `Classical.choice`, and `Quot.sound`. The [frozen root census](../xedni-fixed-family-root-census-20261119/README.md) independently enumerates the necessary public-relation roots above this bound's capacity threshold.

`FixedFamilyRationalRootPlateau.lean` checks the complete 13-vector by 56-offset-pair rational enumeration in 13 kernel-checked chunks. Its 420-element first-occurrence certificate has 419 nonzero reduced fractions, positive denominators at most 11, numerator absolute values at most 191, and coprime coordinates. Distinct fractions have nonzero cross-determinants. A checked ten-class numerator envelope, grouped by reduced denominator, proves the sharp uniform cross-determinant bound 2,046, attained by `5/11` and `191/11`. Gcd divisibility proves that every raw coefficient-offset quotient equals its normalized modular fraction when the denominators survive, and the frozen vector sums make that condition automatic here. Consequently, the Lean theorem proves that the **raw public relation family has exactly 419 nonzero modular roots and misses exactly `q−420` nonzero targets for every prime `q > 2046`**. The independently replayed exact-arithmetic [plateau certificate](../xedni-fixed-family-root-census-20261119/README.md) agrees with the root count and sharp threshold.

| Result | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| Bounded integer survives reduction | `XedniFixedFamilyRationalRootPlateau.cast_ne_zero_of_natAbs_lt` | Prime `q`, nonzero integer with `natAbs < q`; checked |
| Distinct fraction images | `XedniFixedFamilyRationalRootPlateau.modular_roots_distinct_of_det_bound` | Prime `q`, denominators nonzero modulo `q`, nonzero cross-determinant with `natAbs < q`; checked |
| Modular image cardinality | `XedniFixedFamilyRationalRootPlateau.modular_root_image_card_of_certificate` | Finite pair set, every denominator and pairwise determinant satisfies the bounds; checked |
| Nonzero modular image cardinality | `XedniFixedFamilyRationalRootPlateau.modular_nonzero_root_image_card_of_certificate` | Same data, canonical zero pair `(0,1)` present; checked |
| Frozen rational-root enumeration | `XedniFixedFamilyRationalRootPlateau.rationalRoots_eq_certificate`, `rationalRoots_card`, `rationalRoots_nonzero_card` | All 728 ordered coefficient-offset combinations; exact first-occurrence list of 420 fractions, 419 nonzero; checked |
| Reduced coordinates and determinant | `XedniFixedFamilyRationalRootPlateau.rationalRoots_denominator_bound`, `rationalRoots_numerator_bound`, `rationalRoots_coprime`, `rationalRoots_crossdet_ne`, `rationalRoots_crossdet_bound_4202` | Positive denominator at most 11; numerator absolute value at most 191; coprime coordinates; distinct fractions have nonzero determinant of absolute value at most 4,202; checked |
| Sharp determinant bound | `XedniFixedFamilyRationalRootPlateau.rationalRoots_crossdet_bound_2046`, `rationalRoots_crossdet_bound_attained` | Ten checked denominator-class numerator envelopes; every pair has determinant absolute value at most 2,046, attained by two certified fractions; checked |
| All-primes canonical-root plateau | `XedniFixedFamilyRationalRootPlateau.canonical_modular_roots_card_419` | Prime `q > 2046`; exactly 419 nonzero modular images of the normalized rational-root list; checked |
| Raw-to-normalized quotient and raw-family plateau | `XedniFixedFamilyRationalRootPlateau.rawRoot_eq_modularRoot`, `frozen_rawRoot_eq_modularRoot`, `frozen_raw_roots_card_419` | Prime `q > 2046`; all 728 raw public quotients have exactly 419 distinct nonzero modular roots; checked |
| Exact necessary-public-root miss count | `XedniFixedFamilyRationalRootPlateau.frozen_missed_nonzero_targets_card` | Prime `q > 2046`; among `q−1` nonzero target scalars, exactly `q−420` are outside the raw public-relation root set; checked |

Run `lake build FixedFamilyRationalRootPlateau`; `build-fixed-family-root-plateau-output.txt` records the registered build, direct module check, and axiom audit. The checked structural declarations use only `propext`, `Classical.choice`, and `Quot.sound`.

## Finite regular-sum reduction

The reduction bridge now covers an arbitrary finite sequence of affine additions, with a unit slope denominator certified at each step. For a list `P₁,…,Pₙ` of local short-Weierstrass points whose certified sum has endpoint `Q`, the coefficient and point reduction map sends `Q` to the elliptic-group sum of the reduced `Pᵢ`. Consequently, two such sums with the same local endpoint give equal finite-field group sums. This supports relations with varying addends, beyond the repeated-addend chain proved earlier.

The proof is induction on the `RegularSum` certificate. Each final step maps through `map_regularStep` and becomes a genuine group addition by `fieldStep_group_add`; the induction hypothesis then identifies the preceding endpoint with the list sum. The unit-denominator condition is explicit, so vertical and infinity cases need their own certified path before this theorem can be applied to them. In particular, the theorem gives a concrete sufficient condition for the reduction-homomorphism premise used in the fixed-family counting results on any relation represented by such a path.

| Result | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| Reduction of a certified finite sum | `XedniRegularSumReduction.reduce_regularSum` | Commutative source ring, target field, ring homomorphism, elliptic reduced short curve, nonempty `RegularSum` certificate whose every `RegularStep` has a source-unit denominator; checked |
| Equality of two reduced sums | `XedniRegularSumReduction.equal_regularSums` | Two such certificates and equality of their local endpoints; checked |

Run `lake build RegularSumReduction` in this directory. `build-regular-sum-output.txt` records the build and `#print axioms` output; both declarations depend only on `propext`, `Classical.choice`, and `Quot.sound`. The toolchain and Mathlib revisions are pinned as above.

## Certified identity and inverse additions

The finite-sum bridge also accepts the point at infinity and exact inverse cancellation. `ExceptionalSumReduction.lean` represents a local finite point as `some P` and infinity as `none`. Its certified step relation covers addition with infinity, a regular affine chord or tangent, and `P + (−P) = O` in either order. Affine inverse is `(x,y) ↦ (x,−y)` on the short model; the theorem proves that this operation commutes with coordinate reduction. Induction over certified steps then identifies the reduced endpoint with the sum of the reduced inputs. Equal certified endpoints give equal field-group sums.

| Result | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| Negation commutes with reduction | `XedniExceptionalSumReduction.image_neg` | Commutative local ring, target field, ring homomorphism, elliptic reduced short curve, local affine curve point; checked |
| Certified step commutes with reduction | `XedniExceptionalSumReduction.reduce_certifiedStep` | Step is identity on either side, regular affine addition with source-unit denominator, or exact local inverse cancellation; checked |
| Finite certified sum commutes with reduction | `XedniExceptionalSumReduction.reduce_certifiedSum` | Nonempty ordered list and one certificate per addition; checked |
| Equal endpoints imply equal reduced sums | `XedniExceptionalSumReduction.equal_certifiedSums` | Two certified sums with equal local optional endpoints; checked |

The inverse case requires the two local affine points to be exact negatives. A pair that becomes inverse only after reduction needs another argument; the certificate does not silently infer a local group law from residue equality. Run `lake build ExceptionalSumReduction` in this directory. `build-exceptional-sum-output.txt` records the fresh build and `#print axioms` output. Each declaration uses only `propext`, `Classical.choice`, and `Quot.sound`.

## Residue-vertical chord and projective boundary

Let `d=x₂−x₁` and `n=y₂−y₁` for two local affine points on a short-Weierstrass curve. If `d` reduces to zero while `n` reduces to a nonzero field element, the cleared-denominator chord equation `n²=(x₃+x₁+x₂)d²` has no solution `x₃` in the source ring: applying the residue map would make a nonzero square equal zero. Thus the ordinary affine chart cannot supply an integral chord endpoint in this case.

Set `X=n²−(x₁+x₂)d²` and `Y=n(x₁d²−X)−y₁d³`. When `d≠0` over a field, the affine chord coordinates are `X/d²` and `Y/d³`; Lean checks both identities. The standard homogeneous triple `(Xd,Y,d³)` reduces to `(0,−n³,0)` when `d` reduces to zero and `n` remains nonzero. Its middle coordinate is nonzero, so it represents the point at infinity. If the reduced inputs are inverses, their group sum is also infinity by the finite-field elliptic group law.

| Result | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| Affine chord endpoint obstruction | `XedniResidueVerticalObstruction.no_integral_chord_x` | Commutative source ring, residue-field homomorphism, `f(d)=0`, `f(n)≠0`; checked |
| Homogeneous numerator identities | `XedniResidueVerticalObstruction.chord_numerators_correct` | Two curve points over a field and `d≠0`; checked |
| Homogeneous triple reduces to infinity | `XedniResidueVerticalObstruction.homogeneous_chord_at_infinity` | Commutative source ring, residue-field homomorphism, `f(d)=0`, `f(n)≠0`; checked coordinate statement |
| Residue inverse group law and obstruction | `XedniResidueVerticalObstruction.residue_inverse_affine_obstruction` | Elliptic reduced short curve, reduced inputs inverse, `f(n)≠0`; checked |
| Integral witness | `XedniResidueVerticalObstruction.concrete_residue_vertical` | Curve `y²=x³−5x−8`, prime `5`, points `(4,6)` and `(9,−26)`; checked |

The exact-arithmetic replay `python3 run_residue_vertical_witness.py` writes [its result](residue-vertical-witness-result.json). It verifies smooth reduction (discriminant `2 mod 5`), inverse residue points `(4,1)` and `(4,4)`, chord slope `−32/5`, and rational sum `(699/25,18418/125)` on the curve. The coordinate valuations are `−2` and `−3`, respectively. Lean independently checks this witness and the universal coordinate theorems. `lake build ResidueVerticalObstruction` produces `build-residue-vertical-output.txt` with `#print axioms`; every new declaration lists only `propext`, `Classical.choice`, and `Quot.sound`.

The homogeneous result above identifies the three reduced coordinates. The next module constructs their nonsingular projective point and proves equality to the projective zero. A source-ring projective group law still requires proving that the source homogeneous chord triple is on its curve and that reduction respects its group operation.

## Projective point at the residue boundary

`ResidueProjectiveZero.lean` lifts the coordinate conclusion to mathlib's projective point type over the residue field. The reduced chord triple is a nonzero scalar multiple of `(0,1,0)`, so it is nonsingular; its projective class and the zero point are equal. This is a checked point-level consequence of the residue-vertical hypotheses, with no extra ellipticity assumption on the reduced curve.

| Result | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| Triple equals a scaled zero representative | `XedniResidueProjectiveZero.chordResidueTriple_eq_smul_zero` | Commutative source ring, field target, ring homomorphism, reduced chord x-difference zero and y-difference nonzero; checked |
| Nonsingular projective zero point | `XedniResidueProjectiveZero.chordResidueTriple_projective_zero` | Same hypotheses; constructs a nonsingularity proof for the reduced triple and proves its `Projective.Point` equals zero; checked |

The source-ring polynomial identity `Y² = X³ + A X d⁴ + B d⁶`, where `d=x₂−x₁` and `X,Y` are the chord numerators above, is checked in `SourceChordEquation.lean`. It certifies that the source triple `(Xd,Y,d³)` lies on its projective curve. Under the residue-vertical hypotheses, `SourceChordNonsingular.lean` also proves this source representative is nonsingular and reduces coordinatewise to the residue triple. Group-law reduction across all projective addition cases remains open.

Run `lake build ResidueProjectiveZero` in this directory. `build-residue-projective-output.txt` records the fresh build and `#print axioms` output for both checked declarations; each lists only `propext`, `Classical.choice`, and `Quot.sound`.

## Source chord projective equation

The source homogeneous chord triple lies on the short-Weierstrass projective curve over any commutative ring. Write `d=x₂−x₁`, `n=y₂−y₁`, `X=n²−(x₁+x₂)d²`, and `Y=n(x₁d²−X)−y₁d³`. The checked theorem proves `Y²=X³+A X d⁴+B d⁶`, then multiplies by `d³` to obtain the standard projective equation for `(Xd,Y,d³)`. This holds when `d` is a nonunit or zero; no division is used.

The proof subtracts the two input curve equations to get `n(y₁+y₂)=d(x₁²+x₁x₂+x₂²+A)`. A compact four-variable factorization then expresses the weighted equation residual as a multiple of that secant relation plus a multiple of the first point's curve equation. This replaced the earlier expanded normalization attempt and is checked by Lean.

| Result | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| Compact factorization | `XedniSourceChordEquation.chord_key_factor` | Four free ring variables and curve coefficient; checked |
| Full polynomial certificate | `XedniSourceChordEquation.chord_polynomial_identity` | Commutative ring, `X=n²−(2x+d)d²`; checked |
| Secant relation | `XedniSourceChordEquation.secant_relation` | Two source-ring points on the same short-Weierstrass curve; checked |
| Weighted chord equation | `XedniSourceChordEquation.source_chord_weighted_equation` | Same points; no unit-denominator assumption; checked |
| Source projective curve membership | `XedniSourceChordEquation.sourceChordTriple_on_curve` | Same points, with standard homogeneous triple `(Xd,Y,d³)`; checked |

Run `lake build SourceChordEquation` in this directory. `build-source-chord-output.txt` records the build and `#print axioms` for all five declarations. The algebraic lemmas use `propext` and `Quot.sound`; the projective curve membership theorem also uses `Classical.choice` from mathlib's curve definitions. No research claim is encoded as an axiom.

## Source nonsingularity and coordinate reduction

At a residue-vertical chord, the source homogeneous triple `(Xd,Y,d³)` has a nonzero reduced y-coordinate. Its source projective curve equation is established above. If the source representative were singular, its projective `Z` derivative would vanish. Reducing that derivative makes it the square of the nonzero reduced y-coordinate, a contradiction. The Lean module `SourceChordNonsingular.lean` checks this implication and proves that applying the coefficient map to each source coordinate gives exactly the residue triple used by `ResidueProjectiveZero.lean`.

| Result | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| Coordinatewise reduction | `XedniSourceChordNonsingular.map_sourceChordTriple` | Commutative source ring, field target, ring homomorphism, two source curve points; checked |
| Source projective nonsingularity | `XedniSourceChordNonsingular.sourceChordTriple_nonsingular` | Same data plus reduced x-difference zero and reduced y-difference nonzero; checked |

Run `lake build SourceChordNonsingular` in this directory. `build-source-nonsingular-output.txt` records the fresh build and `#print axioms` for both declarations; each lists only `propext`, `Classical.choice`, and `Quot.sound`. The next module strengthens the relevant derivative from nonzero to a unit in the prime-local source ring.

## Unit projective derivative in the prime-local ring

At the residue-vertical chord, the projective `Z` derivative of the source short-Weierstrass equation is `Y²−(2A(Xd)d³+3B(d³)²)` at the homogeneous triple `(Xd,Y,d³)`. The module `LocalChordUnitDerivative.lean` checks this expression against mathlib's projective derivative. Reduction sends the first and third homogeneous coordinates to zero and `Y` to a nonzero element, so the derivative reduces to `Ȳ²≠0`. In a local ring, mathlib's `residue_ne_zero_iff_isUnit` then proves the source derivative is a unit. The theorem is specialized to `Localization.AtPrime P` and the repository's `reduce P` map used in the recorded rational lifts.

| Result | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| Derivative matches mathlib | `XedniLocalChordUnitDerivative.chordZDerivative_eq_polynomialZ` | Any commutative source ring and two source curve points; checked |
| Local derivative is a unit | `XedniLocalChordUnitDerivative.chordZDerivative_isUnit` | Local commutative ring, canonical residue field, reduced chord x-difference zero and y-difference nonzero; checked |
| Prime-local specialization | `XedniLocalChordUnitDerivative.primeLocal_chordZDerivative_isUnit` | Localization of `ℤ` at a prime ideal with the existing `reduce P` map and the same residue conditions; checked |

Run `lake build LocalChordUnitDerivative` in this directory. `build-local-chord-unit-output.txt` records the fresh build and `#print axioms` for all three declarations; each lists only `propext`, `Classical.choice`, and `Quot.sound`.

## Projective addition and residue-vertical reduction

`SourceChordAddition.lean` identifies the homogeneous source chord triple with mathlib's denominator-free `addXYZ` coordinates up to the unit `-1` over any commutative ring. `SourceChordDistinctAddition.lean` proves that unequal source x-coordinates select this chord branch of `Projective.add` and give the same projective point class. `ResidueAdditionZero.lean` uses the broader condition of unequal source y-coordinates: at a residue-vertical chord, reduced y-difference nonzero selects the chord branch even when source x-coordinates coincide. The coordinatewise reduction of the source addition representative then defines the nonsingular zero point of the reduced curve.

`ProjectiveClassReduction.lean` defines `mapClass` by descending coordinatewise ring maps to projective equivalence classes. A ring map sends units to units, so the definition is independent of the representative. At the residue-vertical branch, `mapClass_addMap_residue_vertical` proves that mapping the source `addMap` class equals `addMap` of the mapped input classes on the reduced curve. This is an addition-compatibility theorem for that branch under the exact residue conditions; other branches and a full local reduction group homomorphism remain separate proof obligations.

| Result | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| Chord coordinate identity | `XedniSourceChordAddition.addXYZ_eq_neg_sourceChordTriple` | Commutative source ring, two source curve points; checked |
| Distinct-x addition class | `XedniSourceChordDistinctAddition.addMap_eq_sourceChordClass` | Same data and unequal source x-coordinates; checked |
| Residue-vertical source addition | `XedniResidueAdditionZero.source_add_eq_neg_chord_of_y_ne`, `reduced_source_add_point_zero` | Same source data, field-valued ring map, reduced x-difference zero and reduced y-difference nonzero for the point theorem; checked |
| Ring-homomorphic class map | `XedniProjectiveClassReduction.map_equiv`, `mapClass_mk` | Commutative source and target rings, any ring homomorphism; checked |
| Residue-vertical class compatibility | `XedniProjectiveClassReduction.mapClass_addMap_residue_vertical` | Commutative source ring, field target, reduced x-difference zero and y-difference nonzero; checked |

Run `lake build ProjectiveClassReduction` in this directory. `build-projective-stack-output.txt` records the registered build and `#print axioms` for this stack; every displayed declaration lists only `propext`, `Classical.choice`, and `Quot.sound`. The module-specific `build-*-output.txt` files retain the direct Lean checks made while the shared registration files were leased.

`ProjectiveAddMapDistinct.lean` proves a broader compatibility theorem: if the two mapped representatives remain inequivalent, the source representatives are inequivalent too, and both `addMap` operations select the denominator-free `addXYZ` branch. Mathlib's polynomial `map_addXYZ` identity then makes the class map commute with addition over arbitrary commutative rings. The affine corollaries use either a nonzero mapped x-difference or a nonzero mapped y-difference. The latter includes the residue-vertical branch; the former covers regular distinct-x reduction without requiring the source x-difference to be a unit. The exact hypotheses are in `mapClass_addMap_of_mapped_not_equiv`, `mapClass_affine_add_of_x_ne`, and `mapClass_affine_add_of_y_ne`; all three are checked. Run `lake build ProjectiveAddMapDistinct`; `build-projective-addmap-distinct-output.txt` records the registered build and axiom audit.

## Coalescing inputs and projective normalization

`ProjectiveAddMapCounterexample.lean` gives a smooth-reduction counterexample to extending the raw `PointClass` map to all `addMap` branches. On `E/ℤ : y²=x³−25x+1`, the checked source points `P=(0,1)` and `T=(5,1)` both reduce to `(0,1)` in `ZMod 5`; the reduced discriminant is `3≠0`. Source `addXYZ` is `(625,125,−125)`, so coordinatewise reduction produces the zero vector. The reduced `addMap` instead doubles `(0,1)` and has nonzero projective `Z` coordinate. `raw_mapClass_not_addMap` proves the two resulting projective classes differ.

`ProjectiveCoalescenceObstruction.lean` proves the corresponding general branch obstruction for a ring homomorphism `f : R →+* S`: when source representatives are inequivalent but map to the same vector, mapped source `add` is the zero vector and its raw class map is the zero-vector class. If the target doubling `Z` coordinate is nonzero, the raw class map does not preserve `addMap`. The three checked declarations are `mapped_source_add_vector_zero`, `mapClass_source_addMap_zero`, and `mapClass_addMap_ne_addMap_of_coalescence` in namespace `XedniProjectiveCoalescenceObstruction`. Run `lake build ProjectiveCoalescenceObstruction`; `build-projective-coalescence-output.txt` records the direct Lean check and axiom audit, which lists only `propext`, `Classical.choice`, and `Quot.sound`.

`ProjectiveClassCoalescence.lean` strengthens that obstruction to equality of *reduced projective classes*. Its hypothesis `(f ∘ P) ≈ (f ∘ Q)` allows any unit scaling between reduced representatives. The mapped source chord is still the zero vector. When the target doubling `Z` coordinate is nonzero, the raw class map still fails to preserve `addMap`. This removes dependence on a particular reduced coordinate normalization while keeping the exact source-inequivalence and target-nonzero hypotheses.

| Result | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| Mapped source chord vanishes | `XedniProjectiveClassCoalescence.mapped_source_add_vector_zero_of_equiv` | Commutative rings `R,S`, ring homomorphism `f`, arbitrary Weierstrass curve, source projective classes inequivalent, mapped classes equivalent; checked |
| Raw mapped source sum is zero-vector class | `XedniProjectiveClassCoalescence.mapClass_source_addMap_zero_of_equiv` | Same hypotheses; checked |
| Raw `addMap` incompatibility | `XedniProjectiveClassCoalescence.mapClass_addMap_ne_addMap_of_equiv` | Same hypotheses plus nonzero `Z` of target doubling vector; checked |

Run `lake build ProjectiveClassCoalescence`; `build-projective-class-coalescence-output.txt` records the build and `#print axioms` audit. All three declarations list only `propext`, `Classical.choice`, and `Quot.sound`.

`ProjectivePrimitiveNormalization.lean` proves the exact factorization `addXYZ W P T = (−125) • U` with `U=(−5,−1,1)`, proves `U` lies on the integral curve and has `Z=1`, and proves that the projective class of `U` after reduction equals the target `addMap` doubling class. In the last proof the target doubling vector is exactly `3 • (f ∘ U)` over `ZMod 5`. These facts identify the source factor that must be removed at coalescence; a general local normalization operation remains to be constructed.

`ProjectiveCoalescenceFamily.lean` proves a family behind the concrete example. For each integer offset `d`, take `E_d : y² = x³ − d²x + 1`, `P=(0,1)`, `T_d=(d,1)`, and `U_d=(-d,-1,1)`. Lean checks that both inputs and `U_d` lie on `E_d`, and that `addXYZ E_d P T_d = (-d³) • U_d`. For `d=5^k`, the chord `Z` coordinate is exactly `-5^(3k)`. For every `k≥1`, the source inputs remain inequivalent, the mod-5 curve has discriminant `3` and is elliptic, the primitive source vector reduces to target doubling, and the raw source `addMap` class does not. The growing common factor shows why raw coordinate reduction requires normalization at arbitrarily large 5-adic depths in this family.

`ProjectiveGenericNormalization.lean` proves the general bridge for a source chord with factorization `addXYZ W P Q = c • U`. If the source classes are distinct and a ring homomorphism sends `c` to a unit, the mapped source `addMap` class equals the mapped class of `U`. If the mapped inputs remain distinct as well, the target `addMap` class itself equals the mapped class of `U`. Applying this with `ℤ → ℚ` to the family proves that `U_d` is the actual rational projective sum for every `d≠0`; this is recorded by `rational_generic_add_eq_primitive` and its `5^(k+1)` specialization in `ProjectiveCoalescenceFamily.lean`. Reduction of that integral primitive representative is covered by `primitive_reduction_eq_double`.

`ProjectiveAffineNormalizationUniqueness.lean` closes the choice-of-representative question for the affine integral slice. Over a nontrivial domain, equivalent projective vectors whose `Z` coordinates both equal 1 are identical. In particular, two integral `Z=1` vectors representing the same rational projective class are equal over `ℤ`, so every coefficientwise ring reduction gives the same class. This provides a canonical normalized reduction wherever the rational sum admits an integral affine `Z=1` representative; a local construction for nonintegral affine coordinates or the point at infinity remains a separate step.

`ProjectivePrimitiveUniqueness.lean` extends choice independence to all primitive integral projective triples, including infinity. It records primitivity as an explicit Bézout identity among the three coordinates. If two primitive triples represent the same rational projective class, the rational scaling factor is an integer in both directions and hence an integer unit; their reductions are the same class for every ring map from `ℤ`. A primitive triple maps to a nonzero vector in every nontrivial target ring. This module proves uniqueness and nonvanishing once a primitive representative is supplied.

`ProjectivePrimitiveExistence.lean` supplies that construction. For a nonzero rational triple, multiply each coordinate by the other two canonical denominators to obtain an integral triple in the same rational class. The product of denominators is nonzero. Divide the integral triple by the gcd of its three coordinates; nested integer Bézout identities prove that the resulting triple is primitive, and the nonzero gcd gives the required rational unit scaling. Together with `ProjectivePrimitiveUniqueness.lean`, this establishes existence and choice independence of primitive integral projective representatives for every nonzero rational triple, including infinity.

| Result | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| Primitive representative of integer triple | `XedniProjectivePrimitiveExistence.exists_primitive_int_representative` | Nonzero integer triple; checked |
| Primitive representative of rational triple | `XedniProjectivePrimitiveExistence.exists_primitive_rational_representative` | Nonzero rational triple; checked |

Run `lake build ProjectivePrimitiveExistence`; `build-projective-primitive-existence-output.txt` records the registered build and axiom audit. The resulting reduction on rational projective classes can be defined by choosing the primitive representative, with choice independence supplied by the preceding uniqueness theorem.

`ProjectivePrimitiveReductionMap.lean` constructs that map explicitly. Its domain is the subtype of rational projective classes distinct from the zero-vector class. It chooses a primitive integral representative and maps its coordinates through any ring homomorphism `ℤ →+* S`, where `S` is a nontrivial commutative ring. The result is again a nonzero projective class, and `reduceNonzero_eq_of_rep` proves that every primitive integral representative computes the same result. This establishes the projective normalization step; preservation of the curve equation and compatibility with the full curve group law require their own hypotheses and proofs.

| Result | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| Chosen representative is primitive | `XedniProjectivePrimitiveReductionMap.representative_primitive` | Nonzero rational projective class; checked |
| Chosen representative has the source class | `XedniProjectivePrimitiveReductionMap.representative_class` | Nonzero rational projective class; checked |
| Reduction is choice independent | `XedniProjectivePrimitiveReductionMap.reduceClass_eq_of_rep` | Nonzero rational class, any primitive integral representative with that rational class, ring homomorphism `ℤ →+* S`; checked |
| Reduced class remains nonzero | `XedniProjectivePrimitiveReductionMap.reduceClass_ne_zero` | Same source class, nontrivial commutative target ring; checked |
| Nonzero-class reduction map | `XedniProjectivePrimitiveReductionMap.reduceNonzero_eq_of_rep` | Same hypotheses as choice independence, nontrivial target ring; checked |

Run `lake build ProjectivePrimitiveReductionMap`; `build-projective-primitive-map-output.txt` records the registered build, direct module check, and axiom audit. The displayed axioms are `propext`, `Classical.choice`, and `Quot.sound`.

`ProjectivePrimitiveCurveEquation.lean` lifts the homogeneous Weierstrass equation to nonzero projective classes and proves that the primitive reduction map preserves it. For an integral Weierstrass model `W`, a nonzero rational class satisfying `W.map (Int.castRingHom ℚ)` has a primitive representative satisfying the integral equation. Mapping that representative and the coefficients through any `g : ℤ →+* S` gives a class satisfying `W.map g`. The proof uses the injective cast into `ℚ` to recover the integral polynomial identity, then the ring-homomorphic equation map. It does not require the target ring to be a field; the nonzero target-class theorem requires a nontrivial ring.

| Result | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| Integral representative satisfies curve equation | `XedniProjectivePrimitiveCurveEquation.representative_equation` | Integral Weierstrass model and nonzero rational class satisfying its rational base change; checked |
| Reduced representative satisfies reduced equation | `XedniProjectivePrimitiveCurveEquation.reduced_representative_equation` | Same data and any ring homomorphism `ℤ →+* S`; checked |
| Nonzero curve class maps to reduced curve class | `XedniProjectivePrimitiveCurveEquation.reduceNonzero_onCurve` | Same data with nontrivial commutative target ring; checked |

Run `lake build ProjectivePrimitiveCurveEquation`; `build-projective-primitive-equation-output.txt` records the registered build, direct module check, and `#print axioms` audit. The audited declarations use only `propext`, `Classical.choice`, and `Quot.sound`.

`ProjectivePrimitiveAddition.lean` connects the new reduction map to a noncoalescing addition branch. If the integral `addXYZ` triple of the chosen primitive input representatives factors as `c • U`, with `U` the chosen primitive representative of a rational class `E`, then a nonzero `c` identifies `E` as the rational sum. If the reduced inputs remain projectively distinct and `g c` is a unit, the reduced `addMap` equals the reduction of `E`. The combined theorem supplies both identities from one factorization. The factorization and unit conditions remain explicit; the residue-coalescing branch is a separate proof obligation.

| Result | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| Factorization identifies rational sum | `XedniProjectivePrimitiveAddition.rational_add_eq_of_factor` | Integral model, three nonzero rational classes, distinct integral input representatives, exact `addXYZ` factorization, nonzero factor; checked |
| Normalized reduction commutes with addition | `XedniProjectivePrimitiveAddition.reduceNonzero_add_eq_of_unit_factor` | Same factorization, target ring nontrivial, mapped inputs distinct, mapped factor a unit; checked |
| Joint rational and reduced identity | `XedniProjectivePrimitiveAddition.rational_and_reduced_add_of_unit_factor` | Mapped-input and unit conditions above; checked |

Run `lake build ProjectivePrimitiveAddition`; `build-projective-primitive-addition-output.txt` records the registered build, direct module check, and `#print axioms` audit. The audited declarations use only `propext`, `Classical.choice`, and `Quot.sound`.

`ProjectiveNormalizedCoalescenceFamily.lean` supplies the complementary residue-coalescing result for the exact family `E_d : y² = x³ − d²x + 1`, with `d = 5^(k+1)`. It first embeds any primitive integer triple as a nonzero rational projective class and proves that the global `reduceNonzero` map agrees with reduction of that representative. For every natural `k`, the rational sum of `P=(0,1)` and `T=(d,1)` is the primitive class of `U=(-d,-1)`, whose normalized reduction equals the reduced doubling class. The reduced discriminant is `3` in `ZMod 5`, while direct reduction of the unnormalized integral chord class differs from that doubling class. This gives an arbitrary-depth, smooth-reduction witness for the normalization boundary.

| Result | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| Primitive representative computes global reduction | `XedniProjectiveNormalizedCoalescenceFamily.reduce_classOfPrimitive` | Primitive integer triple, ring map to nontrivial commutative ring; checked |
| Rational sum and normalized reduced sum | `XedniProjectiveNormalizedCoalescenceFamily.power_family_normalized_add` | Natural `k`, exact family offset `5^(k+1)`, residue map to `ZMod 5`; checked |
| Raw class map differs from reduced addition | `XedniProjectiveNormalizedCoalescenceFamily.power_family_raw_map_differs` | Same family and offset; checked |
| Smooth reduced curve | `XedniProjectiveNormalizedCoalescenceFamily.power_family_reduced_smooth` | Same family and offset; checked |

Run `lake build ProjectiveNormalizedCoalescenceFamily`; `build-projective-normalized-coalescence-output.txt` records the registered build, direct module check, and `#print axioms` audit. The audited declarations use only `propext`, `Classical.choice`, and `Quot.sound`.

| Result | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| Primitive reduction remains nonzero | `XedniProjectivePrimitiveUniqueness.primitive_map_ne_zero` | Integer triple with Bézout certificate, homomorphism to nontrivial commutative ring; checked |
| Rational equality descends to integer unit scaling | `XedniProjectivePrimitiveUniqueness.int_equiv_of_rational_equiv_primitive` | Two primitive integer triples and rational projective equivalence; checked |
| Primitive reduction is choice independent | `XedniProjectivePrimitiveUniqueness.primitive_reduction_independent` | Same hypotheses and any ring homomorphism from `ℤ`; checked |

Run `lake build ProjectivePrimitiveUniqueness`; `build-projective-primitive-uniqueness-output.txt` records the registered build and `#print axioms` audit.

| Result | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| Unit-normalized equivalence is equality | `XedniProjectiveAffineNormalizationUniqueness.affine_z_one_equiv_iff_eq` | Nontrivial commutative domain, two vectors with `Z=1`; checked |
| Integral affine representative uniqueness | `XedniProjectiveAffineNormalizationUniqueness.integral_affine_representative_unique` | Two integer vectors with `Z=1`, equal images as rational projective classes; checked |
| Reduction independence | `XedniProjectiveAffineNormalizationUniqueness.integral_affine_reduction_independent` | Same rational-class hypotheses and any ring map from `ℤ`; checked |

Run `lake build ProjectiveAffineNormalizationUniqueness`; `build-projective-affine-uniqueness-output.txt` records the registered build and axiom audit.

| Result | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| Factored mapped source sum | `XedniProjectiveGenericNormalization.mapClass_addMap_eq_primitive_of_unit_factor` | Commutative rings, ring homomorphism, inequivalent source representatives, exact factorization, mapped factor a unit; checked |
| Factored target sum | `XedniProjectiveGenericNormalization.addMap_map_eq_primitive_of_unit_factor` | Same factorization and unit condition, mapped representatives inequivalent; checked |
| Rational family sum | `XedniProjectiveCoalescenceFamily.rational_generic_add_eq_primitive`, `power_family_rational_add_eq_primitive` | Integer offset `d≠0`, respectively offset `5^(k+1)`; checked |

Run `lake build ProjectiveGenericNormalization ProjectiveCoalescenceFamily`; `build-projective-generic-normalization-output.txt` and `build-projective-coalescence-family-output.txt` record the registered builds and axiom audits.

| Result | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| Parametric factorization | `XedniProjectiveCoalescenceFamily.source_chord_factorization` | Integer `d`, fixed curve and points as above; checked |
| Exact power-family chord `Z` | `XedniProjectiveCoalescenceFamily.power_family_chord_z_exact` | Natural `k`, offset `5^k`; checked |
| Smooth reduction and primitive compatibility | `XedniProjectiveCoalescenceFamily.power_family_reduced_curve_elliptic`, `power_family_primitive_reduction` | Natural `k`, offset `5^(k+1)`; checked |
| Raw class-map incompatibility at every depth | `XedniProjectiveCoalescenceFamily.power_family_raw_mapClass_not_addMap` | Natural `k`, offset `5^(k+1)`; checked |

Run `lake build ProjectiveCoalescenceFamily`; `build-projective-coalescence-family-output.txt` records the build and axiom audit. The audited declarations use only `propext`, `Classical.choice`, and `Quot.sound`.

| Result | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| Source chord factorization | `XedniProjectivePrimitiveNormalization.source_chord_factorization` | Fixed integral curve and points above; checked |
| Primitive point equation and coordinate | `XedniProjectivePrimitiveNormalization.primitive_on_curve`, `primitive_z_eq_one` | Fixed integral curve and vector `U`; checked |
| Primitive reduction agrees with target doubling | `XedniProjectivePrimitiveNormalization.primitive_reduction_eq_double` | Fixed ring homomorphism `ℤ → ZMod 5` and projective classes; checked |

Run `lake build ProjectivePrimitiveNormalization`; `build-projective-primitive-normalization-output.txt` records the build and axiom audit. The four declarations use only `propext`, `Classical.choice`, and `Quot.sound` among their audited axioms.

## Reproduction

From this directory, run `python3 run.py`, `python3 generate_coordinate_certificates.py --check`, `python3 generate_curve_equation_certificates.py --check`, `python3 generate_recorded_regular_steps.py --check`, `python3 generate_finite_group_chains.py --check`, `python3 generate_exact_chain_multipliers.py --check`, `python3 generate_public_point_reduction.py --check`, `python3 generate_all_signed_public_relations.py --check`, `python3 run_adaptive_coefficient_census.py`, `lake build AffineReductionBridge`, `lake build RegularChainReduction`, `lake build RegularGroupLaw`, `lake build PrimeLocalReduction`, `lake build LocalZModReduction`, `lake build RationalLocalWitness`, `lake build CoordinateCertificates`, `lake build RationalCurveBridge`, `lake build CurveEquationCertificates`, `lake build RationalRegularStep`, `lake build RecordedRegularSteps`, `lake build FiniteGroupChains`, `lake build ExactChainMultipliers`, `lake build PublicPointReduction`, `lake build SignedPublicRelation`, `lake build AllSignedPublicRelations`, `lake build UniformRelationBound`, and `lake build AdaptiveCoefficientBoundary`, and `lake build SelectorRelationBound`, and `lake build SharedTargetRelation`. The Lean version is pinned in `lean-toolchain`, mathlib in `lake-manifest.json`; the corresponding `build-output*.txt` files record the theorem builds and `#print axioms` output. The replay and certificate generators need only the Python standard library and the source JSON at the sibling path named in the protocol.
