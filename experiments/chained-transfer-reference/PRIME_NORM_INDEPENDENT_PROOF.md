# Independent T20 prime-field norm and completed pullback

This proof concerns only the frozen F101 model and two covers in
PRIME_NORM_REPLAY_PROTOCOL.md (ec2a8b). Producer root6298 supplies their
construction and positive-adjoint normalization. The new consumer checks
the explicit functions independently; it does not reconstruct the producer's
Richelot map. Computational standing remains unsigned. [pcc:unverified]

## Curve maps and their degree

Let C have monic equation f from the frozen fixture, and let E_i have the
fixed short Weierstrass equation. Each cover is

    X=n(z)/q(z)^2,    Y=y*m(z)/q(z)^3.

The consumer checks the complete coefficient identity
f*m²=n³+a*n*q⁴+b*q⁶, canonical coefficients, coprime n/q, squarefree q,
and both signed infinity limits. The independent Lean statements
PrimeNormPullback.actual_first_normalized_cover and
actual_second_normalized_cover prove these actual characteristic101
identities; actual_ordinate_normalization proves the raw/monic scale.
The distinct roots of q are unramified source points: the identity gives
f*m²=n³≠0 there. Each of the four pole points has X pole order2 and Y pole
order3, so maps to the elliptic point O with local degree1. Thus the map
extends over these points. The two source infinities have finite opposite
images with the exact limits in the fixture. Smooth projective completion
extends the rational function map everywhere. [pcc:unverified]

The rational function n/q² on the z-line has degree4 by coprimality and
the displayed polynomial degrees. On C it has degree8, since the
hyperelliptic projection has degree2. The elliptic X-function has degree2,
so the actual curve cover has degree4. In characteristic101 it is separable
because its degree is not divisible by101. This uses function-field towers,
not the size of a finite point sample. [pcc:unverified]

## Independent finite-algebra norm

Take a valid balanced input with finite support u and ordinate v. Remove
the full gcd(u,q²), retaining its multiplicity. Those points all push to O.
For the remaining quadratic support u=z²+a*z+b, reduce the two cover
coordinates to X=A+Bz and Y=C+Dz in F101[z]/u. This evaluation uses units
in that algebra and chooses no support roots. [pcc:unverified]

If B≠0, T=A+Bz is an invertible linear change of the algebra generator.
Its image Mumford representation is

    u_E=T²+(aB−2A)T+(A²−aAB+bB²),
    v_E=C−DA/B+(D/B)T.

The exact support and ordinate substitutions are independently formalized
by image_support_substitution and image_ordinate_substitution. The cover
identity implies v_E²≡T³+a_E*T+b_E modulo u_E. The existing generic
genus1 Cantor engine validates and reduces this actual divisor. These
algebra statements also hold when u is nonreduced, so repeated support is
retained. This route differs from the producer's explicit sum-coordinate
formula. [pcc:unverified]

If B=0 and D=0, the finite images coincide and the existing elliptic group
law doubles (A,C). If B=0 and D≠0, comparing the linear term in the source
relation modulo u gives 2C=aD, so the two image ordinates are opposite.
For repeated u this forces the coincident image to be two-torsion, whose
double is O as well. The algorithm checks 2C=aD before accepting this case.
The linear-support case is an ordinary point evaluation. [pcc:unverified]

If the original finite degree was d and the balanced plus count was p,
the degree-zero source class is

    D_fin+(p−1)∞+ +(1−d−p)∞−.

Because the signed infinity images are T and −T, the missing contribution
is (2p+d−2)T. The degree here is the ORIGINAL finite degree, including
every removed pole. Using the smaller post-removal degree would change
the class. Coherent translation of the entire cover cancels on degree-zero
divisors; it is a positive control, not a false global-sign mutant.
[pcc:unverified]

## Completed quartic pullback

