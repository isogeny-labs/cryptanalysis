# Transported degree52 kernels and exact source-pair elimination

Active version02;version01 remains immutable with its citation error.
2026-11-13. Prospective579e08 was normally published at c37ad390 before
the additive refinement crate. Native147b66 is a finite correctness
observation; the geometric argument below uses the existing global
correspondences from1fd6e7/b9a91f/2e21d5. Standing is unsigned and full
geometric formalization remains open. [pcc:unverified]

## Fixed maps and actual transport

Write A=Res(E), A'=Res(Eprime), with u=Res(gamma),v=Res(delta).
The original and new dual maps Phi0,N0 and Phi',N' have both[2]
compositions and degree8. The odd maps have vu=uv=[13] and degree13^3.
Thus F=Phi' u N0 and G=Phi0 v N' have both[52] compositions, degree52^3
and polarization multiplier52. These are the maps of source45ee45d2;
no rational cofactor observation substitutes for a geometric degree.
Let G0=ker(Phi0) and G'=ker(Phi'). [pcc:unverified]

Native147b66 evaluates the actual degree13 Kohel map on every sorted
source2-torsion point and obtains permutation[0,3,2,1]. It reconstructs
all three coefficient-Frobenius-conjugate Kohel maps, compares their
complete x numerator/denominator and codomain coefficients, and checks
all four points in each factor. All64 product-vector images,4096
linearity/pairing comparisons and Frobenius commutations pass. The
literal old G0 mask9232380353346274305 transports to
2341872925073736705. This basis change is necessary even though both
products have the same abstract2-torsion vector space. [pcc:unverified]

All135 original Smith Lagrangians equal the fresh model census. Every
intersection with u(G0) is retained with actual target coordinates;
binary Gaussian rank independently matches its log2 cardinality. The
dimension0/1/2/3 histogram is64/56/14/1, and all9 rational kernels are
included. The native test does not construct J0[4] or J'[13] divisor
bases. [pcc:unverified]

## Full geometric kernel

Work over an algebraic closure of F223. Since characteristic223 is
coprime to52, K=ker(F) is etale, has52^3 geometric points, and is killed
by52. Its primary factors are K2 of order2^6 and exponent at most4,
and K13 of order13^3 and exponent13. In particular K13 is C13^3 as an
abstract finite group. This is not a statement about its Galois module
or rational points. The explicit projectors are[13] onto K2 and[40]
onto K13:13+40=1+52,4*13=52,13*40=10*52. Their images sum to every
point and their intersection is zero. [pcc:unverified]

