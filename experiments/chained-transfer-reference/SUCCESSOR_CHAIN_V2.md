# Two consecutive nondual Jacobian transfers over F101

This is the written geometric extension of SEVEN_CHAIN_PROOF.md and
SUCCESSOR_GLOBAL_PROOF.md. It concerns the exact models below. Scientific
standing is unsigned. Native acceptance belongs to the living successor
checkpoint; this proof does not turn an unfinished test into a pass.
The field, Picard, quotient, polarization and Torelli bridges are written,
not a full Lean construction of these varieties. [pcc:unverified]

## Exact next Richelot quotient and its prime-field descent

Write Ji=Jac(Ci). The accepted global maps Phi1:J0→J1 and Phi2:J1→J2
are separable (7,7)-isogenies with both polarized-adjoint norms[7]. Their
elliptic product pulls Pi and norms Ni satisfy Ni Pi=Pi Ni=[2], with
Phi1 P0=P1 alpha and Phi2 P1=P2 beta. The actual C2 equation is

    y²=x⁶+22x⁴+10x²+19.

The accepted R1:J1→T1 has determinant33 and raw ordinate scale47, where
T1=Jac(y²=x⁶+91x⁵+94x⁴+27x³+19x²+26x+95). Transport its actual
geometric two-kernel through Phi2. In the native C2 ±Frobenius branch
order the resulting matching is (0,4),(1,5),(2,3). Coefficients remain
in the OLD cubic basis T³+6T²+13T+56, rather than a silently changed
quotient-field basis. Its determinant is49. The actual raw target is
[49,99,36,35,23,80,76]; w=50Y gives the normalized target

    T2=Jac(y²=x⁶+17x⁵+92x⁴+39x³+43x²+93x+95).

The selected-pairing constructor checks all six distinct branch roots,
their exact C2 product, Frobenius-stable matching, nonzero determinant,
smooth source/target and the displayed square normalization. Richelot
theory with the same completed correspondence and adjoint sign as the
accepted R0/R1 construction gives R2:J2→T2 of degree4, with
R2Hat R2=R2 R2Hat=[2]. Native all-class tests support evaluation;
global existence and polarized duality use that geometric construction.
[pcc:unverified]

The independent accepted branch-PGL2 oracle is reused as a byte-identical
prefix of a versioned source. It factors the actual T2 sextic in F101⁶,
checks the exact product and examines all120 distinct transformations
from one ordered branch triple to every ordered target triple. Only the
identity preserves all six roots (consumer PCCe54e1e). Every geometric
branch automorphism is in that list, since three roots determine it.
The hyperelliptic double cover and strong Torelli therefore give
Aut(T2,lambda2)={+1,-1}. This is a written Torelli bridge.
[pcc:unverified]

Let sigma be F101 Frobenius. The stable kernel implies
sigma(R2)=a R2 for an automorphism of the displayed principally polarized
target. Pullback by an isogeny is injective on polarization homomorphisms,
so a preserves the polarization and is ±1. The actual rational109 source
controls provide D=Phi2 Phi1 P0(P), with R2(D) nonzero, rational and of
odd order109. Thus sigma(R2)(D)=R2(D); a=-1 would imply2R2(D)=0.
Consequently a=+1. The displayed R2, and its polarized adjoint, are
defined over F101. This removes the twist ambiguity; rational-output
tests alone are not used as a density argument. [pcc:unverified]

## Regular second chained map and both commuting squares

The actual Phi2 two-action transports Ker R1 exactly to Ker R2.
R1Hat maps T1[2] onto Ker R1: its image has order4 and is contained
there by R1 R1Hat=[2]. Hence

    B=R2 Phi2 R1Hat

kills all of T1[2]. Native tables explicitly check all16 geometric
classes, all256 additions/Frobenius for each Richelot direction and the
adjoint inclusion as well (consumer PCC594b3f). Characteristic101 is
different from2, so this is finite-etale scheme-kernel inclusion.
The quotient property of abelian varieties gives the unique REGULAR
homomorphism Psi2:T1→T2 with B=Psi2[2]. It descends to F101 by uniqueness.
Degrees multiply: deg B=4·49·4=784, deg[2]=16, deg Psi2=49; it is
separable since101 does not divide49. [pcc:unverified]

The adjoint composite satisfies BHat B=B BHat=[28]. Substituting
B=Psi2[2] and cancelling4 in the torsion-free Hom groups gives both
Psi2Hat Psi2=Psi2 Psi2Hat=[7]. This cancellation is not performed on
geometric point groups. Composing the factor identity with R1 and using
R1Hat R1=[2], then surjectivity of[2], gives

    Psi2 R1=R2 Phi2,       Psi2Hat R2=R1 Phi2Hat.

