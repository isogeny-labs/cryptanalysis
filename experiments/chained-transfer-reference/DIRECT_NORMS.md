# Direct elliptic norms of a balanced even-sextic class

This is the CT22 written proof for the direct-coordinate adapter. Runtime
coverage is the two actual C0/C1 models overF101, not a production/catalog
backend. Native certificates are producer-run and all scientific standing is
unsigned. The global Picard and elliptic-group bridges below are written;
seven cleared algebra lemmas are separately checked in Lean. [pcc:unverified]

## Curves, quotient maps and exact implementation domain

For the derivation, let K be a field of characteristic different from2 and3,
and let C:y²=x⁶+d*x⁴+c*x²+b be smooth with b≠0. The two elliptic quotients
are the smooth projective completions of

    E1_long: Y²=U³+dU²+cU+b,
    E2_long: W²=V³+cV²+b*d*V+b².

The covers are pi1(x,y)=(x²,y) and pi2(x,y)=(b/x²,b*y/x³).
Their equations follow directly by substitution. Smoothness follows from
the squarefree source sextic and b≠0; quotient cubics have distinct roots.
These rational formulas extend to morphisms of smooth proper curves.
The short coordinates are X=U+s1 and X=V+s2, with s1=d/3 and s2=c/3;
ordinates do not change. Existing genus2::cubic_to_short constructs these
short curves, and the adapter reuses it unchanged. [pcc:unverified]

The actual adapter accepts only (b,c,d)=(56,13,6) or(68,42,26) overF101.
Their short shifts are2/38 and76/14. Existing C1 component matching
still swaps the factors and scales coordinates by21. The class's model,
field, monic/canonical support, reduced ordinate and source-curve relation
are checked by the unchanged Balanced validator before evaluation.
No extension field, elliptic group or Cantor engine is introduced.
[pcc:unverified]

## Degree2 support with nonzero linear coefficient

Let u=x²+A*x+B, v=V0+V1*x represent a valid finite degree2 support.
Over an algebraic closure, its abscissae x1,x2 satisfy x1+x2=−A and
x1*x2=B. Suppose the elliptic images have coordinates

    Xi=lambda*xi²+s, Yi=V0+V1*xi,

where lambda≠0. If A≠0, the ordinary addition slope is
m=−V1/(lambda*A), and the symmetric formulas are

    Xsum=m²−lambda*(A²−2B)−2s,
    Ysum=m*(s−lambda*B−Xsum)−V0.

Indeed the difference quotient for Y is V1 and that for X is
lambda*(x1+x2). Also x1²+x2²=A²−2B. In the usual ordinate formula,
substitute xi²=−A*xi−B; the coefficient of xi vanishes because
m*lambda*A+V1=0. Everything left is symmetric and belongs toK, without
choosing an individual support root. [pcc:unverified]

This includes repeated support at a nonzero abscissa. For u=(x−r)²,
validity of v²−f modulo u supplies the ordinate jet, so V1 is dy/dx at
the source point. Then A=−2r and m=V1/(2*lambda*r) is exactly the
elliptic tangent slope by the chain rule. A repeated source branch point
with y=0 cannot satisfy that jet relation on a smooth curve. The case r=0
is treated separately below; no invalid denominator is inverted.
[pcc:unverified]

For the first norm use lambda=1 and s=s1. This gives the sum of the two
actual elliptic images, hence the finite pushforward. [pcc:unverified]

## Even support and vertical/doubled images

If A=0, reduction of the even source equation modulo x²+B has no linear
term. Reduction of v² has linear coefficient2*V0*V1, so validity forces
V0*V1=0 in characteristic different from2. If V1=0, both image points
coincide at (s−lambda*B,V0); return their actual elliptic double using
the existing group routine. If V0=0 and V1≠0, the two images have the
same X and opposite Y, so return the origin. When both vanish, doubling
the Weierstrass image also returns the origin. [pcc:unverified]

For A=B=0, source smoothness and b≠0 force V0≠0 and V1=0.
This is repeated support at x=0, and the first norm is the same elliptic
double. It is not discarded as an exceptional denominator failure.
[pcc:unverified]

## Second quotient by reciprocal support

