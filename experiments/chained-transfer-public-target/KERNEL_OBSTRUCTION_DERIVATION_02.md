# Fixed q223 obstruction to a further rational polarized two-isogeny

2026-11-13. Standing unsigned; written derivation with computational premises
and partial Lean formalization. This result concerns only the original fixed
J=Jac(C)/F223 and polarized(2,2,2) quotients over F223. Nativec88589 and
read-only replay907dfc are not signed execution proofs. [pcc:unverified]

## Actual geometric input

The source is E/K, K=F223[z]/(z³−3), #E(K)=11092292=4ell,
ell2773073. The actual Ciani quartic's original15 coefficients and canonical
maps are recorded in V2_MAPS_01.md. Native510d03 finds its rational2-Sylow
C4, using the written Ciani isogeny order bound; thus geometric J[2] has
exactly2 Frobenius-fixed points. Nativee887a9 independently constructs and
checks all28 actual bitangents, whose Frobenius cycles are1,3,6,6,6,6.
[pcc:unverified]

Over an algebraic closure, J[2] is a nondegenerate six-dimensional
symplectic F2 space. Frobenius preserves the pairing because it fixes mu2.
Mumford's theta-characteristic quadratic/parity theorem identifies the
odd theta characteristics equivariantly with the28 odd quadratic refinements.
For a smooth nonhyperelliptic genus3 canonical plane quartic, these are
exactly its28 bitangents: an odd degree2 theta characteristic has a unique
effective divisor, and its doubled divisor is a line section. This is a
standard geometric bridge, not an identification with eight Weierstrass
points on the actual quartic. [pcc:unverified]

## Complete finite symplectic calculation

The original Smith module enumerates135 distinct Lagrangians in an abstract
symplectic model. The new native test audits rank3, closure and isotropy of
each and all4096 pairing pairs through an explicit basis. The standard
count135 follows independently by counting ordered isotropic bases:
63*30*12 divided by7*6*4. The symplectic ordered-basis count is
63*32*15*8*3*2=1451520. Every examined matrix is distinct and symplectic,
so this full cardinality gives completeness. All matrices and their
compatibility/count bytes are retained, including rejected matrices.
[pcc:unverified]

Nativec88589 matches both actual predicates: exactly2 fixed vectors and odd
quadratic-form cycles1,3,6,6,6,6. There are120960 matching matrices, each
having one stable Lagrangian. Identity and transvection controls give135
and15 stable kernels; their odd fixed counts are28 and16. The unchanged
original S8 representative6+1+1 has one stable kernel. [pcc:unverified]

Replay907dfc reads every one of the1451520 saved records, leaving all2366
input hashes including the13063688-byte binary unchanged. Its alternative
algorithm uses Gaussian rank, quadratic truth-table fixed counts for three
powers, and sixth-power identity. It recovers120960 compatible actions and
a representative centralizer of size12. The representative's conjugacy
class therefore has1451520/12=120960 elements. Both input predicates are
conjugacy invariants; its class lies in the compatible set and has the same
finite cardinality, hence equals that set. The original representative's
kernel count1 is conjugacy invariant. This gives a second mathematical
route to the unique-kernel conclusion, with the same explicit unsigned
finite-computation premise. [pcc:unverified]

## Identifying the original kernel, including its polarization

Put A=Res(K/F223)E with its natural principal polarization, geometrically
the product polarization on the three conjugate elliptic curves. The Ciani
degree-two quotient maps pi_i:C→E_i give

    Phi=sum pi_i^*: A→J,    N=(pi_i*): J→A.

Norm/pullback duality under canonical Jacobian polarizations makes N and
Phi dual. This follows functorially from Picard/Albanese autoduality, not
from fitting a scalar on rational samples. Source isomorphisms, signs and
translations used by the actual coordinate models preserve this induced
polarized statement. Frobenius permutes the three quotient maps, so both
maps and the natural product polarization descend to F223. [pcc:unverified]

The written V4 correspondence calculation in V2_MAPS_01.md proves [pcc:unverified]
N Phi=[2] on A and Phi N=[2] on J. Dual isogenies have equal degree; their
product has degree64, so each has degree8. The polarization identity is

    N^*lambda_A = 2lambda_J.

Since char223 does not divide8, ker N is an etale subgroup of order8;
Phi N=[2] places it in J[2]. The polarization descent criterion implies
the Weil pairing is trivial on ker N, hence it is a rank3 maximal-isotropic
subgroup. Because N is defined over F223, this kernel is Frobenius-stable.
It is therefore the unique stable Lagrangian given by the calculation.
[pcc:unverified]

Every F223-rational polarized(2,2,2) quotient of J has a stable Lagrangian
kernel, hence that same kernel. The quotient and its descended principal
polarization are unique up to principally polarized isomorphism, so its
target is A. Geometrically A's product theta divisor is reducible. A smooth
connected genus3 Jacobian's canonical theta divisor is a translate of W2,
the image of the irreducible symmetric square of the curve, hence is
irreducible. Thus A cannot be a canonically polarized Jacobian of a smooth
connected genus3 curve. No further F223-rational polarized(2,2,2) Jacobian
target exists from this fixed J. [pcc:unverified]

## Formal scope and continuing routes

Five exact named Lean bindings392a95/039ca3/9f99f1/e7e736/ea637d prove
closed arithmetic, conjugacy transport of stability, isometry transport of
isotropy, monotonic finite Boolean counting and inclusion plus equal count
implying equal membership. Both unchanged original gates audit8 declarations
including3 generated trueCount equations, zero trusted. The first producer
build's two redundant generalizing annotations are preserved6956b2; only
those tactic annotations changed and all5 statement hashes remain identical.
Actual finite-group completeness, native execution, theta/Galois/Weil
pairing and polarized-isogeny/Jacobian geometry are written bridges and
remain outside this partial Lean formalization. [pcc:unverified]

The obstruction does not cover other degrees, fields, polarizations,
curves, arbitrary degree8 homomorphisms, longer chains or ECDLP security.
In particular J→A can be followed by a DIFFERENT gluing quotient A→J',
giving a longer nondual chain even though the first step is the norm.
Investigate A's rational gluing kernels and explicit Ciani targets next;
do not identify the same dual pair's [2] composition with a new chain.
Computational advantage remains unestablished. [pcc:unverified]

Primary references actually read: Mumford, *Theta characteristics of an
algebraic curve* (1971),pp181–182; Milne, *Abelian Varieties*,Theorem11.1,
Proposition16.8 and Remark16.9; Milne, *Jacobian Varieties*,Section5,
Theorem5.1 and Summary6.11. Exact URLs, file digests and scope notes are in
evidence/kernel-primary-math-01/sources.json. These references support the
stated standard bridges; they do not certify the native execution.
[pcc:unverified]
