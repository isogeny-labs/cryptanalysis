# Nonisomorphic Jacobians and forced rational Richelot backtracks

Both accepted non-split targets, over F17 and shifted F101, have six-cycle
branch Frobenius. Source/target2-torsion over Fp³ has cardinalities16/4,
which obstructs any unpolarized Fp-Jacobian isomorphism. Among all15
Richelot matchings the target has only its previous dual; a next rational
Richelot step must backtrack. These are exact-fixture results, not an
obstruction to other degrees, products, extensions or other covers.
Claims954795/4823b5 bind unsigned correctness evidence. [pcc:unverified]

## Fixed inputs and complete extension checks

Use the first accepted map for E19/F17, determinant11/raw scale3, and the
frozen shifted E109/F101, determinant63/raw scale22. Their source cubics
are[2,2,0,1] and[56,13,6,1]. The immutable source767c945a0 already passes
exact-head focused43022364261: native25/reference46 tests,1 old benchmark
ignored, formatting,strict Clippy and source guards(PCC46a880). This result
does not cover the subsequent CT16 source changes. [pcc:unverified]

`accepted_targets_frobenius_two_torsion_and_next_kernels` reconstructs each
accepted map, computes all three target-bracket discriminants in the checked
cubic field and finds all three nonsquare. The existing quadratic adjunction
splits them in Fp⁶: for nonsquare D, take sqrt(D/NR)*s,s²=NR. All six
distinct roots satisfy the monic target equation. Labeling actual Frobenius
orbits gives permutation[1,2,3,4,5,0] in both cases. No target factorization
type was assumed by the discovery test. [pcc:unverified]

For every unordered branch pair {i,j}, construct the degree2 balanced class
Wi+Wj−K as u=(X−ri)(X−rj),v=0,plus=0. In each Jacobian all15 classes
are validated,nonzero,distinct and killed by doubling; with identity these
give all16 geometric2-torsion points. They are all Frobenius⁶-fixed.
Coefficient Frobenius³ fixes every source class but only three nonzero
target classes. Completed y=0 correspondence fibers give kernel4/image4
on this geometric2-torsion. Every256 addition relation and Frobenius
equivariance of these branch images pass. [pcc:unverified]

## Written geometric bridge and nonisomorphism proof

In odd characteristic a smooth genus2 Jacobian has2⁴ geometric2-torsion
points. Every nonzero point has a unique unordered two-branch-point
description Wi+Wj−K. The fifteen explicit distinct classes therefore
exhaust it. Frobenius acts on these classes by permuting their branch pair;
the balanced infinities are rational. This standard branch-pair geometry is
a written input, not a theorem formalized by the finite Lean certificates.
See Galbraith corrected ch.10 and the primary Richelot kernel description
in Kunzweiler§§3.1–3.2. [pcc:unverified]

The source branch action is(012)(345); its cube is identity. The target
action is(012345); its cube is(03)(14)(25). Only the three opposite pairs
are fixed as unordered two-element sets, so the complete2-torsion over
Fp³ has16 source versus4 target elements, including identity.
[pcc:unverified]

Any Fp-isomorphism of abelian varieties restricts to a bijection of their
geometric2-torsion and commutes with Frobenius, hence with its cube. It
would induce a bijection of those fixed sets, contrary to16≠4. Thus these
isogenous Jacobians are not isomorphic over Fp, even without preserving a
polarization. This strengthens the earlier F17 curve-PGL2 distinction;
it does not assert an absence of geometric isomorphisms over extensions.
[pcc:unverified]

## Why every next rational Richelot step backtracks

A Richelot kernel is a maximal isotropic subgroup specified by a perfect
matching on the six branches. It is defined over Fp exactly when that
unordered matching is Frobenius stable. Enumerating all15 matchings for
the actual six-cycle gives only[(0,3),(1,4),(2,5)]. It is also the matching
obtained directly from the three target H factors, so it is the previous
dual kernel. The original nondegenerate determinant assures that dual
returns the source up to its explicit normalization. [pcc:unverified]

There is a direct combinatorial proof: under a six-cycle a nonopposite
edge has an orbit of six edges,too many for a matching of three edges.
An opposite edge instead has an orbit of three edges,which is precisely
that matching. Therefore these exact targets have no rational next
nonbacktracking Richelot kernel. Reversing the accepted hop composes to[2];
counting it as a new destination or an unexplored chained advantage would
be incorrect. Other-degree isogenies,extension-defined kernels and other
starting covers remain outside this conclusion. [pcc:unverified]

## Formal certificates and limitations

Crypto `TargetFrobenius.lean` has seven core Lean lemmas,gate7,
PCC8c5ee5: source cube identity,source/target fixed branch-pair lists,
unique stable target matching,a moved target pair,generic cube intertwining
and a conditional obstruction to a commuting map with right inverse.
These check finite combinatorics and the function-level isomorphism
argument. They do not construct finite fields,Jacobians or the geometric
branch-pair identification. No new axioms were added. [pcc:unverified]

Raw proposal/first discovery/regression/Clippy receipts are
evidence/target-frobenius-proposal-01.txt,target-frobenius-01.txt/02.txt
and target-frobenius-clippy-01.txt. The first result is retained separately
from subsequent frozen regression assertions and the256 addition controls.
Standing remains unsigned; both group layers use Cantor and no independent
whole-map verifier was substituted by this test. [pcc:unverified]

Reproduce the targeted test with Rust1.99.1,or run check.sh for current
complete CI. The new full47-test replay is pending; the previous46-test CI
is bound to its exact immutable source. Report diagram and every page of
target-frobenius-report.pdf are inspected before publication.
[pcc:unverified]

Next research must consider a genuinely different route rather than repeat
these closed rational Richelot neighbors. Cost advantages still need an
actual destination solver and full construction/transport/recovery accounting.
No benchmark,solver gain,prime-field attack or cross-prime descent follows.
S3/live-budget,KB/vault and crypto frozen-ledger/archive blockers remain;
production/catalog/large-prime coverage is still open. [pcc:unverified]
