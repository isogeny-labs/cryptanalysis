# The E y-coordinate separates the full level-432 fiber

Above the frozen \(C=(639,232)\in X_0(27)(\mathbf F_{997})\), the
24 geometric level-16 lifts have **24 distinct \(y_E\) coordinates**.
Their \(x_E\) coordinates occur in 12 pairs. Consequently the rational map
\(X_0(432)\dashrightarrow X_0(27)\times\mathbf A^1\) given by \((C,y_E)\) has
generic degree one: the good-reduction collision argument in the
[preceding proof](../hecke-432-generic-degree-20261025/RESULT.md)
applies with the affine y-coordinate on the finite set of points in
this selected fiber. This removes \(x_E\) from the generators needed
for the function field of the paired image.

## Frozen coordinate census

The [fiber protocol](protocol.json) fixes the geometric-fiber input,
the proposed rational-function ansatz, two auxiliary primes, and the
training/holdout boundary before evaluation. The [coordinate audit](fiber_audit.py)
reads all 24 successful E points from the independently replayed
GF(997⁴) experiment. It records 24 distinct y values and 12 distinct
x values, each x with multiplicity two. The exact source and prior
arithmetic-audit hashes are in [fiber_result.json](fiber_result.json).
Since the previous proof identifies these points with the complete
special fiber of the étale degree-24 forgetful map, absence of a
y-coordinate collision in that fiber gives a nonempty generic open
with no collision. The checked Lean implication
`YPrimitive.y_image_card` proves that an injective y-coordinate on
24 indexed sheets has a 24-element image. The modular-model
specialization step remains a written proof; its Lean formalization
requires the integral modular-curve and map definitions listed in the
preceding proof map.

## A specialized degree-12 resolvent

After the separation result, the [interpolation protocol](interpolation_protocol.json)
froze a constructive fiber calculation. Over
\(K=\mathbf F_{997}[u]/(u^4+4u^2+622u+7)\), form
\(M(T)=\prod_{i=1}^{24}(T-y_{E,i})\) and interpolate the unique
\(P(T)\) of degree at most 23 with \(P(y_{E,i})=x_{E,i}\).
The pure-Python [certificate](interpolation.json) finds
\(\deg M=24\), \(\deg P=22\), and all coefficients in
\(\mathbf F_{997}\). Both polynomials are even. Thus, with
\(z=T^2\), they take the smaller form
\[
M(T)=Q(z),\quad P(T)=R(z),\qquad \deg Q=12,\quad \deg R=11,
\]
where \(Q,R\in\mathbf F_{997}[z]\) and
\(Q\mid(R(z)^3-z+432)\). The full coefficient lists are saved in
the certificate. Sage independently checks all 24 point evaluations,
both polynomial identities, and the modular remainder; its
[verification receipt](interpolation_verification.json) reports
`PASS_SAGE_INTERPOLATION_REPLAY`. The degree-24 fiber polynomial
factors over \(\mathbf F_{997}\) into eight linear, four quadratic,
and two quartic factors, matching the observed Frobenius orbits.
The even specialized form is a measured property of this fiber; a
global rational resolvent over \(\mathbf Q(X_0(27))\) is the next
construction.

## Rational x_B reconstruction screen

The normalized \(B=432a1\) coordinate was screened with
\[
A(x_C,y_C,y_E)x_B+B(x_C,y_C,y_E)=0,
\]
using monomials \(x_C^a y_C^b y_E^k\), \(b\in\{0,1\}\), of pole
weight \(2a+3b+3k\); A has weight at most D and B at most D+2.
The input q-series and their earlier independent curve/isogeny replay
are hash-bound. Each matrix uses q-exponents from \(-(D+2)\) through
900; terms through 980 were reserved as a holdout. All eight matrices
have full column rank:

| D | Columns | GF(997) rank / minor | GF(1009) rank / minor |
| ---: | ---: | ---: | ---: |
| 24 | 235 | 235 / 464 | 235 / 681 |
| 32 | 397 | 397 / 692 | 397 / 934 |
| 40 | 603 | 603 / 59 | 603 / 692 |
| 48 | 851 | 851 / 100 | 851 / 244 |

The [Sage screen](screen_result.json) records every monomial and pivot
row. [Independent NumPy replay](verification.json) reconstructs the
Laurent monomials and all eight nonzero minors without Sage matrix
linear algebra. The q-series coefficients are 997- and 1009-integral
through the tested range; each nonzero modular minor is a nonzero
rational minor. Nesting therefore excludes every smaller weight bound
in this linear-in-\(x_B\), y-only ansatz. The inherited checked Lean
lemma `DirectLiftRank.no_relation_of_nonzero_minor` proves the abstract
nonzero-minor implication; concrete determinants are independently
computed rather than encoded in Lean.

| Result | Evidence and formalization |
| --- | --- |
| 24 distinct y outputs and 12 paired x outputs | Complete geometric-fiber receipt and `fiber_audit.py`; `YPrimitive.y_image_card` checks the finite-set implication in Lean. |
| Generic degree one for the C/y map | Written finite-étale specialization proof inherited from the paired-map argument, using the 24 distinct y values. Full integral-moduli formalization remains open. |
| Specialized Q/R polynomial identity | Pure-Python GF(997⁴) interpolation and independent Sage polynomial replay. A Lean certificate for the 24 concrete coefficients remains open. |
| No tested rational x_B relation through D=48 | Eight full-rank matrices and independently replayed pivot minors; inherited Lean nonzero-minor implication. |

The Lean module builds with the toolchain and Mathlib revisions in
[formal/DEPENDENCIES.json](formal/DEPENDENCIES.json); its
[`#print axioms` output](formal/build-output.txt) lists only standard
foundations. For replay, use the checked Sage launcher:

```sh
python3 experiments/hecke-432-y-primitive-20261025/fiber_audit.py
./sage --runtime-info
./sage -python experiments/hecke-432-y-primitive-20261025/screen_sage.py
python3 experiments/hecke-432-y-primitive-20261025/verify.py
python3 experiments/hecke-432-y-primitive-20261025/interpolate.py
./sage -python experiments/hecke-432-y-primitive-20261025/verify_interpolation_sage.py
```

The next reconstruction should compute a **relative** degree-12
polynomial for \(z=y_E^2\) over \(\mathbf Q(X_0(27))\) and a trace
interpolation for \(x_B\) in the degree-24 y-basis. That uses the
observed 12 sign pairs and degree-one property directly, instead of
expanding the unrestricted monomial screen to still larger pole weights.
