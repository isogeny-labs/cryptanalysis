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

The source-ring polynomial identity `Y² = X³ + A X d⁴ + B d⁶`, where `d=x₂−x₁` and `X,Y` are the chord numerators above, is now checked in `SourceChordEquation.lean`. It certifies that the source triple `(Xd,Y,d³)` lies on its projective curve. The subsequent source nonsingularity and group-law reduction across all projective addition cases remain open.

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

## Reproduction

From this directory, run `python3 run.py`, `python3 generate_coordinate_certificates.py --check`, `python3 generate_curve_equation_certificates.py --check`, `python3 generate_recorded_regular_steps.py --check`, `python3 generate_finite_group_chains.py --check`, `python3 generate_exact_chain_multipliers.py --check`, `python3 generate_public_point_reduction.py --check`, `python3 generate_all_signed_public_relations.py --check`, `python3 run_adaptive_coefficient_census.py`, `lake build AffineReductionBridge`, `lake build RegularChainReduction`, `lake build RegularGroupLaw`, `lake build PrimeLocalReduction`, `lake build LocalZModReduction`, `lake build RationalLocalWitness`, `lake build CoordinateCertificates`, `lake build RationalCurveBridge`, `lake build CurveEquationCertificates`, `lake build RationalRegularStep`, `lake build RecordedRegularSteps`, `lake build FiniteGroupChains`, `lake build ExactChainMultipliers`, `lake build PublicPointReduction`, `lake build SignedPublicRelation`, `lake build AllSignedPublicRelations`, `lake build UniformRelationBound`, and `lake build AdaptiveCoefficientBoundary`, and `lake build SelectorRelationBound`, and `lake build SharedTargetRelation`. The Lean version is pinned in `lean-toolchain`, mathlib in `lake-manifest.json`; the corresponding `build-output*.txt` files record the theorem builds and `#print axioms` output. The replay and certificate generators need only the Python standard library and the source JSON at the sibling path named in the protocol.
