# Fixed Ciani bitangent coordinate construction

Prospective361ee8 fixes the original q223/seed1 case and all controls before
this implementation. This construction is proposed until the original native
test passes; no new nondual isogeny is asserted. [pcc:unverified]

Use the original Ciani coordinates X,Y,Z and coefficients

    aX^4+bY^4+cZ^4+dX^2Y^2+eY^2Z^2+fZ^2X^2=0.

All six coefficients are recovered from the original Core.rmat. Its original
inverse Moore matrix maps W to(X,Y,Z). Expanding through this matrix must
match every coefficient of the actual fixed F223 quartic up to its original
normalizing scalar. The field is the original Rabin-checked
L=F223[w]/(w^6−3), with the original K embedding z=w². [pcc:unverified]

The three families with a zero line coefficient are obtained by requiring
the even binary quartic on Y=vZ, Y=uX or X=wZ to be a scalar times a square.
This yields a quadratic in v²,u²,w² respectively, followed by square-root
equations in the original finite-extension polynomial engine.
[pcc:unverified]

For a line Y=uX+vZ with u,v nonzero, put U=u²,V=v² and define

    A=a+dU+bU², H=d+2bU, Delta=4ab−d²,
    C=A*((2ea−df)+(de−2bf)U),
    L=Delta*(a−bU²), D=A*(f+eU),
    E=A*(d+6bU)−U*H².

The restricted quartic has coefficients, from X^4 to Z^4,

    A, 2uvH, f+eU+(d+6bU)V, 2uv(e+2bV), c+eV+bV².

For A nonzero, comparison with a scalar times a quadratic squared gives

    C+LV=0,
    4A³*(c+eV+bV²)−(D+EV)²=0.

The implementation checks the unfactored identities for C and L using
original polynomial arithmetic before using them. It obtains U from

    R(U)=4A³*(cL²−eCL+bC²)−(DL−EC)²=0.

For L nonzero take V=−C/L; for L=C=0 solve the second quadratic in V
directly. L=0,C nonzero gives no solution. A=0 is impossible for a generic
bitangent in this chart: its cubic coefficient2uvH would also need to vanish,
forcing A=H=0, contrary to Delta nonzero. Coordinate-zero families are handled
separately. Root equations and every actual line certificate remain required;
the resultant alone does not certify a bitangent. [pcc:unverified]

Each candidate line is transported to actual W coordinates, normalized and
deduplicated. Restrict the original15-coefficient quartic to that line and
require all five binary coefficients to equal scale times Q². Contact Q
may have a root at infinity, repeated roots or nonsplit affine roots. The
test checks gradient/line minors modulo Q in both charts and rejects a fixed
one-coefficient mutation of each contact certificate. These checks use the
original FpR/polynomial arithmetic. [pcc:unverified]

The required native count is28 distinct certified lines. The usual theorem
that a smooth nonhyperelliptic genus3 plane quartic in odd characteristic has
28 odd theta characteristics/bitangents is a written completeness bridge,
not a Lean theorem supplied here. A normalized actual Frobenius permutation
and all orbits are computed directly from the coordinates. No Jacobian
torsion basis, Weil pairing, kernel census or codomain map follows from these
coordinate checks alone. Those remain subsequent obligations.
[pcc:unverified]