Restrict N0 to J0[2]. Its kernel has8 points. Its image lies in G0 by
Phi0 N0=[2]; cardinality64/8=8 shows that the image equals G0.
On2-torsion u is an isomorphism, since its degree is odd. Hence

    ker(F)[2] = N0|J0[2] inverse-image of
                (G0 intersect u^-1(G')),
    #ker(F)[2] = 8 * #(u(G0) intersect G') = 2^(3+d),
    d = dim_F2(u(G0) intersect G').

Every group killed by4 has type C4^a x C2^b. Its order and2-torsion
give2a+b=6 and a+b=3+d, so a=3-d,b=2d. Therefore

    ker(F) = C4^(3-d) x C2^(2d) x C13^3

as an abstract geometric group. It is free C52^3 exactly when d=0.
The polarization supplies maximal isotropy for the52-Weil pairing,
but degree and isotropy alone do not supply freeness. [pcc:unverified]

| Actual eligible target | d | Geometric kernel | Wrong untransported d |
| --- | --- | --- | --- |
| HLP(1,0) | 3 | C2^6 x C13^3 | 2 |
| HLP(1,1) | 2 | C4 x C2^4 x C13^3 | 3 |
| HLP(2,1) | 1 | C4^2 x C2^2 x C13^3 | 0 |

Thus none of these three implemented targets has a free C52^3 kernel.
The wrong untransported-G0 calculation falsely labels HLP(2,1) free;
this explicit negative control is retained. All three nonsquare HLP
cases have d=0, as does product-Q3. They do not become implemented
Jacobian maps over F223 under the specified source just because their
abstract quotient kernels are free. The result excludes this particular
three-target panel, not other degrees, products, twists or chains.
[pcc:unverified]

## Matched kernel gives a global odd-degree factor

For HLP(1,0), the actual equality G'=u(G0) implies that Phi' u kills
G0. The universal quotient property for the isogeny Phi0:A→A/G0=J0
therefore gives a unique F223-defined homomorphism

    beta:J0→J',       beta Phi0 = Phi' u.

This is a global factorization of abelian varieties, not merely a
pointwise division by2. Galois descent follows from uniqueness of the
factorization of F223-defined maps. Its degree is
deg(beta)=deg(Phi' u)/deg(Phi0)=13^3=2197. Pullback of polarizations gives

    Phi0* beta* lambdaJ' = u* (2 lambdaA') = 26 lambdaA
                         = Phi0* (13 lambdaJ0).

Pullback by an isogeny is injective on homomorphisms/polarization classes
(the homomorphism groups are torsion-free and an isogeny has an inverse
up to a nonzero integer). Thus beta*lambdaJ'=13lambdaJ0. [pcc:unverified]

Since v u=[13] acts as the identity on2-torsion, v(G')=G0. The same
quotient argument supplies betaDual:J'→J0 with
betaDual Phi'=Phi0 v. Composing these identities with the surjective
Phi0 and Phi' yields betaDual beta=[13] and beta betaDual=[13].
Furthermore

    F=beta Phi0 N0=beta[2]=[2]beta,
    G=betaDual Phi' N'=betaDual[2]=[2]betaDual.

Thus beta is a DLP-preserving odd-degree transfer on ell2773073, with
inverse[639940]betaDual on its ell subgroup. The existing complete
F/G coordinate implementations do not yet implement complete beta or
betaDual coordinates on every rational Jacobian class. Halving F on
the odd subgroup alone would not fill that gap. [pcc:unverified]

The quotient factorization is exactly the universal-property argument
in Milne, Abelian Varieties, CourseNotes version2.0(2008),Remark8.12,
printedp38. The degree/etaleness,dual exact sequence,and polarization
facts are in Milne,Abelian Varieties,xnotes AVs.pdf,Section8,Theorem11.1,
Proposition16.8/Remark16.9. These two editions use different numbering.
The primary PDFs and exact sections were read for this version;URL and
SHA metadata are in evidence/odd-product-refinement-primary-review-01.
Version01's erroneous Mumford title/citation is preserved and corrected
here;it was not a premise of the quotient proof. No mathematical
statement,proof,code,test,Lean signature or verifier changes.
[pcc:unverified]

## Identical-output source implementation

For every point P of A, globally N0 Phi0(P)=[2]P. Consequently

    H(P)=F(Phi0(P))=Phi' u N0 Phi0(P)=Phi' u([2]P).

FastSourceChain implements the last expression using the original
elliptic doubling, degree13 map and new complete pullback. Its state
contains no old Norm/Phi object. The class outputs and packet tags are
exactly those of the frozen Chain API; source/target identity, canonical
coordinates, odd subgroup and roundtrip checks remain. Recovery is
unchanged:[159985]delta NormPrime H(P)=P on the original ell subgroup.
[pcc:unverified]

Native147b66 compares complete class outputs, encoded packets and source
recovery on32 fixed nonzero odd scalars plus zero and allfive unchanged
literal public targets for EACH of the three targets. Noncanonical,
off-curve, all three nonzero source2-torsion points, all three nonzero
rational target-cofactor classes, foreign field/model packets and an
actual mismatched-target constructor are rejected. The direct undoubled
Phi' gamma image differs from H and doubles to it, preventing silent
output renormalization. All2514 input guards are unchanged. [pcc:unverified]

This removes one old pullback and one old norm and introduces one
elliptic doubling in the forward algorithm. It is a structural
implementation change; there is no measured operation cost, timing
ratio, pipeline improvement or advantage over IC/rho. The original
checkpoint/livebudget/capacity admission and full cold+online counters
remain required. Next: exact partial Lean bindings, source-linked report,
strict independent replay/CI, genuine whole-data publication and actual
new-target solver/cost coverage. [pcc:unverified]
