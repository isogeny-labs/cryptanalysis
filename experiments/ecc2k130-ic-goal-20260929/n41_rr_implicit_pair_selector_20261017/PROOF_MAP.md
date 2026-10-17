# Proof map: code/sign and arithmetic pair sources

The pinned toolchain is `leanprover/lean4:v4.34.1` in `lean-toolchain`. From this directory run `lean SignANF.lean`. The checked output is `lean_check.stdout` with empty `lean_check.stderr`. `lean4checker --fresh` was unavailable on this host.

| Result | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| Two-sign ANF returns all four table bits | `SignANF.covers_four` | All six Boolean inputs; checked, no axioms |
| Simultaneously negating two endpoints negates their sum | `SignANF.simultaneous_sign_flip` | Arbitrary `Lean.Grind.AddCommGroup`; checked, `propext` only |
| First-nonzero coefficient chart and evaluation scaling | `FunctionSelector.first_nonzero`, `normalized_chart`, `dot_scale`, `scaled_zero` in the [preceding module](../n41_rr_function_selector_20261017/FunctionSelector.lean) | Arbitrary field, seven coefficients and finite rows; checked in predecessor |
| Arithmetic mask source reproduces every frozen N41 pair point | No Lean declaration | Complete 40-code by four-sign source in six rotations; producer [preflight](implicit_result.json) and independent [replay](implicit_audit_result.json) each check all 960 outputs. Curve, inverse, half-trace and Frobenius semantics remain to be formalized. |
| N131 W23 source law agrees with the archived checked-Sage samples | No Lean declaration | Eight specified seed edges and 32 signed outputs; [transfer receipt](n131_transfer_result.json) checks both pair x roots on each edge against the archived Sage result. The full 1,049,218-edge domain is outside this sample replay. |
| Seven vanishing RR rows characterize a six-point group relation when seven x coordinates are distinct | No Lean declaration | Curve/divisor and rational-function bridge; written proof in the [preceding result](../n41_rr_function_selector_20261017/RESULT.md). Full curve formalization remains open. |

The complete circuit equivalence theorem would define the binary curve and finite field, prove the half-trace endpoint construction and Frobenius/group laws, then connect the generated Boolean/XOR gates to the seven `L(7O)` evaluations. The current proof module establishes the two new structural implications without assuming a witness or the research claim as an axiom.
