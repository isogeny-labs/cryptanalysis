# The paired X₀(27) and E projection has generic degree one

The morphism
\[
 (f,g):X_0(432)\longrightarrow X_0(27)\times E,
 \qquad E:y^2=x^3+432,
\]
where \(f\) forgets the cyclic-16 factor and \(g\) is the normalized
level-432 map projected to E, is **birational onto its image over
\(\mathbf Q\)**. The decisive witness is the complete degree-24 fiber
above \(C=(639,232)\) in characteristic 997: its 24 geometric points
have 24 different E images. Good reduction transports the absence of
collisions to a nonempty open set in characteristic zero.

## Exact specialization witness

The [geometric-fiber experiment](../hecke-432-geometric-fiber-20261025/RESULT.md)
freezes the source curve \(y^2=x^3+616x+645\), \(j=18\), its indexed
cyclic-27 chain, and the resulting \(C=(639,232)\) on
\(X_0(27):y^2+y=x^3-7\). Nonbacktracking 2-isogeny chains enumerate
all \(3\cdot2^3=24\) cyclic-16 choices. Over \(\mathbf F_{997^4}\),
the exact quarter-shift evaluator computes 24 distinct E outputs;
the independent field-arithmetic audit checks all curve equations,
Frobenius equivariance, and agreement with the eight rational outputs
from the earlier census.

The new [local audit](audit.py) binds those receipts and the rational
coordinate functions by SHA-256, checks the selected C equation and source
\(j\)-invariant, and verifies the following explicit good-reduction data:

| Quantity | Residue modulo 997 |
| --- | ---: |
| Discriminant of source curve \(y^2=x^3+616x+645\) | 3 |
| Discriminant of \(X_0(27):y^2+y=x^3-7\) | 257 |
| Discriminant of \(E:y^2=x^3+432\) | 837 |
| Source \(j\) | 18 |

Here \(997\nmid432\) and \(18\not\equiv0,1728\pmod{997}\).
All 120 saved coefficients of the exact rational functions for
\(j(\tau),j(3\tau),j(9\tau),j(27\tau)\) have denominators prime to 997.
The underlying function identities were established by q-expansion and
pole-degree certificates in the [level-27 coordinate bridge](../hecke-27-coordinate-bridge-20261025/RESULT.md)
and [intermediate-invariant derivation](../hecke-432-prime887-20261025/RESULT.md).
The quarter-shift construction and its equality with the normalized E
projection have the [Sturm-bound identity](../hecke-432-map-identity-20261025/RESULT.md).

## Proof

Work over \(R=\mathbf Z_{(997)}\) and, when orienting the two
quarter shifts, its finite étale extension adjoining \(i=\sqrt{-1}\).
The smooth modular models at a prime away from 432 parametrize the
prime-to-997 cyclic subgroups. The selected source has automorphism group
\(\{\pm1\}\), since its \(j\)-invariant is neither 0 nor 1728;
these automorphisms fix every cyclic subgroup. Therefore the forgetful
map \(f:X_0(432)_R\to X_0(27)_R\) is finite étale of degree 24 in a
neighborhood of the selected C point. The degree is the count of
cyclic order-16 subgroups of a rank-two 16-torsion module.

The E curve has good reduction at 997. Its good-reduction model is a
Néron model, so the characteristic-zero morphism \(g\) extends uniquely
from the smooth modular curve to this model over R. The moduli description
of the quarter shifts uses only subgroup quotients, dual isogenies, the
Weil pairing on 4-torsion, and the group law on the good-reduction
\(X_0(27)\) model; these operations commute with reduction because 2 and
3 are units in R. The exact rational j-functions have 997-integral
coefficients and their denominators are nonzero at each selected
coordinate lift, as checked by the evaluator. Thus the 24 saved E points
are the reduction of \(g\) on the entire special fiber of \(f\) over C.
Changing the global quarter-shift orientation negates every E output
uniformly and leaves pairwise distinctness intact. The Néron mapping
property and the smooth prime-to-level modular models are standard;
see [Conrad's Néron-model notes](https://math.stanford.edu/~conrad/mordellsem/Notes/L11.pdf)
and the [Deligne–Rapoport model discussion](https://msp.org/ant/2017/11-9/ant-v11-n9-p.pdf).

Let \(X=X_0(432)_R\) and \(C_R=X_0(27)_R\), restricted to this
étale neighborhood. In \(X\times_{C_R}X\), the diagonal is open and
closed. On its closed complement, the locus where the two g images
agree is closed because E is separated. Its image in \(C_R\) is closed
because the fiber-product projection is finite. The 24 distinct E
values show that this image omits the selected special C point. Its
complement is therefore an open neighborhood that meets the generic
fiber. Over that generic open the pair \((f,g)\) is injective on every
geometric f-fiber. Since \(X_0(432)_{\mathbf Q}\) is an irreducible
smooth curve, the induced extension of function fields has degree one.
Hence the paired morphism is birational onto its image. The diagonal,
equalizer, and finite-map steps use the [Stacks Project separation](https://stacks.math.columbia.edu/tag/01KH)
and [finite étale](https://stacks.math.columbia.edu/tag/0BL6) results.

## Proof map and replay

| Obligation | Evidence | Formalization status |
| --- | --- | --- |
| Characteristic-zero E map equals the quarter-shift projection | Prior q-series, Sturm bound 144, cusp normalization, and exact group-law identity | Written modular proof; Lean modular-form bridge open |
| Prime-to-997 good models and étale 24-cover at selected C | 997 coprime to 432, source \(j=18\), three nonzero discriminants, standard modular-model theorem | Written proof; integral modular objects absent from current Lean project |
| Reduction of g agrees with evaluated 24 outputs | Moduli isogeny construction, 997-integral coordinate functions, nonzero evaluated denominators, source hashes, prior independent GF(997⁴) audit | Exact executable certificate and written reduction argument; no Lean isogeny-moduli model |
| Empty off-diagonal equalizer near C implies generic degree one | Finite étale diagonal and finite closed-image argument above | Written proof; scheme-theoretic specialization not yet formalized in Lean |
| 24 distinct finite-field values give 24 image points | `GeometricFiber.image_card_of_pairwise_separation` in the preceding PR, with pairwise separation as hypothesis | Checked Lean 4 theorem under pinned toolchain and Mathlib revisions |

The full scheme-theoretic theorem remains open in Lean because the pinned
project does not yet define integral modular curves, cyclic level
structures, the E projection, or the collision equalizer. The written
proof retains those objects and the exact reduction hypotheses rather
than replacing the theorem with its finite-set implication.

Replay the local audit with
`python3 experiments/hecke-432-generic-degree-20261025/audit.py`.
The [receipt](audit.json) is
`PASS_EXPLICIT_GOOD_REDUCTION_AND_SOURCE_BINDINGS`.
The next constructive step is to recover a rational function-field
expression for the inverse to the paired image, using the now established
degree-one property and higher-pole q-series data.
