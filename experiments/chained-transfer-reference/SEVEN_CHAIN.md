# A transported degree49 Jacobian hop over F101

This is the written geometric proof for CT21, extending the frozen Phi
construction in SEVEN_JACOBIAN_PROOF.md. Native certificates and partial Lean
lemmas support the explicitly named steps below; they are producer assertions
with unsigned scientific standing. No full Lean construction of the varieties
or regular quotient is claimed. [pcc:unverified]

## Exact objects and maps

Work in characteristic101. Let J0 and J1 be the canonically polarized
Jacobians of

    C0: y² = x⁶ + 6x⁴ + 13x² + 56,
    C1: y² = x⁶ + 26x⁴ + 42x² + 68.

The previously constructed Phi:J0→J1 is a separable (7,7)-isogeny, with
PhiHat Phi = Phi PhiHat = [7]. Original elliptic factors are E1=(1,46),
E2=(44,21), of orders109/113 and traces−7/−11. Their selected degree7
images are E1'=(26,58), E2'=(69,50). Coordinates here are short
Weierstrass (a,b). Let alpha=alpha1×alpha2. The old/new product pulls P0/P1
and norms N0/N1 use the checked quotient matching, including the component
swap and scales21 on C1. They satisfy Pi Ni=[2], Ni Pi=[2] and
Phi P0=P1 alpha. These are geometric identities from the prior proof,
not divisions on a finite point group. [pcc:unverified]

Let R0:J0→T0 be the accepted Richelot map, where

    T0 = Jac(y²=x⁶+55x⁵+71x⁴+54x³+74x²+75x+31).

The actual Phi action on J0[2] transports Ker R0 to a kernel K1 in J1[2].
It selects R1:J1→T1, with

    T1 = Jac(y²=x⁶+91x⁵+94x⁴+27x³+19x²+26x+95).

Both R0/R1 are separable (2,2)-isogenies and their polarized adjoints satisfy
RiHat Ri=Ri RiHat=[2]. All four rational Jacobian groups have12317=109·113
classes. Their orders are correctness controls, not an isomorphism test.
The new desired hop is Psi:T0→T1. [pcc:unverified]

## Actual geometric kernels and root identity

All coefficient arithmetic uses the same old cubic field
F101[T]/(T³+6T²+13T+56). The common F101⁶ bridge has flat generator
gamma=T+s, s²=2 and modulus[33,46,2,18,56,12,1]. Native adapters verify
inverse/root/Frobenius equations and canonical coordinates against the old
tower. New roots are derived from the actual elliptic7 images; the cubic
modulus is not silently replaced by the new curve's quotient cubic.
[pcc:unverified]

First, the actual P0 image of Ker alpha has49 distinct classes, all killed
by7. Its2401 additions and Frobenius closure are checked; actual eigenvalues
are5 and6. P0 has2-primary kernel, so is injective on7-torsion. Since
Phi P0=P1 alpha and deg Phi=49, these are exactly Ker Phi. This is49 kernel
points, not the whole2401-point geometric J0[7]. [pcc:unverified]

For the two-action, take every product half of the four graph points in
Ker P0. There are64 actual product4-torsion lifts. Their P0 images cover all
16 geometric J0[2] classes, each four times. Their P1 alpha images agree on
each fiber, cover the16 target branch classes, and satisfy all256 additions
and Frobenius compatibility. Thus the table computes the restriction of the
already global Phi; it does not define a putative map by scalar labels.
[pcc:unverified]

In the old ±Frobenius root order, Ker R0 is the matching
(0,4),(1,5),(2,3). Its actual images give the new matching
(0,5),(1,3),(2,4). All six new roots are distinct, the matching is disjoint
and Frobenius stable, and the factor product is exactly C1. Its determinant
is33; the raw target is[78,66,56,53,91,29,88]. The square normalization
is raw ordinate w=47Y, giving exactly the T1 equation above. The source and
target sextics are smooth. Existing Richelot formulas therefore construct
the geometric polarized quotient, not merely a proposed kernel label.
[pcc:unverified]

The selected-pairing constructor checks those conditions independently of
the old first-kernel fixture assertion. Invalid indices, reused branches,
degenerate matchings, duplicate roots, wrong source products and unstable
matchings are rejected. The old fixture selection and normalization checks
remain in force. [pcc:unverified]

## Global F101 descent of the actual normalized Richelot maps

A Frobenius-stable kernel gives a rational quotient up to polarized
isomorphism, but does not by itself fix the twist of a displayed target.
We remove that ambiguity for these exact maps. Native root certificates
enumerate all120 unique fractional-linear transformations taking one fixed
ordered branch triple to an arbitrary ordered triple. Only the identity
preserves all six branch points, for BOTH T0 and T1. This is a complete
geometric test: any algebraic-closure transformation preserving the branch
set is determined by three roots, so its coefficients already lie in the
declared splitting field F101⁶. No bounded search over arbitrary coefficients
or assumption about rational automorphisms replaces this argument.
[pcc:unverified]

