# The first direct F101 quartic cover and its global identification

This is a written argument for the fixed T0→E109 quotient. Runtime
acceptance,independent certificate replay and CI belong to the living
checkpoint. The existing global Richelot and norm/pullback constructions
are explicit dependencies,not consequences of finite testing. Actual
curves,Picard functoriality,polarized adjoints and line-bundle geometry
are not constructed in Lean here. Scientific standing unsigned.
[pcc:unverified]

## Exact map and normalization

Use k=F101,T:y²=F(x),E:Y²=X³+X+46,with

    F=[31,75,74,54,71,55,1]
    N=[14,0,88,97,14]
    Q=[63,0,1]
    M=[41,40,69,73].

All polynomial lists are low to high. Put

    f(x,y)=(N(x)/Q(x)²,y M(x)/Q(x)³).

The coefficientwise certificate is F M²=N³+N Q⁴+46Q⁶. Require
gcd(N,Q)=1,M≠0,smooth T/E and nonzero derivative of N/Q². These
are exact finite polynomial checks,not a fit residual or a statistical
inference. Native02/ad6883 checks all of them and the degree bounds.
The raw coefficient output and all118 finite rational point comparisons
are frozen with the source. [pcc:unverified]

A nonconstant rational map from a smooth projective curve to the proper
curve E extends uniquely at every point. Its function-field degree is4:
the reduced rational function N/Q² on the x-line has degree4,and both
x:T→P1 and X:E→P1 have degree2. Multiplicativity gives2deg(f)=8.
The nonzero derivative also checks separability;degree4 is prime to101.
At the two source infinities,y/x³→±1,so the displayed leading
coefficients give f(infinity±)=±q with q=(14,73). These finite limits
also follow by the local parameter1/x. [pcc:unverified]

Q has simple roots away from F;at each root both source branches have
y≠0. Coprimality and the identity imply N,M are nonzero there. Thus X
has pole order2 and Y order3 at each of the four geometric pole points.
Each maps to O with ramification index1. No pole is silently omitted;
the proper extension takes those four points to O. Native replay of
their coordinates is a separate executable certificate. [pcc:unverified]

## Why this ansatz applies to the old homomorphism

Write R=R0:J(C0)→J(T),N0:J(C0)→E for the accepted first elliptic norm,
and P0=N0† for its pullback. Existing global constructions give
Rhat R=[2],R Rhat=[2],N0P0=[2]. Define H=N0 Rhat and H†=R P0.
Then globally HH†=[4]. These are homomorphism identities on abelian
varieties;no cancellation on finite point groups is used.
[pcc:unverified]

Let h(P)=H([P-infinity-]). The Abel–Jacobi universal property makes h
a curve morphism with induced Jacobian pushforward H. The canonical
polarizations identify its pullback with H†. Norm followed by pullback
on the elliptic Jacobian is[deg h],so HH†=[4] gives deg h=4. The
integer embedding Z→End(E) is injective,including in positive
characteristic;[n] has degree n² for n≠0. [pcc:unverified]

Let delta=[infinity+-infinity-] and D=H(delta). The actual E(k) has
odd order109. Therefore q=[55]D is the unique rational half of D.
Native02 computes q=(14,73),without a discrete-log label. The divisor
of x-x(P) gives h(P)+h(iota P)=D,including the ramified interpretation.
Thus g=h-q satisfies g(iota P)=-g(P) and g(infinity±)=±q. Translation
does not change the induced Picard pushforward,so g_*=H.
[pcc:unverified]

Since g is odd,X∘g lies in k(x),and Y∘g=yS(x). Degree4 makes the
reduced x-function Nold/Dold have numerator/denominator degrees≤4.
The actual F is irreducible of degree6. Consequently no finite
Weierstrass x-coordinate can be a root of Dold. At every other finite
pole,x is an unramified local coordinate and X has even pole order.
Every root multiplicity in the monic Dold is even,so Dold=Qold²
over k,degQold≤2. Because g(infinity±)=±q is finite,the rational
x-function has no pole at infinity;its degree4 forces degQold=2.
[pcc:unverified]

At a finite Weierstrass point,g takes a finite2-torsion value,Y∘g
vanishes and y has a simple zero;S is regular there. Away from branches
and poles it is regular as well. At a pole,its denominator divides
Qold³ by the pole orders2 and3 of elliptic X/Y. Hence S=Mold/Qold³
with Mold polynomial. Regularity at both infinities and y~±x³ gives
degMold≤3. This derives the frozen ansatz for this fixed finite-q
case;it does not assert it for every genus2 cover or every normalization.
[pcc:unverified]

