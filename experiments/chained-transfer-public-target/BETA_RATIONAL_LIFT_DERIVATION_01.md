# Quadratic rational lifts for the matched odd-degree Jacobian factor

The conditional lifting implication is checked in Lean; actual elliptic
four-torsion coordinates and Frobenius actions are checked natively. Nativefb21de,
Lean7f5766 and the five exact bindings in evidence/beta-rational-lift-bindings-01
are unsigned. The complete rational beta evaluator is still being implemented.
Prospective5be5e0 was published in3422ccb4 before this code. [pcc:unverified]

## Constructive lifting lemma

Let A and J be abelian groups with Frobenius endomorphisms FA,FJ, and let
Phi:A→J be a surjective homomorphism commuting with Frobenius. Suppose
2c=0 and FA^3(c)=c for every c in ker(Phi). For any FJ-fixed x choose a lift a
and put c=FA(a)−a. Equivariance makes Phi(c)=0. Then

    b=a+FA(c),       Phi(b)=x,       FA^2(b)=b.

Indeed FA(a)=a+c and

    FA^2(b) = FA^2(a)+FA^3(c)
             = a+c+FA(c)+c = a+FA(c).

The equality Phi(FA(c))=FJ(Phi(c))=0 gives the asserted image. The proof
constructs the correction explicitly; it never assumes rational surjectivity.
Lean QuadraticRationalLift.quadratic_fixed_lift quantifies over every fixed x,
with ordinary abelian-group and homomorphism laws, geometric surjectivity,
kernel exponent2 and kernel cube-period stated separately. [pcc:unverified]

If a second homomorphism Psi kills ker(Phi), any two lifts a,b of the same x
give Psi(a)=Psi(b): a−b lies in ker(Phi), so Psi(a)−Psi(b)=0. This is
lift_images_equal. If N Phi(a)=2a and 2N(x)=0, every lift of x satisfies
4a=2N(x)=0; this is four_torsion_lift_bound. Finally a kernel point fixed
by FA^2 and FA^3 is fixed by FA, by applying FA to the quadratic equality.
This is quadratic_kernel_fixed_is_rational. [pcc:unverified]

## Why the kernel Frobenius hypothesis matters

Take A=C4×C2, J=C2, Phi(a,b)=a mod2 and

    FA(a,b)=(a+2b mod4,b+a mod2),       FJ=identity.

FA is an automorphism, Phi is surjective and equivariant, and its kernel
has exponent2. But FA^2(a,b)=(3a mod4,b). Every lift of the nonzero J point
has odd a, so none is FA^2-fixed. For instance c=(0,1) is in the kernel
and FA^3(c)=(2,1) differs from c. The Lean finite_group_hypothesis_control
checks all group/homomorphism/automorphism/surjectivity/kernel conditions
and this failure by kernel-checked decide. Fin8 encodes a+4b. Nativefb21de
independently checks all eight explicit pairs. This is a finite-group
control; no abelian-variety counterexample is asserted. [pcc:unverified]

## Specialization to the existing Ciani quotient

Keep k=F223, K=k[z]/(z^3−3), ell=2773073 and the actual old elliptic curve

    E: y^2=x^3+(214,144,205)x+(137,218,9),       #E(K)=4ell=11092292.

The degree13 target has a=(196,168,69),b=(8,82,207). Let
A=Res(K/k)E, A1=Res(K/k)E1 and let the existing written complete maps be
Phi0:A→J0 and N0:J0→A, with N0 Phi0=[2]. The Ciani/V4 quotient argument
identifies Phi0 as a separable isogeny with kernel contained in A[2].
These actual geometric identifications remain the written/native bridges
in the existing proof maps; the new abstract Lean module does not replace them.
[pcc:unverified]

All three nonzero E[2] points are defined over K, as checked by the original
field polynomial roots and actual doubling. Over K the Weil restriction
splits into the three conjugate factors, and their two-torsion coordinates
are K-rational. Thus FA^3 fixes A[2], hence ker(Phi0). The constructive lemma
therefore gives a lift in A(k2) for every x in J0(k). [pcc:unverified]

For a rational cofactor-four class x2, N0(x2) is a rational two-primary point
of A. The actual E(K) two-primary group is C2×C2, so 2N0(x2)=0. Consequently
each quadratic lift has order dividing4. It suffices to search the actual
sixteen points of E[4](L), where L=k[w]/(w^6−3). This reduces the missing
cofactor lift to a bounded, explicit geometric precomputation. It does not
compute the missing Picard images by itself. [pcc:unverified]

The field identifications are

    z=w^2,       v=w^3,       k2=k[v]/(v^2−3),       A(k2)=E(L).

