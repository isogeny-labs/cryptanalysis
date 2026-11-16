# Finite-kernel height-ball packing

The checked theorem `XedniFiniteKernelPacking.bounded_relation_of_finite_kernel_norm_gap` derives a bounded integer relation from the size of an additive projection's finite kernel. Its hypotheses give `r` selected points in an additive group `H`, an additive projection to a finite-dimensional real normed space, a point-norm cap `B`, and a minimum nonzero projected norm `δ>0`. If the kernel is contained in a recorded finite set of size `T` and

`T * (1 + 2rKB/δ)^d < (2K+1)^r`,

then a nonzero relation exists with each coefficient of magnitude at most `2K`, where `d` is the real dimension of the target space.

The finite-kernel step removes the separately supplied torsion-label function of PR #1652. For each occupied projection value, the Lean proof chooses one representative. Every value in that fiber differs from its representative by an element of the projection kernel. The map from an original value to its projected value and kernel difference is injective, yielding `|values|≤|projected values|·T`. The earlier checked Euclidean packing theorem bounds the projected values; the coefficient-box theorem turns the strict count into a relation.

## Proof map

| Result | Lean declaration | Exact hypotheses |
| --- | --- | --- |
| Fiber count | `XedniFiniteKernelPacking.finite_kernel_card_le_projected_card` | Additive projection; every zero-projection element belongs to the finite recorded kernel set |
| Euclidean count with kernel | `XedniFiniteKernelPacking.finite_kernel_card_le_radius_ratio_pow` | Fiber count, radius `R≥0`, minimum separation `δ>0` on distinct projections |
| Bounded relation | `XedniFiniteKernelPacking.bounded_relation_of_finite_kernel_norm_gap` | Point norm cap `B≥0`, global projected norm gap `δ>0`, finite kernel set, and strict count below `(2K+1)^r` |
| Selected elliptic-lift application | Open | Construct the real Mordell–Weil quotient and canonical-height norm; establish finite torsion kernel and uniform selected-lift height premises |

In the elliptic application, the intended projection sends a rational point to its class in the torsion-free Mordell–Weil group tensored with `ℝ`. Its kernel is the torsion subgroup. The selected-lift application needs this construction in Lean and the arithmetic bounds on canonical heights and nonzero minimum height for the relevant lifted curves. The theorem retains those requirements as explicit inputs and states their structural consequence.

The formal project pins Lean `v4.35.0-rc4` and Mathlib `021c46bdd042f67b538b9f9871d556a93713a9a9`. `lake build FiniteKernelPacking` completed 2705 jobs. Each of the three new `#print axioms` outputs lists only `propext`, `Classical.choice`, and `Quot.sound`. The imported Euclidean packing and pigeonhole sources are exact copies from prior checked PRs, with hashes recorded in `DEPENDENCIES.json`. `lean4checker --fresh` was unavailable on this host.

## Exact controls

`run.py` enumerates 68 finite-kernel controls on `ℤ²×ℤ/T` with `T=1,2,3,4`, coefficient radii `K=0,…,16`, and points `(1,0,0)`, `(0,1,0)`, `(1,1,1)`. It records every projection fiber, its maximum occupancy, the exact original count, and the Euclidean packing comparison `T(1+4√2 K)²`. All 68 fiber and packing inequalities hold. Integer-square comparisons avoid floating-point rounding.

| Kernel size `T` | First `K` certified by packing | Distinct sums | Box size | Largest observed fiber |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 3 | 127 | 343 | 1 |
| 2 | 7 | 1178 | 3375 | 2 |
| 3 | 11 | 4167 | 12167 | 3 |
| 4 | 15 | 10108 | 29791 | 4 |

Sixteen counterexample controls use the projection `ℤ²→ℤ`, `(x,y)↦x`, on values `(0,n)` for `−K≤n≤K`. Each has one projected value and `2K+1` original values. They demonstrate that a projected-value count needs a finite fiber bound: assigning kernel size one to this infinite-kernel projection fails for every recorded `K≥1`.

The next step is to formalize the torsion-free Mordell–Weil projection and its canonical-height norm for the selected lift family, then test the uniform height premises that control `B/δ`.
