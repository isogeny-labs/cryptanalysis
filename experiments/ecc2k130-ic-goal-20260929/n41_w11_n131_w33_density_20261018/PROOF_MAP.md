# Shared-inverse root section: proof map

For a nonzero source product `p` in characteristic two, the pair output
`u` obeys `C u² + p u + H = 0`. With `v = p⁻¹`, write
`q = C H v²`. The normalized source root is
`h = halftrace(q)` when `Tr(q)=0`; the two output roots are
`u = (p/C) h` and `u = (p/C)(h+1)`. The existing circuit already carries
`p v = 1`, so the new circuit reuses that inverse witness.

For an odd-degree binary field, `Tr(1)=1`. Define the linear extension
`L(y) = halftrace(y + Tr(y))`. The shifted argument has trace zero,
so `L(y)²+L(y)=y+Tr(y)`. When `Tr(y)=0`, this is the required
Artin-Schreier root identity. Because trace and half-trace are additive,
`L` is additive; applying it to each basis coefficient in a Boolean-linear
expression yields the same value as applying it to the complete expression.
The first build failed because it applied half-trace to individual
trace-one coefficients. The corrected build uses `L` coefficientwise and
also enforces `Tr(q)=0` for the complete expression.

| Result | Lean declaration | Exact scope and verification |
| --- | --- | --- |
| S3 equation as a quadratic in its output | `SharedRootTrace.s3_output_quadratic` | Arbitrary field and three field elements; kernel checked. With `A=(ab)²+1`, `B=ab`, and `D=(a+b)²`, the fixed-output resolver applies the prior target normalization theorem. |
| Additivity of the extended section | `SharedRootTrace.shifted_halftrace_add` | Arbitrary field and additive `trace` and `halftrace` maps; kernel checked. |
| Shift has zero trace | `SharedRootTrace.shifted_trace_zero` | Arbitrary field of characteristic two; additive trace taking values 0 or 1, with `Tr(0)=0` and `Tr(1)=1`; kernel checked. |
| Extended Artin-Schreier section | `SharedRootTrace.shifted_halftrace_section` | Same trace assumptions, plus the half-trace root identity for every trace-zero input; kernel checked. |
| Section on trace-zero input | `SharedRootTrace.shifted_halftrace_trace_zero` | Arbitrary field and trace-zero input, assuming the half-trace root identity there; kernel checked. |
| Source equation normalization and branch completeness | `FunctionalRoots.source_normalization`, `FunctionalRoots.two_branch_completeness` | Prior checked module [FunctionalRoots.lean](../n41_n131_pairroot_functional_20261018/FunctionalRoots.lean); arbitrary characteristic-two field with the stated nonzero and witness equations. |
| S3 quadratic normalization | `FunctionalRoots.target_normalization` | Prior checked module; arbitrary characteristic-two field, `A != 0`, and the explicit normalization witness. The concrete N41 resolver asserts `A,B != 0` for each visited pair. |
| Concrete GF(2^41) trace/half-trace implementation and circuit bridge | Open Lean bridge | The exact finite-field representation, source product, source inverse, and XCNF gate semantics are verified by the checked Sage control and full assignment replay. They are not encoded as Lean theorems. |

The [Lean module](SharedRootTrace.lean) is pinned to Lean 4.34.1 by
`lean-toolchain`. Run `lean SharedRootTrace.lean`; `lean_check.log`
records the successful build and `#print axioms` output. Every theorem
uses only `propext`, `Classical.choice`, and `Quot.sound`; there are no
custom axioms or proof placeholders. `lean4checker --fresh` was unavailable
on this host.
