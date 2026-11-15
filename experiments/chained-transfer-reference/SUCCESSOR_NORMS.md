# CT25: exact direct norm specialization for C2 over F101

Scientific standing unsigned. This is a versioned extension of the frozen
DIRECT_NORMS_PROOF.md,whose runtime scope was C0/C1. It establishes the
exact C2 specialization and coordinate matching;it does not broaden that
old record or accept other fields/models. Native complete-graph/whole-guard
acceptance belongs to the living CT25 checkpoint. [pcc:unverified]

## Curves, covers and unchanged generic reference

Let C2:y²=x⁶+22x⁴+10x²+19 over F101. It is the accepted smooth monic
split-infinity model,with square constant19=25². Its two projective elliptic
covers are the completions of

    piA(x,y)=(x²,y),
    piB(x,y)=(19/x²,19*y/x³).

Their long cubics are respectively[19,10,22,1] and[58,14,10,1]. The
actual unchanged generic SplitQuotients constructor uses the reciprocal
curve isomorphism(T,Y)=(25/x,19*y/x³),then the ordinary quadratic cover.
Since25²=19,this is EXACTLY piB,with the same ordinate and sign. Both
reciprocal models are checked monic/smooth;no twist,field change or choice
of an individual support root is introduced. [pcc:unverified]

Short shifts are41 and37. The short curves are EA:(17,91),order113,
and EB:(48,48),order109. Scaling(X,Y) by(18²,18³) maps them respectively
to actual beta targets(23,7) and(59,27). Thus the accepted C2 charts are
(destination,shift,scale)=(1,41,18),(0,37,18). Seven SuccessorNorms Lean
lemmas check the cleared curve identities,characteristic101 implications,
the reciprocal inverse hypothesis and exact shift/scale coefficients,
PCCc2aaaa. The finite fields and elliptic group/Picard objects are not
constructed in Lean. [pcc:unverified]

## Finite divisor norm,including repeated support

All input classes first pass the unchanged Balanced model/canonical-support/
reduced-ordinate/curve validator. For u=x²+A*x+B,v=V0+V1*x and A≠0,
the first finite norm uses the symmetric elliptic sum

    m=-V1/A,
    X=m²-(A²-2B)-82,
    Y=m*(41-B-X)-V0.

These are the generic direct-norm identities from the parent proof at
lambda1/shift41. The support algebra relation x²=-A*x-B and slope
constraint m*A+V1=0 eliminate x from the ordinate. For repeated support,
validity modulo u supplies the correct ordinate jet and hence tangent.
No assumption that u has two distinct rational roots is made.
[pcc:unverified]

For A=0,validity and parity of the sextic imply2*V0*V1=0. Characteristic101
is different from2 and is a field,so V0*V1=0. If V1=0,return the actual
elliptic double of(41-B,V0). If V0=0 and V1≠0,the two ordinates are
opposite and the sum is the origin. When both vanish,the elliptic double
of the branch point is also the origin. At A=B=0,nonzero constant19 forces
V0≠0,V1=0;the repeated x0 case is retained. [pcc:unverified]

For the second norm and B≠0,set t=1/x,A'=A/B,B'=1/B and

    W1=19*(V0*(A'²-B')-V1*A'),
    W0=19*(V0*A'*B'-V1*B').

These are the exact remainder of19*(V0*t³+V1*t²) modulo
t²+A't+B'. Apply the same finite sum rule at lambda19,shift37 with
support(A',B') and ordinate(W0,W1). Inversion is an isomorphism on this
finite support algebra,so repeated jets and multiplicities are preserved.
The parent DirectNorms Lean identities formalize the cleared reciprocal
support and ordinate remainder with explicit inverses. [pcc:unverified]

If B=0,A≠0,the x0 point maps under piB to the elliptic origin and the
other point x=-A is evaluated with ordinate V0-A*V1. If A=B=0,both
second images are the origin. Degree1 support is evaluated directly,
using the origin at x0 for piB. Degree0 has no finite contribution.
These are the projective images,not omitted exceptional terms.
[pcc:unverified]

## Both balanced infinities and global Picard equality

Write infinity± by y/x³→±1. The first cover sends both to the origin.
The second sends them to ±Q,with Q=(37,19) on EB. A degree m balanced
class with plus count n represents

    D_fin+(n-1)*infinity+ +(1-m-n)*infinity-.

Its second norm is therefore the finite sum plus(2n+m-2)Q;its first
norm is the finite sum. This includes all degree0/1/2 choices and the
identity(m0,n1). The implemented correction and sign are exactly the
parent formula at b19/s237. [pcc:unverified]

Pushforward along each finite projective cover preserves principal divisors
and induces the Picard norm. The finite-algebra/tangent rules and explicit
infinity images above compute that pushforward on every allowed balanced
support. Hence these direct formulas equal the two GENERIC norms as
homomorphisms on the stated representation. Equality is not inferred from
finite rational test outputs as a density argument. The cited generic
Picard result is the same Galbraith corrected Chapter8 Theorem8.3.8/
Corollary8.3.10 used in the frozen parent proof. [pcc:unverified]

## Runtime specialization and retained controls

The old public C0/C1 constructor keeps its old whitelist and still rejects
C2. A separate explicit C2 factory supplies the same arithmetic builder
with[19,10,22];it is not acceptance of a general model catalog. No field,
polynomial,elliptic or Cantor engine body is replaced. C2 direct norms use
base-field arithmetic;the subsequent Richelot evaluation retains its
existing extension-field arithmetic. [pcc:unverified]

The original C2 generic coordinate evaluator remains. Generic Phi2 and
quarter-Psi2 variants select true generic divisor norms;naive Psi2 keeps
generic Phi2 norms. Complete graph comparisons exercise every input,
with the unchanged closed Richelot stages whose complete pointwise
equality was retained at CT24. All source/recovery/geometric controls
remain required. Exact acceptance and failed attempts are recorded outside
this frozen mathematical proof. [pcc:unverified]

C2 factory01 checks all12317 rational classes,both norms,all paired
additions/orders and every degree/zero category,including118 repeated
supports and238 infinity corrections,PCC0355ab/root562797. This is
correctness evidence,not a timing measurement or an end-to-end algorithm
advantage. Formalization remains partial:actual fields,balanced Picard
objects,proper completion and elliptic functoriality remain written.
[pcc:unverified]
