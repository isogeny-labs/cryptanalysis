# Proof map for target-derived fiber membership

| Result | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| Composition of target-root enumeration and right-product membership preserves every listed source witness | `TargetFiber.query_iff_exists_source_witness` | Arbitrary type with zero; `rootExact` states that the enumerated right roots are exactly the upper-equation zeros for each listed left root; `fiberExact` states that the GCD oracle accepts exactly when one listed product pair zeros `H`. Checked in Lean 4.34.1; `#print axioms` reports no axioms. |
| Upper equation gives a degree-at-most-two polynomial in the right reciprocal coordinate | Open concrete algebra bridge | For `U(z,v,t)=(1+(zv)^2)t^2+zvt+(z+v)^2` in characteristic two, expand to `(1+(zt)^2)v^2+ztv+(t^2+z^2)`. The Sage job forms exactly these three coefficients and calls the field-root routine. The four-family run contained no identically zero upper polynomial; a general algorithm must handle that exceptional case. |
| Right-product GCD detects an allowed right block | Open polynomial-GCD bridge | `G_Q(q)=∏(q+q_j)` splits into 32 distinct roots over `GF(2^41)`. For each listed `p_i`, `deg gcd(G_Q,H(p_i,q,v))>0` iff a listed `q_j` zeros `H`. The existing `JointNorm.joint_zero_iff` is a checked finite-product zero lemma, but does not yet formalize Sage's polynomial GCD or the specialized `H`. |
| Root pair and product pair correspond to the actual diagonal-point sum and public target | Open curve-law bridge | The independent checked-Sage group audit enumerated 1,048,576 signed combinations across the four frozen cases, cofactored each right sum by four, and checked `4(L+R)=Q`. It agreed with all four algebraic decisions; a general Lean curve-law theorem is not yet available. |

Readable proof: fix a left root `z` and public raw-target reciprocal `t`.
Every nonexceptional right coordinate satisfying the upper addition relation
appears among the roots of the displayed quadratic. For a proposed root `v`,
the split polynomial `G_Q` has exactly the allowed second-product values as
roots. A positive-degree GCD with `H(p_i,q,v)` therefore supplies one allowed
`q_j`; conversely, such a `q_j` divides both polynomials. Looping over every
allowed first product `p_i` gives the existential source-product condition.
The Lean theorem proves the composition of those two exact subroutines. The
concrete group audit checks the chart and sign bridge on the frozen panel.

Build from this directory with `lean TargetFiber.lean`; the toolchain is
pinned in `lean-toolchain`, the compiler version in `lean_version.txt`, and
the output including `#print axioms` is in `lean_check.log`. Only bundled
Lean/Std dependencies were used. `lean4checker` was unavailable in this
environment.
