# Proposed nondual chain through a different gluing on Res(E)

Prospective proposal, not an implemented or validated new transfer. Preserve
the fixed q223 source and every candidate. The fixed-degree obstruction
c2270b excludes another rational polarized(2,2,2) Jacobian quotient directly
from J; it does not exclude J→A→J' with A=Res(K/F223)E and a different
second gluing kernel. [pcc:unverified]

## First discriminating construction

Audit all Frobenius-stable Lagrangians of A[2], using the actual three source
2-torsion points and their conjugates. With a conjugate basis on each
elliptic factor, Frobenius cyclically permutes three two-dimensional blocks.
The expected stable-kernel count is9:3 product kernels and6 gluing kernels.
This count and classification require their own native check; they are not
the count1 for J[2]. [pcc:unverified]

For each of the3 nonzero2-torsion roots r of the original short source
y²=x³+a_s x+b_s, translate x by r to obtain

    E_1: y²=x(x²+A_1*x+B_1),
    A_1=3r, B_1=3r²+a_s, Delta_1=A_1²−4B_1.

Let E_2,E_3 and their coefficients be the Frobenius conjugates. Each
Delta_i is a nonzero square in K because full E[2] is K-rational. Solve

    h_2*h_3=Delta_1, h_1*h_3=Delta_2, h_1*h_2=Delta_3

using h_1²=Delta_2*Delta_3/Delta_1,
h_2=Delta_3/h_1,h_3=Delta_2/h_1. Keep BOTH simultaneous sign choices,
giving6 candidates over the3 roots. Frobenius compatibility must be checked
explicitly; applying its cube shows the possible common sign discrepancy
must be+1. [pcc:unverified]

Form the symmetric matrix

    H = [[h_1,-A_3,-A_2],[-A_3,h_2,-A_1],[-A_2,-A_1,h_3]],
    Q = adj(H).

The proposed Ciani equation is (X²,Y²,Z²) Q (X²,Y²,Z²)^t=0.
Transport by the original Moore basis and require all15 normalized
coefficients to lie in F223. Keep det(H)=0, nonsquare determinant, repeated
model and other failures separately; do not select replacement inputs.
[pcc:unverified]

## Algebra requiring independent checks before any model claim

For a Ciani matrix Q with diagonal a,b,c and off-diagonal d/2,e/2,f/2,
the X-sign quotient has even quartic

    v²=(d²−4ab)t^4+(2df−4ae)t²+(f²−4ac).

The proposed Jacobian model is y²=x(x²+A_X*x+B_X), where

    A_X=8ae−4df=−16*adj(Q)_{23},
    B_X=−64*a*det(Q),

and cyclically. For Q=adj(H), the adjugate identities predict

    a=−4B_1, b=−4B_2, c=−4B_3,
    A_X=16*det(H)*A_1,
    B_X=(16*det(H))²*B_1.

These identities, the even-quartic Jacobian identification and all field/
twist factors require original native arithmetic and feasible faithful
Lean checks. Let D=16det(H). If D is a square, scaling x by D and y by
sqrt(D)^3 should identify the quotient with the original translated E_i.
A nonsquare D is a quadratic-twist obstruction, not an eligible target for
the original odd subgroup. The square test must be performed, not assumed.
[pcc:unverified]

For nonzero det(H), the Ciani smoothness factors are predicted nonzero:
the diagonal entries are−4B_i, det(Q)=det(H)², and the pair discriminants
are−4det(H) times the corresponding h_i. Verify these symbolically and with
the original plane-quartic smoothness certificate. Det(H)=0 can require a
different genus3 model; it does not prove that the gluing quotient fails
to exist. [pcc:unverified]

## Actual maps, not just matching quotient invariants

An eligible curve still needs actual homomorphisms. For each quotient, use
the actual prime-field base point to identify its genus1 quartic with its
Jacobian, preserving the actual affine origin. A square root used by an
even-quartic coordinate formula may lie only in F223^6; translation by the
actual origin must make the resulting rational point descend to K. Check
every such descent before using the original K3 fibre-ideal trace reducer.
The quotient fibre has the line Y=tZ and its actual quadratic X-fibre;
infinity and multiplicity cases remain required. [pcc:unverified]

Construct Phi':A→J' and N':J'→A, prove both compositions[2], and check
the odd generator and all five public points independently. If J' is
distinct, F=Phi' N and G=Phi N' have both compositions[4], so preserve the
original prime-ell DLP. Returning through the original identical gluing
only gives[2] and is retained as the trivial control. [pcc:unverified]

Distinct coefficient arrays are insufficient to prove a nonisomorphic
target. One proposed discriminating invariant is the degree6 ternary
quartic catalecticant determinant together with the Ciani discriminant:

    Disc ~ abc*(d²−4ab)²*(e²−4bc)²*(f²−4ac)²
           *(4abc+def−a*e²−b*f²−c*d²)^4.

The ratio Disc²/Catalecticant^9 should be a projective invariant when the
denominator is nonzero. Its normalization, transformation weights and
discriminant formula require independent proof before use. Retain zero/
equal invariants as inconclusive, not an isomorphism certificate.
[pcc:unverified]

Next read the primary split-Jacobian gluing literature, verify the formulas
and all6 known-case candidates, then implement surviving maps. No novelty,
kernel count, new curve, nondual chain or computational advantage is claimed
by this proposal. If every candidate is obstructed or isomorphic, retain
that outcome and proceed to another justified degree or field route.
[pcc:unverified]
