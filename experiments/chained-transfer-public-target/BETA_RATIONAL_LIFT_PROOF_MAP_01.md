# Proof map: quadratic rational lifts and the quadratic Picard backend

All standings below are unsigned. The actual Ciani quotient, Picard functor,
Weil restriction, Frobenius and norm identities retain their explicit written/
native bridges. The Lean module proves the structural implications with these
hypotheses; it does not assume the rational lifting conclusion. [pcc:unverified]

| Claim | Exact declaration | Hypotheses and conclusion |
| --- | --- | --- |
| ea1776 | QuadraticRationalLift.quadratic_fixed_lift | Ordinary abelian-group/homomorphism laws, surjective geometric Phi commuting with Frobenius, exponent2 kernel and F³=1 on kernel imply every F-fixed target has an F²-fixed lift. |
| 59b526 | QuadraticRationalLift.lift_images_equal | Two homomorphisms, kernel containment and equal Phi images imply equal Psi images. |
| 1706b2 | QuadraticRationalLift.four_torsion_lift_bound | N Phi(a)=2a and 2N(x)=0 imply 4a=0 for every lift of x. |
| 8ffe1f | QuadraticRationalLift.quadratic_kernel_fixed_is_rational | F²(c)=c and F³(c)=c imply F(c)=c. |
| 42dab6 | QuadraticRationalLift.finite_group_hypothesis_control | Exact finite C4×C2 model checks all listed group/hom/automorphism/surjectivity/kernel2 laws, an F³-kernel failure and no F²-fixed lift of the nonzero target. |
| 637454 | QuadraticNormIdentity.norm_multiplicative | Exact polynomial norm identity for arbitrary a,b,c,d,n:Int. Field reduction and nonsquare hypotheses are separate. |

The original 4.34.1/4.35.0 gates pass20 group-module declarations including seven
named roots and generated proof helpers, plus one norm-module declaration, zero
trusted. Six named structural roots in the group module have no axioms. Its
finite control and the exact Int norm theorem use only propext and Quot.sound.
Every reported declaration has an actual #print axioms log. The five group
bindings and one norm binding pass the unchanged original PCC locally. There
are66 unique partial bindings with the inherited60; this is not66 geometric
formalizations. [pcc:unverified]

Nativefb21de checks all16 four-torsion points on each actual elliptic curve,
all256 additions each, both degree13 compositions and the actual F³/F⁶ actions.
Nativeb28edc checks the actual quadratic-field operations and Picard scalar
extension. Complete small-prime class closures148/356/1324 and their generating
edges match the original engine; the223 class inputs are a bounded ordered
list. Genuine extension-class tests and their finite scope are in the native
record. These are finite implementation checks. [pcc:unverified]

IDC1hd724979553e97e07 is an identity.certificate/v1 record for quadratic norm
multiplicativity. The unchanged producer native issuer/checker verifies64
sealed and32 extra points over its specified Mersenne field. A separate exact
integer coefficient expansion and the Int Lean theorem support the polynomial
over Z. The certificate's proof pointer names the actual checked source; the
native checker does not run Lean. The omitted-imaginary-term process rejects101.
This certificate does not replace the conditional group proof or prove actual
Picard geometry. [pcc:unverified]

Preserved failures: b1e193 first finite-control elaboration/encoding build;
4ad5ee producer outside-root rejection; af90a4 nested workspace metadata101;
literal-editor initializer inventory assertion and identity-caller API/dependency
build failures. Corrected producer checks use byte-identical sources within its
own root. Original verifiers, source, tests and old18 workflows are unchanged.
[pcc:unverified]