For B≠0 put t_i=1/x_i. Their monic support has A'=A/B and B'=1/B.
The second image is (X,Y)=(b*t_i²+s2,b*(V0*t_i³+V1*t_i²)).
Reducing its ordinate modulo t²+A't+B' gives

    V1'=b*(V0*(A'²−B')−V1*A'),
    V0'=b*(V0*A'*B'−V1*B').

The exact remainder identity is

    b*(V0*t³+V1*t²)−(V0'+V1'*t)
      = b*(V0*t+V1−A'*V0)*(t²+A'*t+B').

Apply the same degree2 sum rule with lambda=b, s=s2 and the reciprocal
support/ordinate. This also transports repeated-support jets correctly:
inversion is regular and has nonzero derivative away from x=0. It is
algebraically equivalent to the existing sqrt(b)/x reciprocal chart on the
two actual models, with the SAME ordinate b*y/x³ and no twist/sign change.
[pcc:unverified]

If B=0 and A≠0, the roots are0 and−A. Under pi2 the x=0 point maps
to the elliptic origin, while the other is evaluated directly with ordinate
V0−A*V1. If A=B=0, both second images are the origin. For degree1
support x=r, evaluate pi1 directly and pi2 directly when r≠0; when r=0,
pi2 is the origin. Degree0 has no finite contribution. These are actual
projective images, not dropped terms. [pcc:unverified]

## Balanced infinities and the Picard norm

The source infinities are infinity±, according to y/x³→±1. The first
cover maps both to the elliptic origin. The second maps them to
±Q, Q=(s2,b) on the short second quotient. A balanced class represents

    D_fin+n*infinity+ +(2−m−n)*infinity− −(infinity+ +infinity−),

where m=deg u. Pushing it forward and using the elliptic group law gives
the finite first sum and

    finite second sum +(2n+m−2)Q.

This is the precise correction implemented, including degree0 plus counts
0/1/2, both degree1 infinity choices and all degree2 cases. The original
RichelotAlgebra.balanced_infinity_sum is the existing module identity behind
the coefficient. The actual identity class (m=0,n=1) maps to both origins.
[pcc:unverified]

Pushforward of divisors along a finite cover preserves principal divisors
and induces the usual Picard norm (Galbraith, corrected Chapter8,
Theorem8.3.8/Corollary8.3.10). The formulas above compute that pushforward
on every allowed support, with multiplicities and all infinity terms.
Therefore they equal the existing two norm homomorphisms globally on the
stated balanced representation. Generic distinct-point addition, repeated
jets and the explicit exceptional cases supply the equality; finite F101
tests alone are not used as a density or global-morphism argument.
[pcc:unverified]

## Native and formal scope

Native receipt02 compares BOTH outputs against the unchanged generic norms
on ALL12317 C0 and ALL12317 C1 rational classes. Both models also satisfy
every deterministic paired-addition check for each quotient, actual point
validity/orders, identity and wrong-model rejection. Each model has disjoint
degree/zero categories[3,4,232,2,216,232,11628],118 repeated supports and
238 nonzero infinity corrections. ConsumerPCC2c9f2c remains unsigned.
[pcc:unverified]

After integration, both Phi/Psi order109 source tests pass. The old generic
coordinate evaluators remain available and the naive chain evaluator uses
them explicitly. The changed complete Phi test compares generic and direct
evaluations on every source/target class; full changed-matrix acceptance is
a separate obligation until its receipt finishes. ConsumerPCC589b24 pins the
source stage and retained Clippy iteration diagnostic. [pcc:unverified]

DirectNorms.lean proves seven conditional algebra lemmas: symmetric squares,
slope inverse, ordinate support reduction, reciprocal support, reciprocal
ordinate remainder, even-support square remainder and zero-factor splitting
under explicit inverse2/domain hypotheses. Gate7 passes with no trusted native
uses;PCC8eaf58 binds exact declarations. Actual finite fields, valid Mumford
jets, elliptic group law, projective cover completion and Picard functoriality
remain written bridges. Project source census97 is distinct from a full
formalization of the norm theorem. [pcc:unverified]

This is arithmetic engineering for an already defined map. It proves no
measured speedup, index-calculus improvement, rho/BSGS advantage or cross-prime
transfer. The runtime supports only the two declared F101 models; the written
algebra does not silently expand catalog coverage. Successful S3 admission,
live budget/capacity and a frozen matched complete-cost protocol remain
required before a benchmark or solver run. [pcc:unverified]
