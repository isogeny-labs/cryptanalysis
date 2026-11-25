# Actual inert sextic: representation and operation proof map

Actual fixed D/F7 is Y^2=H(W)=6W^6+2W^4+1, with the two covers from
crypto5114. H is squarefree. Infinity has two conjugate branches eta^2=6;
their rational sum Dinf is a canonical divisor of degree2. Base field,
curve, cover order and infinity model are never changed. Native
qualification below is pending; all mathematical standing is unsigned.
[pcc:unverified]

## Unique actual degree-two packets

For a nonzero rational degree-zero class x, Riemann--Roch applied to
x+Dinf gives an effective rational degree2 representative A. A rational
point (0,1) supplies the usual rigidified Picard identification, so this
is a line bundle over F7. If A includes one infinity branch, rationality
forces the other and A=Dinf, contradicting x!=0. If A contains a complete
hyperelliptic fibre, it is canonical and x=0. Thus A is affine and
semi-reduced, including allowable repeated non-Weierstrass points.
[pcc:unverified]

For noncanonical degree2 A in genus2, RR gives h0(A)=1. Hence two
equivalent such effective divisors are equal. The precise Mumford ideal
(u(W),Y-v(W)) recovers A, including multiplicities: u is monic degree2,
deg v<2 and u divides H-v^2. A repeated Weierstrass root would force H'=0
there and is excluded by squarefreeness. Distinct valid pairs give distinct
nonzero classes; the identity is represented only by (1,0). No degree1
packet relative to a single rational infinity is admissible. Exhausting
49 monic quadratics and49 linear v-polynomials is therefore a complete
2401-case correctness population, not a search for a new curve. The
known prime-to-eleven degree4 E-square isogeny predicts #JD(F7)=121 and
JD(F7)~C11^2; the native exact count must independently agree.
[pcc:unverified]

## Composition and one-step balanced reduction

Use exact extended polynomial gcds, with monic d and explicit Bezout
coefficients s1,s2,s3 for d=gcd(u1,u2,v1+v2). Compute

    u=u1*u2/d^2,
    v=(s1*u1*v2+s2*u2*v1+s3*(v1*v2+H))/d mod u.

Every division is exact and every Bezout/curve congruence is checked.
The standard affine composition removes the principal divisor of d;
its two infinity counterweights are both deg d. Degrees are0,2,4.
For degree4, set u'=monic((H-v^2)/u),v'=-v mod u'. The coefficient
of W^6 is6-v3^2, which is nonzero for every v3 in F7. Consequently u'
has degree2; no cancellation at either conjugate infinity occurs. The
function Y-v has pole order3 at each infinity, so its full divisor
relation is Acomp+Aextra-3Dinf. Negating the complementary divisor
therefore gives the genuine class sum relative to Dinf. For composed
degree0 or2 the equal counterweights already give the canonical result.
The identity branch is exact. Inversion is (u,-v). This is the even-genus
inert specialization of the read balanced arithmetic, not an unchecked
application of an odd-degree reducer. [pcc:unverified]

## Independent actual pushforwards

Evaluate the roots of each actual quadratic u, with repeated roots counted
twice. Split roots are in F7; irreducible quadratics use their own quotient
F7[t]/u(t), with second root -u1-t, exact nonzero norm inverses and actual
elliptic addition. Evaluate Y=v(root), both rational functions p1,p2 and
add the resulting elliptic points. At W=0, p2 is O by its proven proper
extension. The base p1_*Dinf is2O, and p2_*Dinf=(0,eta)+(0,-eta)=O, so
there is no omitted base correction. Every resulting sum must be in F7.
These sums are computed from divisor roots, never supplied product labels.
[pcc:unverified]

The complete121 packets must map bijectively to all121 ordered E(F7)^2
point pairs. Every one of14641 Cantor additions must agree with actual
elliptic addition under those independently evaluated pushforwards. This
checks the concrete group operation and transfers group axioms from the
genuine elliptic product; it does not define the Cantor law by table labels.
The written divisor identities separately connect it to the actual JD.
[pcc:unverified]

## The transferred input and unknown-log interface

For finite P=(x,y), A=p1^*P has u=W^2-(5x+3),v=y. For x!=0,
B=p2^*P has u=W^2-1/x,v=(y/x)W. Both origins map to the identity.
All nonzero F7 E points have x!=0; the curve has no rational point above
x=0. Check the covers' push--pull/cross-zero identities on all11 points.
Build Gamma(P)=6*(A(P)+B(-2P)), using only the input point; require
p1_*Gamma(P)=P,p2_*Gamma(P)=-2P for all inputs. The finite inverse2
implements the already-proved integral global map; it does not prove it.
[pcc:unverified]

Use the named existing Shanks BSGS algorithm with inputs solely a canonical
Mumford base, target and order11. Its function receives no oracle scalar,
source projection or class-pair label. The driver supplies all11 known
oracle cases for correctness and checks returned k by independent original
elliptic replay [k]T=Q. This is toy unknown-log-interface correctness,
without authenticated blindness, novelty, timing or scaling inference.
The projection-only solver negative remains: p1_* recovers the input
elliptic point and does not determine its unknown log. [pcc:unverified]

## Formal map and next obligations

The core conclusions here are written actual-divisor proofs plus planned
complete native arithmetic. Generic genuine-homomorphism crypto-lean38
remains at7ad357f8 with both frozen import failures before theorem checking,
zero accepted theorems/audit not reached; no unchanged repeat or dummy
group. Full faithful Lean RR/divisor/Jacobian and algorithm correctness
remain open. Preserve source/claims/default resources. After native
qualification, inspect the exact packet/table/control outcomes, preserve
all first failures, complete report/CI and advance the next unblocked
actual-map or prime-field-descent obligation. [pcc:unverified]
