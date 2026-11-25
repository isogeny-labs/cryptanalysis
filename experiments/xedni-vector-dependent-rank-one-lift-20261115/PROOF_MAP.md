# Proof map

Lean `v4.35.0-rc4` and Mathlib `021c46bdd042f67b538b9f9871d556a93713a9a9` are pinned in `formal/`. The imported `AdaptiveInverseLift.lean` is an exact copy of the checked source at SHA-256 `7e553b80159c0f2408e58a7498cce59de8f972145c1c788210ff52f31c9b58b8`. `formal/build-output.txt` records the successful build and `#print axioms`.

| Result | Lean declaration | Exact hypotheses | Status |
| --- | --- | --- | --- |
| Public relation supplies one common scalar preimage | `XedniVectorDependentRankOneLift.public_factorization` | Field `K`; `b≠0`; `aU+bV=0` | Checked |
| Public-group relation is equivalent to one common rank-one preimage | `XedniVectorDependentRankOneLift.public_relation_iff_rank_one` | Additive commutative group `A`; integers `a,b`; multiplication by `b` is bijective on `A`; public points `U,V` | Checked |
| Bézout certificate inverts multiplication on a torsion group | `XedniVectorDependentRankOneLift.coefficient_bijective_of_torsion` | Additive commutative group `A`; every point killed by integer `q`; integers `b,c,d` with `bc+qd=1` | Checked |
| Torsion public relation is equivalent to a rank-one preimage | `XedniVectorDependentRankOneLift.torsion_public_relation_iff_rank_one` | Same `q`-torsion and Bézout hypotheses; integer `a`; public points `U,V` | Checked |
| Rank-one multiples satisfy the coefficient relation | `XedniVectorDependentRankOneLift.rank_one_relation` | Any additive commutative group; integers `a,b`; common point `P` | Checked |
| Rational point specialization | `XedniVectorDependentRankOneLift.rational_rank_one_relation` | Exact `liftPos x y` on `modelRat x y`; all integer `x,y,a,b` | Checked |
| Reduction commutes with both constructed multiples | `XedniVectorDependentRankOneLift.rank_one_reduction_commutes` | Additive commutative groups `H,A`; additive homomorphism `ρ : H →+ A`; point `P`; integers `a,b` | Checked |
| Reduced constructed pair retains its relation | `XedniVectorDependentRankOneLift.rank_one_reduced_relation` | Same additive homomorphism and point; integers `a,b` | Checked |
| Reduced model has discriminant `−1664` | `XedniVectorDependentRankOneLift.baseModel_discriminant` | Every natural modulus `p` | Checked |
| Reduced model is elliptic away from discriminant primes | `XedniVectorDependentRankOneLift.baseModel_isElliptic` | Prime `p`; `p ∤ 1664` | Checked |
| Reduced model is elliptic for the frozen eight-field panel | `XedniVectorDependentRankOneLift.panel_baseModel_isElliptic` | `p ∈ {47,101,191,211,251,281,347,349}` | Checked |
| Centered coordinates satisfy the finite curve equation | `XedniVectorDependentRankOneLift.reduced_generator_equation` | Natural `p`, integer `x,y`, and the displayed equation `y²=x³−x−2` in `ZMod p` | Checked |
| Selected finite point has the centered coordinates | `XedniVectorDependentRankOneLift.reducedGenerator_coordinates` | Previous equation; `ZMod p` nontrivial; `baseModel p` elliptic, supplied by `panel_baseModel_isElliptic` on the frozen panel | Checked |
| Integral/rational model and reduction | `XedniAdaptiveInverseLift.rational_model`, `reduction_model` | Integer `x,y`; reduction additionally assumes the displayed finite-field point equation | Checked imported declarations |
| Public relation recovers the target scalar | `XedniDirectRelation.finite_relation_recovers` | Nonzero coefficient sum, compatible public sampled points | Checked in earlier PR; source SHA-256 `ab7e93ecca78edab04edb9047bd181bf830e686e4470aba3b602272dd857bf53` |
| Reduction of constructed multiples to the exact public points | `audit_sage.py` | Eight specified prime-order curves, every one of 6,136 saved events | Independently checked Sage; Lean bridge open |

The remaining Lean bridge requires a formal good-reduction map from the rational elliptic-curve point group to the specified finite-field curve, including the point at infinity and denominator cases, and a proof that this map sends `liftPos x y` to `reducedGenerator p x y hpoint`. The finite model's nonsingularity on the panel, its point equation, and the finite point's coordinates are checked in Lean. Scalar-multiplication compatibility follows from the checked additive-homomorphism lemma once that map is constructed. The concrete reduction of every constructed multiple is checked by Sage.
