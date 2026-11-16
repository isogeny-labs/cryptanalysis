# Checked finite Euclidean packing bound

Theorem `XedniEuclideanPacking.card_le_radius_ratio_pow` gives an explicit finite bound in any finite-dimensional real normed space `E`. For a finite set `S` contained in the closed radius-`R` ball about zero, with distinct points separated by at least `δ>0`,

`|S| ≤ (1 + 2R/δ) ^ finrank(ℝ,E)`.

The Lean proof constructs pairwise disjoint open balls of radius `δ/2` around the points of `S`, contains their union in the ball of radius `R+δ/2`, and compares Haar volumes. The first theorem retains the uncancelled volume inequality; the second divides by the strictly positive smaller-ball volume. It covers rank zero and `R=0` without an exceptional case.

`labelled_card_le_radius_ratio_pow` charges a finite label set for the fibers of a projection onto `E`. `bounded_relation_of_euclidean_packing` then composes this bound with the full coefficient-box pigeonhole theorem. If the radius and separation hypotheses hold for all distinct projected sums from `|aᵢ|≤K`, equal projections and equal labels identify a unique sum, and

`T * (1 + 2R/δ)^d < (2K+1)^r`,

the theorem returns a nonzero integer relation among the `r` points with each coefficient of magnitude at most `2K`. Here `T` is the cardinality of the supplied label set and `d=finrank(ℝ,E)`.

For a canonical-height quotient, take `E` to be the real tensor of the torsion-free Mordell–Weil lattice, `||P||²=ĥ(P)`, `δ=√μ` for a lower bound `μ>0` on nonzero canonical height, and `R=K∑ᵢ√ĥ(Pᵢ)`. If `ĥ(Pᵢ)≤M`, then `R≤rK√M`. A finite torsion label set accounts for fibers. Thus the checked geometric theorem supplies the finite count `T(1+2rK√(M/μ))^d` once these arithmetic objects and inequalities are instantiated. The selected xedni lift family still requires a uniform height/discriminant premise and this canonical-height instantiation; those assumptions are visible in the theorem's radius, separation, and faithful-label hypotheses.

## Proof map

| Result | Lean declaration | Exact hypotheses |
| --- | --- | --- |
| Disjoint-ball volume inequality | `XedniEuclideanPacking.card_mul_half_sep_pow_le_radius_pow` | Finite-dimensional real normed space; `R≥0`, `δ>0`; norm radius and pairwise separation |
| Explicit packing count | `XedniEuclideanPacking.card_le_radius_ratio_pow` | Same hypotheses; bound `(1+2R/δ)^d` |
| Fiber-labelled count | `XedniEuclideanPacking.labelled_card_le_radius_ratio_pow` | Faithful projection and finite labels, plus radius and separation on projected values |
| Bounded integer relation | `XedniEuclideanPacking.bounded_relation_of_euclidean_packing` | All coefficient-box sums satisfy the labelled projection conditions; strict packing count below `(2K+1)^r` |
| Canonical-height instantiation | Open | Real Mordell–Weil quotient, torsion labeling, selected-lift height and minimum-height bounds |

Lean `v4.35.0-rc4` and Mathlib `021c46bdd042f67b538b9f9871d556a93713a9a9` are pinned. `lake build EuclideanPacking` completed 2704 jobs. `#print axioms` for all four new theorems lists only `propext`, `Classical.choice`, and `Quot.sound`; the imported pigeonhole module has the same foundation record. `HeightPigeonhole.lean` is an exact source copy from the preceding checked experiment, pinned by hash. `lean4checker --fresh` was unavailable on this host.

## Exact control

`run.py` enumerates 42 coefficient-box instances, `K=0,…,20`, for the points `(1,0)`, `(0,1)`, and `(1,1)` in `ℤ²`, with torsion orders `1` and `2` (the third point carries the torsion coordinate). The maximum squared projected norm is `8K²` and the minimum nonzero squared norm is `1`, giving the exact bound `T(1+4√2 K)²`. The script compares this irrational bound by integer squaring, without floating-point rounding. Every exact count obeys it. The observed counts agree with `12K²+6K+1` for `T=1` and, for `K≥1`, `24K²+2` for `T=2`.

| Torsion order | First `K` certified by exact packing bound | Distinct sums | Coefficient-box size |
| ---: | ---: | ---: | ---: |
| 1 | 3 | 127 | 343 |
| 2 | 7 | 1178 | 3375 |

The integer upper bound `T(1+6K)²` also holds in all 42 controls. These controls test the finite lattice count and strict threshold; the elliptic-lift arithmetic hypotheses are the next proof step.
