# Rational elliptic torsion kernel for finite packing

The Lean theorem `XedniEllipticTorsionKernel.bounded_relation_of_rational_curve_norm_gap` instantiates the finite-kernel packing bridge on rational elliptic-curve points. Mathlib's Northcott and elliptic finite-torsion theorems supply a finite torsion set; `torsionKernel_card` identifies its cardinality with `Nat.card` of the torsion subgroup. Under an additive projection whose zero fiber is torsion, a norm cap `B` on the selected points, a minimum nonzero projected norm `δ>0`, and the strict count

`T * (1 + 2rKB/δ)^d < (2K+1)^r`,

the checked theorem returns a nonzero relation with integer coefficients of magnitude at most `2K`. Here `T` is the actual torsion-set cardinality and `d` is the finite real dimension of the projection target.

## Proof map

| Result | Lean declaration | Exact hypotheses |
| --- | --- | --- |
| Torsion membership in finite set | `XedniEllipticTorsionKernel.mem_torsionKernel` | Elliptic Weierstrass curve over a field with admissible absolute values and Northcott property |
| Torsion-set cardinality | `XedniEllipticTorsionKernel.torsionKernel_card` | Same field and curve hypotheses; exact `Nat.card` of the torsion subgroup |
| Elliptic relation bridge | `XedniEllipticTorsionKernel.bounded_relation_of_elliptic_torsion_norm_gap` | Additive projection with kernel contained in torsion; point cap, global norm gap, strict packing count |
| Rational-curve specialization | `XedniEllipticTorsionKernel.bounded_relation_of_rational_curve_norm_gap` | Mathlib's number-field instances supply Northcott for `ℚ`; remaining projection and norm assumptions stated explicitly |
| Canonical-height projection for selected lifts | Open | Construct the torsion-free Mordell–Weil real tensor and canonical-height norm; establish uniform height and norm-gap premises for the selected lift family |

The rational specialization removes the need to assume torsion finiteness separately. The current formal project uses Mathlib's naive-height and finite-torsion API; it does not construct the canonical-height projection. The selected-lift height and minimum-height estimates are arithmetic premises to establish or retain conditionally.

The formal project pins Lean `v4.35.0-rc4` and Mathlib `021c46bdd042f67b538b9f9871d556a93713a9a9`. `lake build EllipticTorsionKernel` completed 3507 jobs. All four new `#print axioms` receipts list only `propext`, `Classical.choice`, and `Quot.sound`. The imported finite-kernel, Euclidean packing, and pigeonhole sources are pinned exact copies. `lean4checker --fresh` was unavailable on this host.

## Checked-Sage rational-curve control

The frozen control is `E/ℚ: y²=x³−x−2` with `P=(2,2)`, already used by the fixed-curve xedni admission study. The checked Sage launcher reports rank one, trivial torsion, and `P` equal to its generator up to sign. Sage's `Point.height()` uses its default normalised Néron–Tate convention; it returns `ĥ(P)=1.06598813993015` at the displayed precision, and the double/triple height ratios `4` and `9` at that precision. The ratio `B/δ` below is invariant under a common height rescaling. For selected points `P,2P,3P`, the quotient has `d=1`, `T=1`, `B=3√ĥ(P)`, and `δ=√ĥ(P)` under the generator assertion, giving the finite bound `1+18K`.

| Coefficient radius `K` | Box vectors | Distinct rational sums | Packing upper bound |
| ---: | ---: | ---: | ---: |
| 0 | 1 | 1 | 1 |
| 1 | 27 | 13 | 19 |
| 2 | 125 | 25 | 37 |
| 3 | 343 | 37 | 55 |
| 4 | 729 | 49 | 73 |

The packing bound first falls below the coefficient-box count at `K=1`; the exact control contains the relation `2P−(2P)=0` with coefficients bounded by `2`. The independent checked-Sage audit reconstructs the curve, rank, torsion, generator relation, scalar interval, all exact point sums, and every threshold row. Both producer and audit exited zero with empty stderr. `sage-runtime-info.json` records the accepted local Sage build before the jobs. These are exact group counts and a displayed-precision height diagnostic; they do not supply the uniform bounds for the selected xedni lift family.

The next experiment is to construct the canonical-height projection formally and freeze a selected-lift family so the required `B/δ` bound can be tested or established curve by curve.
