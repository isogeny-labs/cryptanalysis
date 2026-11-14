# Actual odd source transfer and its global interpretation

2026-11-13. Native de87bd follows prospective protocol e9234b.
All standing is unsigned; geometric interpretation is a written argument,
with feasible universal Lean implications developed separately.
[pcc:unverified]

## Actual source, target and coefficient evidence

Over K=F223[z]/(z^3-3), let
E:y²=x³+(214+144z+205z²)x+(137+218z+9z²).
The actual normalized Kohel degree13 map gamma has target
Eprime:y²=x³+(196+168z+69z²)x+(8+82z+207z²),
with immutable equation identifier
N4-E13-short-936b863521fdce08d2724c468f27979cb39d9443d082b4be14209bb08f408414.
The entire kernel polynomials, rational maps and cross-polynomials are in
evidence/odd-source-acceptance-02/all-native-records.json.xz.
The old quadratic-to-short shift and field/model tags are retained.
[pcc:unverified]

The source order is11092292=4*2773073, trace-2724 over K. The full degree84
division polynomial is squarefree. Exact iterated qK Frobenius gcds have
degrees0,0,6,0,0,12. Dividing the sixth-power gcd by the third-power gcd
gives the degree6 forward kernel; the original SEA quotient-ring check
returns eigenvalue2. Repeating on Eprime gives the degree6 third-power gcd
as normalized dual kernel, with eigenvalue4. Both kernels have no K-rational
x roots, checked by their first Frobenius gcd. No large extension or
point-generator placeholder is used. [pcc:unverified]

For each normalized map write x'=N/D and y'=y*T/D², T=N'D-ND'.
The complete original polynomial arithmetic gives

    (x³+a*x+b)*T² = N³*D + aPrime*N*D³ + bPrime*D⁴.

Both whole residuals vanish; each deliberate change bPrime→bPrime+1
produces a nonzero residual. Numerator/denominator degrees are13/12 and
their gcd is1. These are whole coefficient identities, not the finite
random evaluations performed by the older check_x_identity helper.
Original engines and that helper are unchanged. [pcc:unverified]

## Why these rational expressions are homomorphisms

The identity defines a nonconstant rational map E→Eprime. Smooth projective
curves and the proper target extend it across every missing point; Milne,
Abelian Varieties, Theorem3.1 records the extension fact in greater
generality. At infinity the normalized map has x'~x and y'~y, hence sends
O to O. Milne Corollary2.2 then makes it a group homomorphism. Its degree is13:
the rational x-map has degree13 and comparison with the two degree2
elliptic x-projections cancels that factor2. Since char223 does not divide13,
this isogeny is separable. This argument uses the actual smoothness,
coprimality and leading coefficients from the native certificate.
[pcc:unverified]

The second normalized Kohel target has coefficients13^4*a,13^6*b.
The K-isomorphism (X,Y)→(X/13²,Y/13³) identifies it with E. Composing that
isomorphism with the second normalized map gives delta:Eprime→E.
The complete x AND y rational cross-products establish

    delta gamma=[13]_E,      gamma delta=[13]_Eprime.

Both composite x-maps have coprime numerator/denominator of degrees169/168.
The reference uses the raw division-polynomial convention, including
leading13 in psi13:

    x13=(x*g13²-4*(x³+a*x+b)*g12*g14)/g13²,
    y13=y*x13'/13.

The y formula follows by pullback of dx/(2y) under multiplication[13].
The independent original affine multiplication engine agrees on all
specified source and target points. Equality on the dense rational-map
domain and extension gives the global identities, hence delta is the
dual degree13 isogeny. [pcc:unverified]

Neither kernel has a rational nonidentity point: a finite affine kernel
point would have a K-root of its denominator, and the exact first-power
gcd rules this out. Thus gamma and delta inject their finite rational
groups in opposite directions. Their orders are equal and gamma is a
bijection E(K)→Eprime(K). This also transfers the original order certificate
without an unsupported point-counting claim. On the ell subgroup, inverse
transport is [639940]delta because13*639940=1+3*ell. On the whole rational
group [3413013]delta is inverse because13*3413013=1+4*11092292. The two
inverses have different scopes. No scalar is inferred from a DLP table.
[pcc:unverified]

Native de87bd checks36 source and36 target points, both[13] compositions,
1024 homomorphism pairs in each direction, every rational2-torsion point,
two off-curve rejections, a nonzero exact-ell image and all five unchanged
public targets. Test-only known answers stay outside runtime map inputs.
The first compile failure1ea2d5 preserves seven nonexistent-square-API
errors and all2452 unchanged selected inputs; the correction only calls
the existing original multiplication API. No scientific outcome is omitted.
[pcc:unverified]

## Different product and the proposed next Jacobian transfer

The actual source j-conjugates are
(166,136,127),(166,135,47),(166,175,49).
The target conjugates are
(217,167,46),(217,10,10),(217,46,167).
The two sets are disjoint. A polarized isomorphism between the corresponding
products over the algebraic closure would have degree-one columns: the
sum of the nonnegative degrees of the three component homomorphisms in
each column is1. Each column therefore contains an elliptic degree1
isomorphism, which the disjoint j sets exclude. Thus the canonically
principally polarized products A=Res(E) and Aprime=Res(Eprime) differ.
This is stronger than renaming a coordinate model of the same polarized
product; it is not a computational advantage statement. [pcc:unverified]

The next construction must actually glue Aprime, retaining all three
2-torsion roots, both HLP signs and every singular/nonsquare/duplicate
outcome. It must supply a smooth Cprime/F223, an actual origin and complete
PhiPrime:Aprime→Jac(Cprime), NormPrime in the reverse direction, with both
dual[2] identities. They are not supplied by this source-isogeny phase.
[pcc:unverified]

CONDITIONAL on that separately completed construction, define
F=PhiPrime*Res(gamma)*Nold and
G=PhiOld*Res(delta)*NormPrime. The two dual[2] identities and both[13]
source identities give GF=FG=[52]. The degree would be8*13³*8=140608,
and F would have polarization multiplier52. Since52 is coprime toell,
it would preserve the chosen DLP and have inverse [159985]G on its odd
image, using52*159985=1+3*ell. All three final statements are conditional
until the new Jacobian maps are constructed and checked. [pcc:unverified]

If such a new Jacobian were F223-ppav-isomorphic to old J, its degree8 norm
would identify a rational polarized2-kernel of old J. The earlier unique
kernel result would force its quotient Aprime to be polarized-isomorphic
to A, contradicting the actual disjoint-j product argument. This provides
a conditional endpoint discriminator; no actual new endpoint is claimed
here and no extension-field Jacobian isomorphism is ruled out by the
F223-unique-kernel premise. [pcc:unverified]

The remaining requirements are explicit gluing/Picard maps, feasible formal
bridges, clean independent full/CI replay and whole raw-data publication.
Benchmark admission, complete transport costs and strongest ECDLP references
remain necessary to establish any computational advantage. The source maps
and polynomial identities alone establish no cost improvement.
[pcc:unverified]
