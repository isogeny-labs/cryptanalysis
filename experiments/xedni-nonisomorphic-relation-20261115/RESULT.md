# Qualified rank-one curve family yields 38 checked rational relations

The frozen `(1,2)` relation vector gives **38 rational relations** among the admitted point pairs of the qualified nonisomorphic rank-one family. Each relation was replayed as `U+2V=O` on its exact rational curve in checked Sage and reduced to the matching public-group equation. All 38 rows recover the fixture scalar 17 through `(t₁+2t₂)/3 mod q`, followed by independent scalar multiplication against the public target.

The pinned Lean theorem `rank_one_relation_iff` states the structural reason: for any nontorsion generator `P`, `(aP)+2(bP)=O` if and only if `a+2b=0`. Its companion `recover_of_relation` proves the scalar-recovery algebra over any field where 3 is nonzero. The specific curve ranks, generator identities, good reductions, and rational group equations are checked in the Sage audit; the full elliptic arithmetic witness is not formalized in Lean.

## Complete frozen query law

The workload has `Q=17G`, `R(t)=Q−tG`, and every ordered `(t₁,t₂)∈[0,q)²` on the eight selected fields. Each field keeps its base curve; the proved rank-one nonbase curves at `p=571` and `p=677` are additional arms. The cap is `|k|≤4` in each curve's proved rational generator. Identity and duplicate pairs are retained as statuses before the admission and relation test.

| Field prime | Subgroup `q` | Qualified model arms | Admitted distinct relation tests | Rational relations | First relation query in full order |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 313 | 331 | base | 56 | 4 | 4,323 |
| 421 | 439 | base | 56 | 4 | 5,727 |
| 431 | 419 | base | 56 | 4 | 5,467 |
| 547 | 571 | base | 56 | 4 | 7,443 |
| 571 | 599 | base, `u3` | 112 | 8 | 3,019 |
| 593 | 313 | base | 12 | 2 | 4,714 |
| 617 | 293 | base | 56 | 4 | 3,829 |
| 677 | 353 | base, `u3` | 112 | 8 | 1,789 |
| **Total** | | **10 arms** | **516** | **38** | |

The complete producer retained **1,471,112 public queries** and **1,954,522 per-model membership statuses** in compressed raw rows. Across those statuses it recorded 8,530 identity, 4,260 duplicate, 1,941,216 outside-cap, 478 admitted nonrelation, and 38 rational-relation outcomes. It charged 516 rational group-relation tests and the same number of matched public-vector tests. The preceding setup contains all 24 rank-screen attempts, including two unresolved exact ranks, and two generator-completeness checks; those costs are not silently assigned zero.

On `p=571`, the added `u3` arm first relates at query 3,019 versus 7,807 for the base arm. On `p=677`, it first relates at query 1,789 versus 4,609. These are positions in the frozen lexicographic schedule. The additional arm also doubles per-query model membership work on those two fields, and the family was selected after the rank screen. The counts therefore describe relation yield and search work for this panel, without a wall-time or same-target speed comparison.

## Verification and proof map

| Result | Lean declaration or independent check | Exact scope |
| --- | --- | --- |
| Rank-one relation criterion | `XedniNonisomorphicRelation.rank_one_relation_iff` | Any additive commutative group and point with `n•P=0 → n=0`; coefficients `a,b∈ℤ` |
| Scalar recovery | `XedniNonisomorphicRelation.recover_of_relation` | Any field with `3≠0`; public offsets `t₁,t₂` and relation `(w−t₁)+2(w−t₂)=0` |
| Two extra rational curves have rank one, trivial torsion, complete generators and distinct `j` invariants | Parent Sage rank screen and this independent Sage audit | Exact curves and field primes 571, 677 |
| Every saved status, rational group equation, public equation and scalar replay | `audit.py` through the checked repository Sage launcher | All 1,471,112 query rows and 516 admitted distinct per-model tests |

The formal package pins Lean `v4.35.0-rc4` and Mathlib `021c46bdd042f67b538b9f9871d556a93713a9a9`. `lake build RankOneRelation` passes and both `#print axioms` reports list only standard Lean foundations. The source contains no `sorry`, `admit`, custom research axiom, or unverified native evaluation. `lean4checker --fresh` was unavailable on this host. The checked Sage runtime receipt, complete raw statuses, producer and audit outputs, and file seal make the finite-panel result replayable.

For every positive row, the same `(1,2)` coefficient vector satisfies the directly computable reduced-group relation `R₁+2R₂=O`. The next falsifier is whether a curve-selection policy can reveal useful coefficients before paying for an equivalent public relation search, with rank screening, failed curves, and target-dependent work all charged in a paired same-target comparison.