The automorphism of L fixing K and restricting to k2/k Frobenius is the
third coordinate Frobenius. Accordingly FA on this representation is F^3.
The K embeddings fixing k2 use exponents0,4,2. Taking the three F^2-conjugate
fibre ideals produces the same unordered product. The basis1,w^2,w^4 spans
L over k2: multiplication by1,v produces all six monomial coordinates,
using w^7=3w. Nativefb21de checks v^2=3, F^2(v)=v and F(v)≠v. [pcc:unverified]

For each nonzero two-torsion branch root e_i, its half has

    x=e_i ± sqrt((e_i−e_j)(e_i−e_k)).

Both square roots of the curve's y-coordinate give the four halves. The
native code retains every resulting point, checks doubling to the specified
branch point, checks order dividing4 and all256 ordered additions on each
actual curve. Both actual rational degree13 maps are base-changed from their
published polynomial certificates, and both compositions equal[13] on every
point. The 32 point records include source/target coefficients, all coordinates,
doubles, Frobenius images and isogeny images. Coordinate F has actual off-curve
mutation examples, while F^3 preserves each K-defined curve. [pcc:unverified]

## How this completes the cofactor part of beta when implemented

For matched HLP(1,0), existing derivation03 gives the global factor

    beta Phi0=Phi1 gamma,       F=[2]beta,       betaDual beta=[13].

Its target quartic is the actual15-coefficient model
[1,121,174,193,172,175,11,124,77,78,48,58,89,63,164], with P0=(1,0,84),
modelCiani-Jac-odd-product-v1-7ea9d0f9d1a48a48489425beab48274fca7bd0848e47a0bac3a027c01601e2c4.
For each x2, choose a four-torsion lift a in E(L) and compute Phi1 gamma(a).
Actual kernel containment makes this independent of the lift. Since the global
factor is k-defined, the output is rational. The planned native control will
check both facts on every lift and all four actual rational cofactor classes.
[pcc:unverified]

For arbitrary x in J0(k), ell≡1 mod4 gives x2=[ell]x and xodd=x−x2. The planned
evaluator sums the geometric cofactor value and [1386537]F(xodd). The latter
equals beta(xodd) because2·1386537=ell+1. This is a conditional complete
rational-point algorithm once the genuine quadratic Picard arithmetic and
base-changed complete fibre ideals are implemented and checked. Its precomputed
table has at most sixteen four-torsion inputs, and contains no odd-subgroup log.
Complete global closed rational coordinates remain a separate requirement.
[pcc:unverified]

## Formal and computational scope

Both original standalone proof gates, Lean4.34.1 and4.35.0, pass20 declarations
including seven named roots and generated proof helpers, zero trusted.
The six named structural roots use no axioms. The finite control uses only
propext and Quot.sound. Exact original PCC bindings ea1776,59b526,1706b2,8ffe1f,
42dab6 locally pass and remain unsigned. Original path rejection4ad5ee is kept;
the successful producer gate checks a byte-identical source inside its own root.
The initial finite-control elaboration failureb1e193 is preserved. [pcc:unverified]

Quadratic Picard implementation has finite nativeb28edc controls: complete
small-prime base closures148/356/1324 and all generating edges; genuine
non-base extension classes; all nonzero inverses including49728 at223.
The223 non-base Picard/complete-fibre map remains next. Its explicit field
operations must handle a+p*b modulo v^2−nu; integer arithmetic modulo p^2
does not define this field. All original785 inputs, arithmetic22 source inputs
and old18 workflows remain unchanged. These are development correctness checks,
with no performance timing, calibrated cost or advantage claim. [pcc:unverified]

Sources checked: Milne, Abelian Varieties version2.0(2008), I§7/Theorem7.2 and
Remark8.12 printed39; Howe–Leprévost–Poonen, arXiv math/9809210v1, §4.1/Lemma13/
Proposition15 with its twist assumptions; the committed Ciani/odd-quotient
derivations and actual original field/Picard/fibre source. Source metadata and
KB-unavailable receipt are622871. No novelty claim is made. [pcc:unverified]

The norm polynomial (ac+n*bd)^2−n(ad+bc)^2=(a^2−nb^2)(c^2−nd^2)
has exact Int Lean binding637454 and certificate IDC1hd724979553e97e07.
The original native issuer checks64 sealed and32 extra Mersenne-field
points, independently of an exact integer coefficient expansion. The
certificate pointer matches the actual checked Int source; the checker
does not run Lean. Dropping the imaginary term rejects101. Both original
proof gates pass one norm declaration/zero trusted, with propext and
Quot.sound. This is the supporting polynomial identity; field reduction
and nonsquare hypotheses remain explicit. [pcc:unverified]
