# Finite height-ball packing bound

For a rank-`d` Mordell–Weil quotient with minimum nonzero canonical height `μ>0`, torsion order `T`, and points `P₁,…,Pᵣ` of height at most `M`, the distinct sums from the coefficient box `|aᵢ|≤K` obey the explicit finite bound

`N(K) ≤ T (1 + 2rK sqrt(M/μ))^d`.

Indeed, canonical height gives a Euclidean norm `||P||=sqrt(ĥ(P))` on the real tensor of the torsion-free quotient. Every projected sum lies in the ball of radius `R≤rK sqrt(M)`. Distinct projected lattice points have distance at least `δ=sqrt(μ)`. Open radius-`δ/2` balls about them are disjoint and lie inside the radius-`R+δ/2` ball. Comparing Euclidean volumes gives at most `(1+2R/δ)^d` projected points. Each has at most `T` torsion lifts. The case `d=0` has one projected value and the same bound gives `T`.

Consequently, if `μ≥aM` for `a>0` and

`T (1 + 2rK/sqrt(a))^d < (2K+1)^r`,

the coefficient-box pigeonhole argument gives a nonzero integer relation with each coefficient of magnitude at most `2K`. For fixed `r>d`, `T`, and `a`, some finite `K` satisfies this strict inequality. This removes an asymptotic lattice-point error term from the *conditional* finite counting step. Applying it to the selected xedni lifts still requires the discriminant-to-height and Lang-type lower bound uniformly for those lifts, and a faithful construction of their Mordell–Weil quotient and torsion labels.

## Checked formal core

`FiniteGridPacking.lean` checks three implications with Lean 4. The first counts separated values assigned to distinct cells of a `d`-dimensional integer grid with radius `M`. The second includes a finite label for projection fibers. The third composes that count with the existing coefficient-box pigeonhole theorem to obtain a bounded nonzero relation. The grid-cell diameter estimate and the construction from canonical height remain explicit geometric proof obligations; the Euclidean volume argument above is presently a written proof, not a Lean theorem.

| Result | Lean declaration | Remaining input |
| --- | --- | --- |
| Grid count `(2M+1)^d` | `XedniFiniteGridPacking.separated_grid_card_le` | Bounded grid index, cell diameter, separation |
| Torsion-labelled grid count | `XedniFiniteGridPacking.labelled_grid_card_le` | Faithful projection and labels, same geometric inputs |
| Bounded relation | `XedniFiniteGridPacking.bounded_relation_of_labelled_grid` | Strict count below `(2K+1)^r` |
| Euclidean ball count | Written proof above; Lean declaration open | Formal Euclidean volume packing or explicit quantizer |
| Selected elliptic lift application | Open | Uniform height and discriminant premises, quotient and torsion construction |

The formal project pins Lean `v4.35.0-rc4` and Mathlib `021c46bdd042f67b538b9f9871d556a93713a9a9`. `lake build FiniteGridPacking` completed successfully (1445 jobs); each new `#print axioms` lists only `propext`, `Classical.choice`, and `Quot.sound`. The imported `HeightPigeonhole.lean` and `MetricPacking.lean` are exact source copies from the preceding checked experiment. `lean4checker --fresh` was unavailable on this host.

## Exact control

`run.py` enumerates all 34 coefficient-box controls for `K=0,…,16`, with `r=3`, `d=2`, points `(1,0)`, `(0,1)`, `(1,1)` and torsion orders `1` and `2` (the third point carries the torsion coordinate). Here `δ=1` and `R≤(2+sqrt(2))K≤7K/2`, so the integer upper bound is `T(1+7K)^2`. All 34 exact counts obey it. The bound alone first certifies a collision at `K=5` for `T=1` and `K=12` for `T=2`. At those thresholds the exact distinct counts are respectively `331 < 1331` and `3458 < 15625`. These are exact lattice controls for the finite count, not selected elliptic lifts.

The next proof step is a checked Euclidean packing theorem or coordinate quantizer with an explicit cell bound, followed by the canonical-height quotient instantiation for the selected lift family.
