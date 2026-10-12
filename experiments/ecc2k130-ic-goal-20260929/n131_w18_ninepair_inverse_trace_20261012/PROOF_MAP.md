# Proof map: inverse-trace source replacement

The new implementation result substitutes a previously validated source gate
inside the balanced nine-pair target circuit. The nine pair slots, target
choice, point-sum equations, and distinct-column shield have the same source
law as the balanced BDD circuit.

| Result | Lean declaration | Exact assumptions | Status |
| --- | --- | --- | --- |
| Replacing a pointwise equivalent gate preserves existence of a nine-slot point-sum witness with the same distinct-column predicate and target | `GateReplacement.exact_gate_substitution` | `∀ code, bdd code ↔ inverseTrace code`; arbitrary nine-slot distinct-column predicate and point-sum function | Checked in Lean; `#print axioms` reports no axioms |
| Inverse witnesses and zero-trace tests select exactly the 33,191 frozen W18 canonical codes | Concrete field/source bridge to the preceding theorem | GF(2)[t]/(t^131+t^13+t²+t+1), seed 212, W18 masks and the frozen folded-column table | The prior `n131_w16_w18_sixpair_width_gate_20261010/native_audit_result.json` independently checks rationality against every nonzero W15–W18 mask (491,516 cases); the `n131_w18_inverse_trace_terminal_20261011/gate_equivalence.json` exhaustively compares all 17-bit codes with the BDD set; checked Sage confirms all 18 endpoints in this constructed relation in `control_gate_sage.json`; **Lean formalization partial** |
| The point-sum witness on a selected Frobenius conjugate pulls back to the public subgroup point | `NinePairOrbit.relation_pullback` in the prior orbit experiment | Additive inverse Frobenius, source closure, and `[4]U=Q` | Conditional theorem checked in the prior pinned Lean module; concrete-curve bridge remains open |

Run `lean GateReplacement.lean` in this directory with the pinned
`lean-toolchain`. The recorded `lean_runtime.txt` pins the Lean executable
commit and `Std` supplied by that toolchain; `lean_check.txt` contains the
build output and axiom audit.
`lean4checker --fresh` was unavailable on this host. The concrete gate bridge
would require formal definitions of the 131-bit binary field, Koblitz
coordinate rationality, the W18 code map, and its folded-column table, then
a kernel-checked finite census or a symbolic proof of their equivalence.