For affine P=(X,Y) on E, let U be the monic form of n−X*q² and set
V=Y*q³*m^(-1) modulo the ORIGINAL U. Every nonidentity rational point
has Y≠0 since the checked target orders109/113 are odd. The coprime n/q
and cover equation imply gcd(m,U)=1: a common zero would have q≠0 and
force Y²=0. The consumer explicitly checks the inverse and V²=f modulo U.
The universal identity cleared_fibre_factorization and the conditional
unit_ordinate_recovery formalize this finite-algebra implication. They
make no unsupported characteristic101 claim about the separate fixed
2^61−1 universal identity certificate. [pcc:unverified]

The whole P fibre has degree4. Write d=deg U and delta=4−d. A missing
point is necessarily a source infinity, so X equals the corresponding
infinity X-value. The two infinity images are distinct and opposite,
since their nonzero Y-values lie in odd order groups. Consequently all
delta missing points have the sign selected by Y. [pcc:unverified]

In particular the exact characteristic101 identities are

    n0−10*q0²=z²+52z+56,
    n1−71*q1²=z²*(96z+24).

The first has finite degree2 and two equal signed infinities. The second
has finite degree3, including a repeated finite point at z=0, and one
infinity. The two literal identities are proved by actual_first_degree_drop
and actual_second_degree_drop. Keeping U and V modulo the full U retains
the repeated point's ordinate jet. Replacing U by its squarefree part is a
different divisor. [pcc:unverified]

Let K=∞+ +∞−. The pole fibre is div(q)+2K, so the pullback of P−O is
the completed P fibre minus2K. If its infinity multiplicities are nplus
and nminus, the existing semireduced reducer takes plus=nplus−1:

    D_fin+(nplus−2)∞+ +(nminus−2)∞−
      =D_fin+(plus−1)∞+ +(1−d−plus)∞−.

The exact integer accounting is formalized in balanced_completion_accounting.
For a generic degree4 finite fibre plus=−1. For O the degree-zero class is
the identity. The adapter delegates all actual reduction to the unchanged
old balanced engine, after validating the complete finite scheme. It adds
no alternate Cantor or infinity reduction algorithm. [pcc:unverified]

## Picard maps, composition and finite recovery

Pushforward and pullback of the actual covers induce group maps on
Picard groups (Galbraith corrected8.3.8/8.3.10). Same-component norm after
pullback is[4] by the cover degree. On the F101 rational groups every
cross-component homomorphism vanishes because109 and113 are coprime.
This rational argument alone does not prove a geometric cross-map theorem
over arbitrary extensions. [pcc:unverified]

The producer's written polarization/Richelot argument identifies the norm
pair M and positive adjoint Mdag globally, with both compositions[4] and
degree16. The independent consumer's full12317-class acceptance, if it
passes, will test its adapters against that claim on the entire rational
domain, including its own group operations and the F101² pointwise oracle.
It is not substituted for the producer's global Picard proof.
[pcc:unverified]

Since4 is prime to12317, public recovery can multiply Mdag(M(D)) by9238,
or multiply the elliptic components by82 and85 BEFORE Mdag. These
constants are independently proved in actual_public_inverse_constants.
Neither map uses a discrete-log label or enumeration inverse. They are
inverses on the fixed finite rational groups; the global degree16 isogeny
has no global inverse morphism. Runtime coordinate arithmetic needs no
extension field. The separate oracle and class enumeration do use extension
arithmetic as validation/setup. [pcc:unverified]

## Formal and empirical boundaries

Eleven exact Lean declarations have separately bound local PCC pass
verdicts (evidence/prime-norm-lean-01,380d2b); standard foundation axioms
only,zero trusted-native declarations. Full curve/Picard functors,
projective completion and local jets, compatibility with the old reducer,
and the polarization bridge remain written and native obligations. The
upstream replay executes the producer implementation; it is not an
independent Richelot reconstruction. No timing, baseline improvement or
solver advantage follows from correctness of this representation.
[pcc:unverified]
