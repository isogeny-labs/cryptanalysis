# The existing forward Jacobian seven-transfer using F101 arithmetic

Scientific standing unsigned. This describes an evaluator of the existing
fixed Psi:J(T0)→J(T1),not a new global transfer. Global old-map geometry
is retained from SEVEN_CHAIN_PROOF.md/eb3240 and its dependencies.
QUARTIC_COVER_PROOF.md/6afa9c,T0_SECOND_QUARTIC_PROOF.md/a38aa4 and
QUARTIC_PULLBACK_PROOF.md identify the replacement norm/pullback stages.
No timing comparison is inferred from their correctness receipts.
[pcc:unverified]

Let H0=(N_(0,109),N_(0,113))R0hat and
K1=R1(P_(1,109)+P_(1,113)). The accepted global factorization gives

    [4]Psi=K1 alpha H0.

The new explicit quartics identify each H0 component globally. Their
T1 counterparts identify the components of K1 as the ordinary Picard
pullbacks of the displayed degree4 curve maps. Their coordinates use
the actual selected elliptic factors:E109(1,46)→E109'(26,58) and
E113(44,21)→E113'(69,50). No swap,twist or extra chart scale is implicit.
The original quotient charts are already absorbed in the cover data.
[pcc:unverified]

On the rational groups of orders109 and113,the inverse of4 is82 and85,
respectively. Therefore the following point algorithm computes Psi:

1. Evaluate both direct T0 norms H0_j(D).
2. Multiply their actual elliptic points by82/85.
3. Apply the corresponding actual degree7 alpha_j.
4. Pull back through the direct T1 quartic f_(1,j),then add the two
   balanced classes with the existing arithmetic.

Every operation is over F101. Division by4 uses only public group orders,
not discrete-log labels. It is a rational-point algorithm,not a proposed
global inverse of the inseparable/separable morphism[4]. Since both
elliptic images have the stated odd orders,the integer scalars multiply
the sum by an inverse of4. Multiplication by4 is injective on
J(T1)(F101),whose order is12317. The displayed old global identity
therefore proves equality with the accepted Psi on the complete rational
domain. [pcc:unverified]

The constructor needs only the accepted fixed sextic/cover coefficients
and two selected stable elliptic kernel cubics[72,100,35,1] and
[59,46,8,1]. Existing Kohel code builds the two normalized alpha maps
over F101. The native test verifies numerator,denominator,kernel,domain
and codomain coefficient equality with the old selected maps. Parameter
discovery is inherited input provenance;no claim of free discovery or
cold setup advantage is made. [pcc:unverified]

Neither the constructor nor forward evaluator calls a Richelot or an
extension-field evaluator. The test's rational-class enumeration and old
reference are separate. The old balanced reduction arithmetic is reused
with exact source-body custody. The direct pullback support equation is
valid in finite algebras with nilpotents,with the actual infinity counts
and origin/invalid-input handling derived in QUARTIC_PULLBACK_PROOF.md.
[pcc:unverified]

Native15/72e1d8 and strictClippy pass every12317 exact old forward output,
bijection,fixed-partner addition,negation,identity and wrong-model control.
The earlier joint H0 version19b3bd remains a separate accepted intermediate
with its old R1 remainder. Unused-import failure14/7451f1 is preserved;
no arithmetic or test was weakened to repair it. [pcc:unverified]

The old global adjoint norm is PsiHat Psi=[7]. Thus on a prime-order
subgroup r=109 or113 the existing transfer remains injective,additive
and DLP-preserving. If Q=[k]P,the new evaluator returns Psi(Q)=[k]Psi(P)
and produces the same concrete destination points as the old algorithm.
Recovery by the old adjoint and inverse7 remains valid. A direct
prime-field adjoint is a successor implementation task. No existing
source,generic,naive or geometric control is removed.
[pcc:unverified]

Independent flat-field certificates replay the four curve equations,
complete rational witness domains,infinity limits and all geometric pole
branches. The complete T0/T1 class groups separately replay under the old
second Cantor engine. These are not independent evaluations of the whole
isogeny or independent geometric-kernel membership;those remain open.
The136written Lean helpers/25modules include two new finite-algebra
lemmas,not a construction of the Picard quotient or degree theorem.
[pcc:unverified]

Actual consumer integration must retain the old route and pass its own
complete changed guards on a fresh child of the first quartic PR.
Matched cold evaluation,source/destination solver,recovery and verification
costs remain admitted follow-up work;S3/profile/livebudget access is absent.
No computational advantage or general scaling conclusion is asserted.
[pcc:unverified]
