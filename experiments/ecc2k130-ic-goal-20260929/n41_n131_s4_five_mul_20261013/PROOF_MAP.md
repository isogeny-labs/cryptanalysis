# Five-product S4 proof map

| Result | Lean declaration | Verification | Open bridge |
| --- | --- | --- | --- |
| Reuse `u=(ab)c` in both elementary symmetric functions: `e3=u+t(c(a+b)+ab)` and `e4=tu` | `FiveMulIdentity.optimized_eq_symmetric` | `lean FiveMulIdentity.lean` with pinned Lean 4.34.1; `#print axioms` reports only standard `propext`. The theorem equates XOR-normalized coefficient lists in four independent variables. | A Lean homomorphism from the custom characteristic-two polynomial normalizer to arbitrary field evaluation is not yet formalized. |
| Resultant and six-term S4 form | `FiveMulIdentity.resultant_eq_symmetric` | Same checked module and axiom audit. The prior [Bézout certificate](../n41_n131_s4_target_gate_20261013/S4Bezout.lean) proves the seven-variable coefficient identity. | The curve-point and inverse-x chart bridge, including exceptional points, remains open. |
| Exact field and group controls | None yet | Checked Sage verifies the optimized polynomial against the prior resultant in `GF(2)[a,b,c,t]` and checks all four signed-sum roots in GF(2^41) and GF(2^131). The N41 pinned complete XCNF model is checked independently. | Full Lean formalization of the binary elliptic curve and circuit semantics remains open. |

The proof source is [FiveMulIdentity.lean](FiveMulIdentity.lean). The [Lean version](lean_version.txt) and [build and axiom log](lean_check.log) are retained. The checked Sage runtime and result are [sage_runtime_info.json](sage_runtime_info.json) and [sage_result.json](sage_result.json). `lean4checker --fresh` was unavailable.
