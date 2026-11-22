# Proof map

The [Lean module](BilinearGate.lean) was built with the pinned [Lean 4.34.1 toolchain](lean_version.txt), commit `5045d0056413266e57c625dcd7c365b10e377c52`, using `lean BilinearGate.lean`. The [build output](lean_check.log) prints no axioms for all four declarations. The module imports only `Std`; `lean4checker` was unavailable.

| Obligation | Declaration or evidence | Exact scope and status |
| --- | --- | --- |
| A characteristic-two Artin–Schreier column `z²+z` has zero trace | `BilinearGate.artin_schreier_trace_zero` | Checked for any multiplication and addition with an explicitly assumed Boolean trace law `Tr(x+y)=Tr(x) xor Tr(y)` and square invariance `Tr(x²)=Tr(x)`. |
| Each bilinear S3 lift column `(tcd)²+tcd` lies in the trace-zero hyperplane | `BilinearGate.bilinear_column_trace_zero` | Checked under the same laws, universal in `t,c,d`. |
| A squared source-basis column has zero trace when its source coordinate does | `BilinearGate.square_column_trace_zero` | Checked. The N41 W6 basis has zero trace by independent finite-field calculation in the [result](RESULT.md). |
| A nonzero pivot row of a rank-one Boolean product matrix equals the right basis vector | `BilinearGate.pivot_row_is_right_vector` | Checked for all dimensions and indices, under `gamma(i,j)=alpha(i) and beta(j)` and `alpha(pivot)=true`. |
| The pivot-conditioned solver enumerates every rank-one solution exactly once | [native source](native.cpp), [direct comparator](cases.jsonl), [Python audit](audit_result.json), [checked-Sage positive](sage_result.json) | Checked exhaustively for each of 1,026 frozen six-by-six N41 family cases and independently replayed on 16 selected direct joins; the positive also passes group replay. A universal Lean proof of first-set-bit partition, field-linear solve completeness, and S3 curve-coordinate equivalence remains open. |
| The first-pivot N131 lift has at least 210 free binary variables when consistent | [transfer bound](transfer_bound.json) | Written dimension proof from at least 341 variables and at most 131 field equations. The needed coordinate-projection injectivity follows from the halftrace identity and trace guard at `c=0`; its N131 field instantiation and rank-nullity bridge are not yet formalized. |

The full mathematical statement would connect the exact N41 and N131 field representations, pair-output linear spaces, the inverse-coordinate S3 polynomial, and the rank-one solver's complete witness enumeration. The Lean declarations prove the structural trace and pivot steps; the field and algorithm bridges above remain explicitly open.
