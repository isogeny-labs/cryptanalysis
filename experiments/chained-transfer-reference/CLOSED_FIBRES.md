# CT23 closed-fibre Richelot chart: written algebraic bridge

This document states equality of a new evaluation chart with the retained
completed Richelot correspondence. Its runtime domain is the actual R0/R1
maps overF101 and their existing F101^6 coefficient field. A generic algebra
argument does not enlarge supported curves. Native acceptance and exact
source/receipt identifiers belong to CLOSED_FIBRES_CHECKPOINT.md. This text
makes no measured-cost claim. Scientific standing is unsigned.
[pcc:unverified]

## Existing correspondence and its normalization

Use the actual quadratic splittings g1,g2,g3 and their duals h1,h2,h3 from
the unchanged validated construction, including determinant and ordering.
The raw models have equations y_raw²=product(g), w_raw²=product(h), and

    g1(x)h1(z)+g2(x)h2(z)=0,
    y_raw*w_raw=g1(x)h1(z)(x-z).

This is Kunzweiler, DCC92 (2024), §3.2 Proposition8, with its own normalized
hi convention; our actual g/h identities and scales are retained from the
existing construction, rather than copied from a different twist. The
publisher PDF/hash is in SOURCES_20261111.md. Proposition7 supplies the
nondegenerate Jacobian codomain. Its subsequent degree5/rational-Weierstrass
assumptions are not hypotheses of our split-sextic arithmetic. The accepted
maps' projective completion and positive-adjoint reverse sign remain the
ones already proved in SEVEN_CHAIN_PROOF.md. [pcc:unverified]

Let the normalized source/target ordinates be y and Y, with
source_scale*y=y_raw, target_scale*Y=w_raw. Forward source_scale=1 and
target_scale=22 forR0 or47 forR1. Reverse uses source_scale=22/47 and
target_scale=1, then the existing final negation. No new choice of twist,
square root, polarization or descent datum is introduced. [pcc:unverified]

## Elimination retains the finite scheme, including multiplicities

Work over a field K of characteristic different from2 on a valid source
support u=x²+a*x+b, ordinate y=v(x). Reduce the first correspondence
modulo u, obtaining A(z)*x+B(z), with degA,degB at most2. Put

    R(z)=B(z)²-a*A(z)*B(z)+b*A(z)².

The exact polynomial identity

    (A*x+B)*(B-a*A-A*x)+A²*u(x)=R(z)

shows that R vanishes in S=K[z,x]/(u,A*x+B). Assume degR=4 and A is a
unit moduloR. A Bezout identity for A andR also makes A a unit in S.
Hence x=-B/A there. Conversely, in K[z]/R the element x=-B/A satisfies
u(x)=R/A²=0 and A*x+B=0. The two natural algebra maps are mutual
inverses. Thus the projection is an isomorphism of finite algebras,

    S ≅ K[z]/R.

This is an algebra identity, not a check on a finite collection of points or
a density argument. It remains true with nilpotents. For repeated support
u=(x-t)², its resultant is (A*t+B)², so multiplicity has not been discarded.
A valid Mumford ordinate carries the required jet modulo u, and the algebra
isomorphism transports that jet. [pcc:unverified]

If A is not a unit or degR drops, this chart is rejected with a specific
route code; no inverse is taken. These conditions reject a coordinate
chart, not the isogeny. Prime-input evaluation then uses the original
completed pointwise map on that exact input. Extension inputs return an
explicit boundary rather than assuming their support splits in K.
[pcc:unverified]

## Ordinate recovery and actual target divisor

Assume source_scale*target_scale*v(-B/A) is a unit moduloR. In K[z]/R set

    Y=g1(-B/A)*h1(z)*(-B/A-z)
      /(source_scale*target_scale*v(-B/A)).

The first correspondence and source ordinate identities hold in this
algebra. The second correspondence holds by the explicit inverse; the
existing Richelot identity then gives Y²=the normalized target sextic.
Runtime also checks u(-B/A)=0, A*(-B/A)+B=0 and that target equation
moduloR, independently of the reduction result. The monic pair (R,Y)
therefore describes exactly the pushforward finite scheme, with its
multiplicities, without choosing support or target roots. [pcc:unverified]

A nonunit ordinate denominator is another explicit chart boundary. In
particular branch support is never divided by zero. Target degree drops
are not silently omitted; they retain the existing projective completion
through prime-input fallback. [pcc:unverified]

## Balanced divisor and shared reduction

Write K_target=infinity_plus+infinity_minus. Each completed fibre class is
its degree2 target scheme minus K_target, consistently with the existing
pointwise evaluator. Two source support points, counted with multiplicity,
therefore give a four-point target divisor minus2*K_target. In the raw
balanced representation

    finite_m + n*infinity_plus + (2-m-n)*infinity_minus - K_target,

m=4,n=-1 represents precisely finite4-2*K_target. The code passes that
signed raw parameter to the same reduction previously used by Cantor
addition. The existing body is factored into a shared method without a
changed formula or acceptance check. Its reduction is a principal-divisor
operation; it is not a new group law. Canonical output validity is checked.
[pcc:unverified]

Degree0/1 supports use the old whole-fibre/infinity helpers directly in the
same coefficient field. For finite degree m and balanced plus count n,
add (2*n+m-2) times the original positive-infinity fibre. The negative
infinity fibre is its negative as already fixed in the completed map.
The reverse evaluator retains its final sign. Consequently the new chart
and every fallback agree with the original Picard correspondence on their
actual supported inputs. This equality carries the existing global maps,
dual norms and descent data; it does not need a new finite-to-global leap.
[pcc:unverified]

## The actual Psi kernel obligation

The accepted global square is Psi*R0=R1*Phi, with degPsi=49. The known
Phi kernel has49 geometric7-torsion points in the existing F101^6 field.
R0 has2-primary kernel, so is injective on those points. Their images are
therefore49 distinct points killed byPsi, hence its full geometric kernel
by the known degree and separability. The new evaluator allows writing
these actual T0 divisor classes without a support-root extension. The
acceptance test must still compute every image, check7-annihilation,
all2401 additions and Frobenius action, and compare geometric dualR0
composition with[2]. An unsupported chart is an outstanding computation,
not a proof that the corresponding point does not exist. [pcc:unverified]

## Formalization map and independent controls

ClosedFibres.lean supplies six cleared commutative-ring identities:
quadratic remainder, resultant identity, linear/quadratic coordinate
recovery with an explicit inverse, repeated-support resultant and cleared
ordinate recovery. PCCa97f41/gate01 records that partial source. Coordinate
rings/Bezout algebra isomorphism, Mumford jets, scheme-theoretic pushforward,
projective completion and Picard reduction remain written bridges above.
The full construction is not claimed Lean formalized. [pcc:unverified]

The retained pointwise implementation uses Fp2 splitting for prime supports
and combines it with cubic kernel coefficients in Fp6; the new chart uses
closed polynomial arithmetic in the original coefficient field. On prime
inputs those operands are in the cubic subfield, by closure under the
existing arithmetic. The implementation still uses the existing tower
representation, so avoiding root selection is not itself an operation-count
or measured-cost advantage. Full all-class comparison, independent flat/tower
and elliptic kernel controls, failed attempts and unsigned PCC standing
must be reported at their actual tested scope. [pcc:unverified]