Together with the accepted Psi1 R0=R1 Phi1, this proves globally [pcc:unverified]

    Psi2 Psi1 R0=R2 Phi2 Phi1,
    (Psi2 Psi1)Hat(Psi2 Psi1)=[49].

The composite has degree2401. These are homomorphism identities, not an
inference from any finite list of tested scalar values. [pcc:unverified]

## Rational evaluation, recovery and actual kernel fields

All rational Jacobian groups have odd order12317=109·113. Therefore
Psi2(D)=R2 Phi2 R1Hat([6159]D). The production version instead uses

    Psi2(D)=R2 P2 beta (N1(R1Hat D)/4),
    Psi2Hat(Q)=R1 P1 betaHat (N2(R2Hat Q)/4).

The inverse4 scalars are82/85 modulo109/113. The existing elliptic
point-multiplication and actual quotient charts compute these divisions
without assigning a discrete logarithm to the input. C2 norms remain the
existing generic norms; the C0/C1 direct-norm whitelist is not enlarged.
Original pointwise Richelot evaluation and naive Jacobian halving remain
references. The closed-fibre chart uses its explicit boundary/fallback
rules, without inverting branch ordinates. [pcc:unverified]

For either original elliptic component let S(P)=R0 P0(P), interpreting
P in one factor and zero in the other. The global identities give

    N0 R0Hat Psi1Hat Psi2Hat Psi2 Psi1 S(P) = [196]P,
    N2 R2Hat Psi2 Psi1 S(P) = [4] beta alpha(P).

Inverse196 is104 modulo109 and64 modulo113. The degree and these
coprimalities preserve the original DLP in both subgroups. Native
source07 checks every109/113 scalar, nonzero full order, both naive/
quarter directions and both actual coordinate identities; its frozen
partial receipt PCC3dcebd does not assert the complete-graph run passed.
[pcc:unverified]

R1 is injective on7-primary torsion, so Ker Psi2=R1(Ker Phi2) has49
points, with the same Frobenius5/6 action. Likewise R0 restricts to a
Galois-equivariant bijection

    Ker(Phi2 Phi1) → Ker(Psi2 Psi1).

Indeed the commuting square includes the image in the latter kernel,
R0 has2-primary kernel, and both kernels have2401 points. The accepted
nondual elliptic-kernel argument gives abstract group Z49×Z49, with
Frobenius33/27 modulo49 of orders42/14. Hence the chained composite's
full geometric kernel also needs F101^42; only49 of its2401 points lie
over F101⁶. All maps themselves are defined over F101. A splitting-field
cost for listing every kernel point is not a descent obstruction for
evaluating the rational maps. [pcc:unverified]

## Distinct unpolarized F101 Jacobians and limits

Native intersection controls check the three nonzero2-points of each
embedded elliptic factor on each of J1/J2: none belongs to the
corresponding Richelot kernel. Because those kernels are2-primary,
R1 and R2 preserve the embeddings of the actual elliptic curves E1'
and E1'' into T1 and T2. Their rational trace types are-7; the other
elliptic factors have trace-11. There are no cross homomorphisms between
these F101 isogeny classes. Each product-isogenous surface thus has a
unique connected elliptic subvariety of each trace type. Any unpolarized
F101-isomorphism T1≅T2 would identify E1' and E1'', contradicting
j87≠47. The same argument distinguishes T0 from T2 usingj12≠47.
No algebraic-closure nonisomorphism is claimed. [pcc:unverified]

TwoHopTransport.lean proves two-square composition, composite adjoint
norm49, full source reverse196 and both modular recovery implications.
Its module/function hypotheses are explicit; it does not define the
actual varieties. Existing ChainTransport/RichelotDescent lemmas cover
each individual quotient/sign/quarter implication. Formalization remains
partial with the geometric dependencies above. No benchmark, advantage
over Pollard rho or existing index-calculus baseline, cryptographic-size
coverage, novelty verdict or signed scientific standing is inferred.
[pcc:unverified]

Primary sources remain HLP math/9809210v1 §3.2 Propositions3–4;
Kunzweiler DCC92(2024) §3.2 Propositions7–8; Milne Abelian Varieties
v2 Remark8.12 and Proposition10.20; Milne Jacobian Varieties(2021)
Theorem12.1. Their checked PDF hashes and exact scopes are retained in
the two parent proofs. Shared KB/atlas access remains unavailable;
no new literature absence or priority claim is made.
