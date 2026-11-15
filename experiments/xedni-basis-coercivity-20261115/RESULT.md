# Height-to-coordinate coercivity and basis conditioning

The checked counterexample isolates a missing step in a coordinate-based xedni height argument. On the rank-two integer lattice, set `squareHeight(x,y) = |x|² + |y|²`. Every nonzero point has squared height at least one, and `(0,1)` has height one. For any `N`, the shear `shear N(a,b) = (a+Nb,b)` is an additive automorphism with inverse `unshear N(x,y) = (x-Ny,y)`. The unit-height point `(0,1)` has coordinates `(-N,1)` in that basis. The Lean theorem chooses `N=C+1` for any proposed coordinate bound `C`.

Thus a lower bound on the least positive height does not by itself bound coordinates in an arbitrary integral basis. This counterexample concerns the coordinate shortcut, not the original xedni analysis: Jacobson et al. use a regulator and geometry-of-numbers count to control values without fixing such a basis.

The positive Lean theorem `coordinate_bounded_of_height` states the exact extra input that makes the shortcut valid. For a selected basis and represented point, assume a common real `μ>0` satisfies `μ |a_i|² <= height` for each coordinate. If `height <= B < μ(K+1)²`, then every integer coordinate obeys `|a_i| <= K`. In an elliptic-curve application, `height` must be the canonical height and `μ` must be established uniformly for the relevant lift family and basis choices. This project does not assert that arithmetic estimate.

## Proof map

| Mathematical result | Lean declaration | Exact hypotheses |
| --- | --- | --- |
| Coercivity gives a coordinate box | `coordinate_bounded_of_height` | Real `μ>0`, `height<=B`, all `μ|a_i|²<=height`, `B<μ(K+1)²` |
| Shear and inverse are additive lattice maps | `unshear_shear`, `shear_unshear`, `shear_add`, `shearAddEquiv` | Any natural shear parameter `N` |
| Minimum positive squared height is one | `squareHeight_pos_of_ne_zero` and direct evaluation at `(0,1)` | Standard squared height on `ℤ×ℤ` |
| Unit-height coordinates exceed any fixed bound | `unbounded_coordinates_in_sheared_basis` | Any proposed natural bound `C`; choose `N=C+1` |

The formal project pins Lean `v4.35.0-rc4` and Mathlib `021c46bdd042f67b538b9f9871d556a93713a9a9`. `lake build BasisCoercivity` and `#print axioms` for all seven declarations are saved and checked by `verify.py`. The outputs contain only `propext`, `Classical.choice`, and `Quot.sound` as applicable. `lean4checker --fresh` was unavailable on this host. The next proof step is a quantitative reduced-basis or basis-free height-ball bound under the paper's explicit arithmetic hypotheses.
