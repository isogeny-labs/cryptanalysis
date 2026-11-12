# All four quartic covers and their direct balanced pullbacks

Scientific standing unsigned. This extends the fixed T0 arguments in
QUARTIC_COVER_PROOF.md/6afa9c and T0_SECOND_QUARTIC_PROOF.md/a38aa4
to T1 and derives the implemented pullback. Existing global Richelot,
norm,polarization and Picard constructions are explicit written
dependencies;the new Lean results cover finite algebra only.
[pcc:unverified]

## Exact T1 maps and global identification

T1 is y²=F1(x),F1=[95,26,19,27,94,91,1],over F101. Both maps
are f=(N/Q²,yM/Q³),with low-to-high coefficient lists:

| Target | N | Q | M | f(infinity+) |
|---|---|---|---|---|
| E109'=(26,58) | [8,60,36,0,84] | [47,0,1] | [98,45,84,37] | (84,37) |
| E113'=(69,50) | [3,0,76,42,46] | [70,0,1] | [4,76,75,41] | (46,41) |

Construction12/0d5e14 and independent flat-field16/850e92 check
F1 M²=N³+aNQ⁴+bQ⁶,gcd/smoothness/separability and rational
x-degree4. The source sextic is irreducible of degree6. Both infinity
limits are finite and opposite. Each map has four simple geometric
pole branches:exactly two are rational. They are(85,21),(85,80) for
E109' and(43,4),(43,97) for E113'. The other two are retained in the
declared F101⁶ certificate. None is discarded by a denominator test.
[pcc:unverified]

For j=109,113 put H_(1,j)=N_(1,j)R1hat. The old global identities
give H_(1,j)H_(1,j)†=[4],hence its Abel–Jacobi curve map has degree4.
Centre it by q=[55 or57]H_(1,j)([infinity+-infinity-]),using the actual
odd elliptic group order109 or113. The native q is the displayed finite
point. The old centred map is odd. The derivation in6afa9c therefore
applies:its reduced x-denominator is a square of degree≤2 and its
ordinate has the predicted finite-q bound. [pcc:unverified]

Both new and old centred maps have degree4. Milne's arbitrary-map cube
identity bounds their difference degree by16. The frozen116distinct
finite agreements already exceed that bound;the two origin-valued
witnesses additionally check every finite rational source point.
The independent checker verifies the entire118-point source domain,
all target values,infinities and geometric poles. Expected old-H value
provenance remains an explicit dependency. The same total-degree fibre
argument from6afa9c identifies the maps globally. Thus f_*=H_(1,j)
and f*=H_(1,j)†=R1P_(1,j),with the accepted principal polarizations.
[pcc:unverified]

## A fibre as a finite algebra,including repeated support

For any of the four covers take a finite rational target point P=(X,Y).
Its elliptic rational group has odd order109 or113,so Y≠0. Write

    U=N-XQ²,   V=YQ³/M mod U,

and normalize U to be monic. Coprimality of N,Q makes Q a unit in
A=F101[x]/U. The exact cover and target equations give in A

    F M²=Y²Q⁶.

This makes M a unit even if A has nilpotents. With supplied inverses
Yi,Qi its explicit inverse is F M Yi² Qi⁶. Indeed multiplying by M
gives F M² Yi² Qi⁶=1. No field assumption on A is used. Consequently
V²=F in A. The ideal(U,y-V) represents the whole finite fibre,with
its ramification multiplicities and Mumford jets. It contains no
opposite hyperelliptic pair because P≠-P. [pcc:unverified]

QuarticFibre.cleared_fibre_factorization/d4010b proves over any [pcc:unverified]
commutative ring the exact divisibility identity

    F M²-Y²Q⁶=(N-XQ²)(N²+NXQ²+X²Q⁴+aQ⁴),

under the supplied cover/target equations. The second bound theorem,
ordinate_denominator_inverse/4286c9,proves the explicit inverse above [pcc:unverified]
from the fibre equation and supplied units. Gate01/local verdicts3413a4
pass2theorems/zero trusted native,using standard Lean foundations.
This is faithful finite-algebra formalization;actual fields,proper
curves,divisor multiplicities and Picard duality remain written.
[pcc:unverified]

## Exact infinity counts before the existing reduction

Let K=infinity++infinity-. Since Q is monic quadratic,has no source
branch root and the infinity images are finite,

    div(Q)=f*(O)-2K.

Hence f*([P-O]) is represented by the P-fibre minus2K. Normally
degU=4,so the balanced unreduced representative has finite degree4
and plus count n=-1. It is not a reduced Class yet.
[pcc:unverified]

If P=+q,put k=4-degU. At infinity+ the elliptic function X-X(q)
has order k,because the denominator has degree4 and its numerator has
degree4-k. Y(q)≠0 makes X-X(q) a target uniformizer,so this is exactly
the fibre multiplicity. The divisor is Dfin+k infinity+-2K,which
means n=k-1. For P=-q the fibre is Dfin+k infinity--2K,which means
n=-1. The common x-polynomial degree drop must therefore be resolved
using the actual Y sign;it does not by itself specify the divisor.
[pcc:unverified]

Actual k values are[1,2] for the T0 components and[2,1] for T1.
The implementation checks both signs,origin P=O→zero,and the exact
finite support equation before calling the pre-existing balanced
reduction. Its arithmetic body is byte-identical after extraction
from Balanced::add;the checked raw-support entry is new. The original
add still composes validated classes and calls that same body.
No new field,polynomial or group engine is introduced.
[pcc:unverified]

Native13/5143f5 checks all109+113 target points on each source model,
exact old R_iP_(i,j),injective images,all49,300 ordered elliptic-group
additions across the four cases,norm4/off-diagonal0,all signed degree
drops and off-curve rejection. Visibility-only extraction of the old
point enumerator and original/new reduction source custody are pinned.
The implemented formula is scoped to these rational odd-order groups;
geometric nonzero2-torsion requires another fibre chart and is not
claimed as an implemented domain. [pcc:unverified]

Primary sources checked directly:the arbitrary-map cube and degree/
norm/fibre passages linked in6afa9c,and Galbraith corrected Chapter10
Lemma10.4.14,Theorems10.4.16/19 and Example10.4.18. They justify the
balanced infinity reduction and uniqueness. KB/ecdb unavailable;atlas
vault locked. No novelty,field-family or measured-cost claim.
[pcc:unverified]
