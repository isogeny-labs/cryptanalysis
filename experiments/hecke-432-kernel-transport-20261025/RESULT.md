# Generator-free level-432 evaluation at p=883

The kernel-chain evaluator maps all **864 noncuspidal rational points** of
\(X_0(432)(\mathbf F_{883})\) to **36 points** of
\(B(\mathbf F_{883})\), where \(B:y^2=x^3-16\). Each image point has
**24 source chain pairs**. The full B group has 931 points, so exactly 895
points are absent from the noncuspidal image. Accounting for the 24 rational
cusps separately gives a rigorous lower bound of 871 points absent from the
whole rational modular-curve image. The actual cusp images remain to be
evaluated for an exact whole-curve count.

| Source stratum | Chain pairs | Distinct B images | Fiber size |
| --- | ---: | ---: | ---: |
| Trace 20 representatives | 432 | 18 | 24 |
| Trace 52 representatives | 432 | 18 | 24 |
| Combined noncuspidal source | **864** | **36** | **24** |

The two stratum image sets are disjoint. All 54 previously measured
rational-generator subgroups match their generator-free chain entry and B
output. The earlier witness pair \((1,1)\) maps to \((281,882)\), and the
cubic-extension witness pair \((1,0)\) maps to \((216,882)\).

## Construction and exact checks

An input consists of the four rational 2-isogeny edges and three rational
3-isogeny edges recorded by the [complete source census](../hecke-432-stable-kernel-chains-20261025/RESULT.md).
The first two 2-edges form \(q:E\to E_0\) of degree four; the remaining two
form \(\psi:E_0\to E_{16}\). The dual of \(q\) is composed from the two
prime-degree duals. Its kernel supplies \(T\), while \(\ker\psi\) supplies
\(R\), both of order four over \(\mathbf F_{883^2}\). We orient \(T\) by
\(e_4(R,T)=i\), \(i^2=-1\).

The three 3-edges form an isogeny with cyclic kernel \(C_{27}\). Its full
kernel polynomial has 13 distinct x-roots. Sage's `push_subgroup` applies
the rational x-map of \(q\) to that polynomial, yielding the 13-root
polynomial of \(q(C_{27})\); coprime degrees preserve its order. Quotienting
by \(\langle T+R\rangle\) and \(\langle T-R\rangle\), then pushing the
27-kernel polynomial through each quotient, gives two exact pairs of source
and quotient j-values on \(X_0(27)\). The previous
[coordinate bridge](../hecke-27-coordinate-bridge-20261025/evaluate_sage.py)
inverts each j-pair to a point on \(y^2+y=x^3-7\). Frobenius conjugacy,
the twist to \(y^2=x^3+432\), and the unique rational dual-isogeny preimage
recover the B point. The [Sage isogeny interface](https://doc.sagemath.org/html/en/reference/arithmetic_curves/sage/schemes/elliptic_curves/hom.html)
describes the kernel-polynomial and subgroup-push operations used here.

For 816 inputs each j-pair has one coordinate lift. For 48 inputs each has
two; the Frobenius and dual-isogeny conditions still select exactly one B
point. `audit.py` checks complete one-to-one coverage of all input chain
keys, the 36 images and 24-fold fibers, and all 54 earlier controls.
`full_result.json` retains every path, j-pair, coordinate count, and B
output, including the 48 multi-lift rows.

This is an exhaustive exact finite-field evaluation, with no wall-time
comparison or IC candidate assigned. It removes the extension-degree-18/36
generator construction from this finite-field evaluation path; the producer
uses \(\mathbf F_{883^2}\) for the 4-torsion orientation and coordinate
descent. This result does not determine an inverse map for points outside
the 36-point noncuspidal image.

## Proof map and replay

| Result | Evidence and formalization |
| --- | --- |
| Kernel transport through q and both shifted quotients | Exact isogeny compositions, 13-root squarefree kernel polynomials, degree-27 quotient checks in `evaluate_sage.py`; written coprime-kernel argument above. A Lean elliptic-isogeny formalization remains open. |
| 864 inputs, 36 images, 24 per image | Full enumeration in `full_result.json`; independent key and fiber audit in `audit.json`; all 54 prior generator outputs agree. Enumeration is executable evidence, not a Lean theorem. |
| 895 B points outside the noncuspidal image | `ExactImageGap.exactly_895_missing` proves the finite-set implication given image cardinality 36 and target cardinality 931. `#print axioms` reports only `propext`, `Classical.choice`, and `Quot.sound`. |
| At least 871 B points outside the whole rational source image | Written bound: at most 24 additional images arise from the 24 rational cusps. Exact cusp images are open. |

The Lean toolchain is `leanprover/lean4:v4.35.0-rc4` with mathlib revision
`021c46bdd042f67b538b9f9871d556a93713a9a9`. The checked command and
output are in `formal/build-command.txt` and `formal/build-output.txt`;
`lean4checker --fresh` was unavailable. The Sage startup receipt is
`sage-runtime-info.txt`.

From the repository root, replay with
`./sage -python experiments/hecke-432-kernel-transport-20261025/evaluate_sage.py --all`
and `python3 experiments/hecke-432-kernel-transport-20261025/audit.py`.
The launcher verifies the accepted Sage build before each run. On this host,
the producer redirects Sage's lazy-import cache to the research volume
because the system temporary volume is full; that cache is outside the
arithmetic path. `SEAL.sha256` binds the persisted files.