## A finite certificate with a proved global degree bound

For any two morphisms a,b:T→E,define their degree as
deg(a*L),L=O_E(O). Constant maps have degree0. Apply Milne AVv2
ChapterI Corollary5.3(the arbitrary-map theorem-of-cube pullback identity)
to a,b,-b. The constant map0 has degree0 and[-1]*L≅L,so taking degrees
gives the exact parallelogram law

    deg(a+b)+deg(a-b)=2deg(a)+2deg(b).

This uses the arbitrary-map corollary,not merely the translation form of
the theorem of the square. For our two degree4 maps f,g,it gives
deg(f-g)≤16. A nonconstant curve morphism's fibre has at most its total
degree many distinct geometric points,even when inseparable. Thus
agreement at17 distinct source points forces f-g to be constant. One
agreement then forces that constant to be O. Therefore f=g globally.
[pcc:unverified]

The frozen native02 list contains118 distinct actual source points and
their values under g=N0 Rhat([P-infinity-])-q,all agreeing with f. A
separate checker must replay their source/target membership,distinctness,
all coordinates and the coefficientwise identity from frozen inputs.
The old route remains a dependency for the provenance of these expected
values. The degree argument supplies the global implication;agreement
on a finite set by itself would not. It follows that f_*=H and f*=H†
under the accepted old global constructions. [pcc:unverified]

## Direct norm on arbitrary balanced support

An input class is represented by

    Dfin+(n-1)infinity+ +(1-m-n)infinity-,  m=deg u≤2.

Its image in E is the sum of the finite f-images plus(2n+m-2)q.
Degree0 plus0/1/2 therefore contributes-2q/O/+2q. Degree1 finite
support uses the actual map or O at a pole,then adds its infinity term.
The input must pass the existing model/canonical/support validation.
[pcc:unverified]

For monic quadratic u=x²+A x+B with Q invertible in k[x]/u,reduce
X=N/Q²=r0+r1x and Y=vM/Q³=w0+w1x in that finite algebra. If r1≠0,
the line slope is lambda=w1/r1 and the sum is

    Xsum=lambda²-2r0+A*r1
    Ysum=lambda*(r0-Xsum)-w0.

These follow from the usual elliptic secant and trace(x)=-A. Repeated
roots retain the Mumford derivative jet;the same polynomial line
congruence gives the tangent when appropriate. If r1=w1=0,double the
actual point(r0,w0) using the old elliptic engine. If r1=0,w1≠0,the
curve equation modulo u implies2w0=A*w1:the two images are opposite,
or a repeated branch image doubles to O. Their sum is O.
[pcc:unverified]

If Q is nonunit,compute gcd(u,Q²),including support multiplicities.
Degree2 means both finite contributions map to O;degree1 leaves one
linear finite contribution after exact division;degree0 is the unit
case. This covers repeated pole support without pretending the
denominator is invertible. Existing elliptic group operations finish
the sum and the integer infinity correction. Executable acceptance
requires every12317 T0 class,all negations/fixed-partner sums,actual
pole/coincident-X/repeated/infinity cases and foreign-model rejection
against the retained H route. Those receipts belong to the checkpoint.
[pcc:unverified]

## Sources and limits

Sources checked directly:Milne,Abelian Varieties v2.0(16March2008),
ChapterI Corollary5.3 and its pullback proof,
https://www.jmilne.org/math/CourseNotes/AV.pdf,
SHA256f5ca4e63e5092a4b102daad1470e4cbed5fe8f82115e3a28c8881e3f67f6aaef;
Galbraith,Mathematics of Public Key Cryptography,corrected Chapter8,
Lemma8.1.3,Definition8.1.6,Lemma8.1.9,Theorem8.2.12/Corollary8.2.13
and Theorem8.3.8(1,5,6),official book index
https://www.math.auckland.ac.nz/~sgal018/crypto-book/crypto-book.html.
The latter supplies extension,degree,fibre and norm/pullback facts.
Retained SEVEN_CHAIN_PROOF.md/SEVEN_JACOBIAN_PROOF.md supply the old
global quotient/polarization hypotheses. Existing private Sutherland
Lagrange code is reused with exact source custody,not claimed as new.
KB/ecdb are unavailable and the atlas vault is locked;no novelty or
absence claim is made. [pcc:unverified]

This is an evaluator of the already constructed H,not a new transfer.
Construction cost,full pipeline and matched solver cost comparisons
remain separately admitted tasks. No measured advantage or general
field-family statement follows from these fixed coefficients.
[pcc:unverified]