Each genus2 hyperelliptic curve has only its hyperelliptic involution over
the identity of the branch line; the complete stabilizer test therefore gives
curve automorphisms {1,iota}. Strong Torelli (Milne, Jacobian Varieties,
Theorem12.1) identifies the origin-preserving polarized Jacobian automorphisms
with {+1,−1}. This is a written geometric bridge; the native test alone does
not implement Torelli. [pcc:unverified]

Let sigma be F101 Frobenius and R one of R0/R1. The maps R and sigma(R)
have the same stable kernel and the same principally polarized target.
The quotient universal property gives sigma(R)=a R for a target
automorphism a. Both pull back the target polarization to2 times the source
polarization, so a preserves it. Pullback by an isogeny is injective on
polarization homomorphisms: if R^vee b R=0, surjectivity of R and the finite
kernel of R^vee force the connected image of b to be zero. Thus a is +1
or−1. [pcc:unverified]

The actual correspondence has a rational input D with nonzero rational
image of odd order (the109 source controls supply witnesses for both R0
and R1). Therefore sigma(R)(D)=sigma(R(D))=R(D). The choice a=−1 would
imply2R(D)=0, contradicting its nonzero odd order. Hence a=+1 and R is
defined over F101. The adjoints descend as well, since the canonical source
and target polarizations do. This proves global descent of the displayed
normalization; finite rational-output tests alone were not used as a density
argument. [pcc:unverified]

## Full geometric two-kernel inclusion and regular quotient

On T0[2], R0Hat has kernel Ker R0Hat of order4 and therefore image4.
The identity R0 R0Hat=[2] places that image in Ker R0, also of order4,
so they are equal. All group schemes here are finite etale because101≠2.
Native code additionally constructs all six actual T0 branch roots, all16
two-classes and the actual R0Hat images. It checks four preimages per image
and all256 additions. It computes R1 on all16 J1[2] classes as well,
checking its four-element kernel and every addition. [pcc:unverified]

The actual Phi2 table sends Ker R0 exactly onto Ker R1. Consequently

    C = R1 Phi R0Hat : T0 → T1

kills every geometric point of T0[2]. The actual three-table composition
checks all16 cases explicitly. Since T0[2] is finite etale, this is scheme
kernel inclusion. Multiplication[2] is the quotient by T0[2]. The abelian
variety quotient property (Milne, Abelian Varieties v2.0, Remark8.12) gives
a unique REGULAR homomorphism Psi with

    C = Psi [2].

Uniqueness and C/[2] being defined over F101 imply Psi is defined over F101.
C is a surjective isogeny; hence so is Psi. Degrees multiply:

    deg C = 4·49·4 = 784,
    deg[2] on a surface = 16,
    deg Psi = 49.

The kernel is separable because101 does not divide49. The construction is
global and does not assert that geometric two-torsion points can be halved
by an odd rational group order. [pcc:unverified]

## Polarized dual and commuting squares

The adjoint composite is CHat=R0 PhiHat R1Hat. Globally,

    CHat C = R0 PhiHat [2] Phi R0Hat = [28] on T0,
    C CHat = [28] on T1.

Since C=Psi[2], these become [4]PsiHat Psi=[28] and
[4]Psi PsiHat=[28]. Hom groups of abelian varieties are torsion-free:
if a homomorphism is killed by a nonzero integer, its connected image is
contained in a finite group scheme, so the homomorphism is zero. Cancel4
IN HOM, not in the geometric point groups. We obtain both global dual
norms[7], so Psi is a (7,7)-isogeny for the canonical polarizations.
[pcc:unverified]

Compose C=Psi[2] on the right with R0 and use R0Hat R0=[2]. This gives
(Psi R0−R1 Phi)[2]=0. Multiplication[2] is surjective geometrically,
so

    Psi R0 = R1 Phi.

The reversed factor similarly gives PsiHat R1=R0 PhiHat. These squares
are equalities of global homomorphisms. They are not inferred only from
the109 tested source points. [pcc:unverified]

## Faithful rational evaluator and source controls

Both rational groups have odd order12317, so the global Psi evaluates as
R1 Phi R0Hat applied to[6159]D. The production evaluator instead moves
the same divisions into the two explicit elliptic coordinates. Because
Phi=P1 alpha N0/2, it computes

    Psi(D) = R1 P1 alpha (N0(R0Hat D)/4),
    PsiHat(Q) = R0 P0 alphaHat (N1(R1Hat Q)/4).

