# Proof map

The [Lean module](ConditionalRouter.lean) is pinned to
`leanprover/lean4:v4.34.1`. `lean ConditionalRouter.lean` built, and
the [axiom log](lean_check.log) reports only `propext` and
`Quot.sound` for `ConditionalRouter.conditional_replacement`. The
theorem contains no `sorry`, `admit`, or custom research axiom.
`lean4checker --fresh` was unavailable.

| Statement | Formal or computational evidence | Hypotheses and status |
| --- | --- | --- |
| Replacing a gate by a formula agreeing on the current survivor domain preserves the accepted set there | `ConditionalRouter.conditional_replacement` | Arbitrary input type, explicit domain and agreement after earlier gates; kernel checked |
| The selected coordinate-product labels reject only families whose outputs all miss that target-selected product | Frozen source label definition in `analyze.py`, independently reconstructed by `audit.py` | Exact N41 source family outputs and selected target features; computational bridge |
| Every staged coefficient formula agrees with its corresponding label on every survivor | `analyze.py` assertions; independent `audit.py` replay | All 38 stage domains and both pivot variants; verified finite computation |
| Stage rank and minimum full-rank degree | High-pivot producer and low-pivot audit at stages 0, 1, 5, 16, 28, and 37 | Exact 16-bit source masks, monomial order, and 766 trace-compatible families; concrete rank certificates are not embedded in Lean |
| Final survivor is the witness two-code family for the fixed-suffix ordinary residual | Index 966; predecessor `trace_audit_result.json` and archived group replay | Frozen N41 public target/source law with five suffix states fixed; independently replayed earlier |

The Lean theorem proves the key conditional-synthesis step under
the actual agreement requirement. The source-label construction,
finite binary ranks, and curve/group witness remain computational
bridges. A complete Lean theorem for the concrete N41 curve and
all 37 coefficient vectors remains open.
