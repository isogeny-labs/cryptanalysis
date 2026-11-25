# Written dependencies for the separate unit verifier

All statements below have unsigned standing. They connect fixed native
arithmetic to the certificate's mathematical objects; native acceptance
does not establish the unformalized geometric dependencies by itself.
[pcc:unverified]

In F7[z], let m=z6+2z4+5z3+3z2+6z+3,A=z3+4z+6,D=3z2+5,
V=2z4+3z2+3z+1. Coefficient multiplication gives A2-3D2=m and
DV=1+6m. In R=F7[z]/m, b=AV satisfies b2=3 and D*b=A.
Putting a=z-b, direct expansion gives

 a3+2a+6 = z3+4z+6-(3z2+5)b = A-Db = 0.

The cubic has F7 evaluations6,2,4,4,1,1,3, hence is irreducible.
In its degree3 field,3^171=-1, so adjoining b makes a degree6 field K.
The map K->R defined by these two roots is unital; R is nonzero and
six-dimensional because m is monic degree6. A unital map from a field
is injective, and equal finite dimensions make it an isomorphism. This
also proves m irreducible. The verifier separately checks all relations
and full-rank basis conversion before invoking Fermat inverses.
The Lean leaves check the two coefficient identities only; their field
and quotient-instance lift is still missing. [pcc:unverified]

The original division factor is monic degree6. Six distinct valid marked
roots, with the canonical encoding isomorphism above, exhaust its roots
by the polynomial degree bound. Inspecting every bit and its zero padding
therefore certifies the117649 original accept/reject decisions while
evaluating the polynomial at just the six marked elements. No original
field-search driver is run. [pcc:unverified]

General Miller doubling/addition accumulates line/vertical divisors.
For n4 it takes two doubling rounds; the implementation does not reuse
the producer's closed f4 expression. With T order11,3T differs from T
and2T. Every support in the moved Weil divisor lies in an E[4] coset
translated by nonzero11-torsion, so it is disjoint from E[4] and O.
All actual support/denominator conditions are still checked. The same
orientation as the stored packet pairs values relative to i=3b.
[pcc:unverified]

The quotient-polynomial verifier checks entire degree2/3 algebras,
including nonreduced cases, against both C7 equations and the explicit
maps. The length3 origin jet has basepoint(1:0:-1), satisfies the curve
modulo t3, and has nonzero tangent coordinate since (Z/X)' at0 is2.
It gives the specified embedded jet; no native genus3 divisor reduction
or arbitrary-target solver follows from these fixed correspondences.
[pcc:unverified]

The actual F7 isomorphism beta:E7^3->Jac(C7), its inverse alpha and
Gram H remain the prior3-torsion/conic/geometric proof dependency.
Through beta, the checked finite point actions are actual J[4] and
J(F7) actions, rather than an unproved synthetic product identification.
Exact integer coefficient identities transport to Hom compositions by
the actual CM action w=Frobenius+2. In particular ell*S*v=1 gives a
global left inverse, and ell Hinv ell*=4 gives the degree4 cover through
standard Jacobian universal-property/push-pull facts. Those general
Hom/polarization/Jacobian bridges remain absent from the Core Lean
coefficient leaves. Finite modulo11 inverses do not replace them: the
rational-point recipe inverse3=4 yields global[12]L/degree576.
[pcc:unverified]