Inverse4 is82 modulo109 and85 modulo113. These divisions use known group
orders and point multiplication, never an unknown DLP scalar. Both versions
are compared on all109 original source scalars. The complete graph tests
evaluate each production map on EVERY rational class exactly once; norms
and paired sums reuse those actual outputs. No production evaluator reads
a corpus or a scalar-labelled table. [pcc:unverified]

Let j0:E1→J0 be the first elliptic pull, and S(P)=R0 j0(P).
For every P in the order109 source,

    Psi(S(P)) = R1 Phi j0(P),
    N0 R0Hat PsiHat Psi R0 j0(P) = ([28]P,0),
    N1 R1Hat Psi R0 j0(P) = ([4]alpha1(P),0).

The first-coordinate inverse28 is74 modulo109; inverse7 on the transferred
Jacobian subgroup is78. All109 scalar relations, nonzero image/order109,
both naive-halving comparisons, commuting square and direct coordinate/
recovery checks pass. Both entire12317-class Psi domains pass bijections,
both dual[7] norms,12317 deterministic paired-addition cases per direction,
wrong-curve rejection and canonical coefficientwise F101 descent.
These are not all12317² addition pairs; global additivity comes from the
regular construction above. [pcc:unverified]

## Distinct unpolarized F101 Jacobians

The old/new elliptic pulls embed their factors, as proved in the Phi report.
Both cross-kernels meet their embedded elliptic2-torsion trivially: native
code checks all12 nonzero intersection controls, for two factors on each
side. Because each Richelot kernel is2-primary, the compositions R0 j0
and R1 j1 remain embeddings of the ORIGINAL elliptic curves E1 and E1'
into T0 and T1. This is stronger than merely mapping isogenous elliptic
curves onto these subvarieties. [pcc:unverified]

Over F101 the trace−7 and trace−11 elliptic isogeny classes have no cross
homomorphisms (Tate/Weil). Each surface, isogenous to the corresponding
product, consequently has a unique connected elliptic subvariety of each
trace type: it is the identity component of the kernel of a complementary
projection. Any unpolarized F101-isomorphism T0≅T1 must carry the embedded
trace−7 curve E1 isomorphically to the unique such curve E1'. But their
j-invariants are12 and87. Hence no such surface isomorphism exists.
This argument uses rational trace-type uniqueness and makes no unproved
algebraic-closure nonisomorphism claim. Psi therefore reaches a genuinely
different F101 Jacobian from the previously accepted T0. [pcc:unverified]

## Evidence, formalization and limits

Consumer certificates:b9242a (49-kernel),2f72c8 (64-lift action),c2a691
(full R1),c1b585 (full geometric composite and elliptic intersections),
afd0a9 (109-chain controls),2b4435 (correct actual equations/full Psi).
The erroneous source equation in unsigned9b9e0a is preserved and explicitly
corrected by2b4435; no test used its mistyped coefficients. Root9a1c6b pins
the complete target automorphism certificate. All records remain unsigned.
[pcc:unverified]

ChainTransport.lean supplies six structural implications;SevenJacobian.lean
supplies functional descent/Hom cancellation/recovery helpers.
RichelotDescent.lean proves four conditional odd-sign/quarter lemmas;
gate4 and localPCCf4ced8 statement bindings all pass. There are90 written
source lemmas in the complete census, with zero trusted native uses.
Formalization stays partial: finite fields, Picard functoriality, regular
quotients, polarized duality, Torelli and elliptic-subvariety uniqueness
remain explicit written dependencies. Retain every failed and passing
native/Lean attempt; do not weaken statements to disguise these gaps.
[pcc:unverified]

Primary texts checked: Kunzweiler, Efficient computation of (2^n,2^n)-isogenies,
Sections3.1–3.2/Lemma6/Propositions7–8; HLP arXiv math/9809210v1
Section3.2; Milne, Abelian Varieties v2.0(2008), Remark8.12; Milne,
Jacobian Varieties, June12 2021, Theorem12.1 and its uniqueness proof.
The last PDF is https://www.jmilne.org/math/xnotes/JVs.pdf with SHA256
36c3f09c7462dbbd4ae1f8b81a02bd9ff84f03c5a346351d7d5d78fc3f173486.
Earlier primary PDF hashes are retained in the frozen Phi proof. KB/ecdb
were unavailable; no novelty audit or new atlas identity is inferred.
[pcc:unverified]

This is same-prime coefficient descent. It is no cross-characteristic map
or prime-field Weil restriction. Both surfaces admit explicit elliptic
projections; the original source subgroup occupies only one factor.
Future total-cost controls must include the direct alpha1 elliptic route,
source/destination rho and BSGS, existing index calculus, construction,
transport, solve, recovery and verification. No solver or timing experiment
was admitted or run; S3/livebudget gates and independent signed validation
remain open. Consumer and root frozen-ledger forks block integration without
an accepted reconciliation retaining both histories. [pcc:unverified]
